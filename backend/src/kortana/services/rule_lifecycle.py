"""V11D — Rule Lifecycle Management.

Manages policy rules through a promotion pipeline:
  DRAFT → REVIEW → ACTIVE → RETIRED

Rules are versioned, reviewable, and promotion-gated like code.
Each stage transition is recorded as a RulePromotion with the
operator who triggered it.  Active rules are pushed into the
V10D PolicyEngine; retired rules are removed.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger("kortana.rule_lifecycle")


# ---------------------------------------------------------------------------
# Rule stages
# ---------------------------------------------------------------------------


class RuleStage(str, Enum):
    """Lifecycle stage of a policy rule."""

    DRAFT = "draft"
    REVIEW = "review"
    ACTIVE = "active"
    RETIRED = "retired"
    REJECTED = "rejected"


# Valid stage transitions
_VALID_TRANSITIONS: dict[RuleStage, list[RuleStage]] = {
    RuleStage.DRAFT: [RuleStage.REVIEW],
    RuleStage.REVIEW: [RuleStage.ACTIVE, RuleStage.REJECTED],
    RuleStage.ACTIVE: [RuleStage.RETIRED],
    RuleStage.RETIRED: [],
    RuleStage.REJECTED: [RuleStage.DRAFT],
}


# ---------------------------------------------------------------------------
# Rule version
# ---------------------------------------------------------------------------


@dataclass
class RuleVersion:
    """A versioned snapshot of a policy rule at a specific stage."""

    version_id: str
    rule_id: str
    stage: RuleStage
    name: str
    description: str
    conditions: dict[str, Any]
    action: str
    priority: int
    author_id: str
    reviewer_id: str | None = None
    changelog: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    promoted_at: datetime | None = None
    version_hash: str = ""

    def __post_init__(self) -> None:
        if not self.version_hash:
            self.version_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "version_id": self.version_id,
                "rule_id": self.rule_id,
                "name": self.name,
                "conditions": self.conditions,
                "action": self.action,
                "priority": self.priority,
                "author_id": self.author_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def rule_snapshot(self) -> dict[str, Any]:
        """Return the rule content as a serializable dict."""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "action": self.action,
            "priority": self.priority,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_id": self.version_id,
            "rule_id": self.rule_id,
            "stage": self.stage.value,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "action": self.action,
            "priority": self.priority,
            "author_id": self.author_id,
            "reviewer_id": self.reviewer_id,
            "changelog": self.changelog,
            "created_at": self.created_at.isoformat(),
            "promoted_at": self.promoted_at.isoformat() if self.promoted_at else None,
            "version_hash": self.version_hash,
        }


# ---------------------------------------------------------------------------
# Rule promotion record
# ---------------------------------------------------------------------------


@dataclass
class RulePromotion:
    """Records a stage transition for a rule version."""

    promotion_id: str
    version_id: str
    rule_id: str
    from_stage: RuleStage
    to_stage: RuleStage
    promoted_by: str
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    promotion_hash: str = ""

    def __post_init__(self) -> None:
        if not self.promotion_hash:
            payload = json.dumps(
                {
                    "promotion_id": self.promotion_id,
                    "version_id": self.version_id,
                    "rule_id": self.rule_id,
                    "from_stage": self.from_stage.value,
                    "to_stage": self.to_stage.value,
                    "promoted_by": self.promoted_by,
                    "timestamp": self.timestamp.isoformat(),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            self.promotion_hash = hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "promotion_id": self.promotion_id,
            "version_id": self.version_id,
            "rule_id": self.rule_id,
            "from_stage": self.from_stage.value,
            "to_stage": self.to_stage.value,
            "promoted_by": self.promoted_by,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "promotion_hash": self.promotion_hash,
        }


# ---------------------------------------------------------------------------
# Rule lifecycle manager
# ---------------------------------------------------------------------------


class RuleLifecycleManager:
    """Manages the promotion lifecycle of policy rules.

    Rules progress through DRAFT → REVIEW → ACTIVE → RETIRED,
    with reviewer separation and audit trail.
    """

    def __init__(self) -> None:
        self._versions: dict[str, RuleVersion] = {}      # version_id → version
        self._rule_versions: dict[str, list[str]] = {}    # rule_id → [version_ids]
        self._promotions: dict[str, list[RulePromotion]] = {}  # rule_id → [promotions]

    def create_draft(
        self,
        rule_id: str,
        name: str,
        description: str,
        conditions: dict[str, Any],
        action: str,
        priority: int,
        author_id: str,
        changelog: str = "",
    ) -> RuleVersion:
        """Create a new draft rule version."""
        version_id = f"rv_{secrets.token_hex(8)}"
        version = RuleVersion(
            version_id=version_id,
            rule_id=rule_id,
            stage=RuleStage.DRAFT,
            name=name,
            description=description,
            conditions=conditions,
            action=action,
            priority=priority,
            author_id=author_id,
            changelog=changelog,
        )
        self._versions[version_id] = version
        if rule_id not in self._rule_versions:
            self._rule_versions[rule_id] = []
        self._rule_versions[rule_id].append(version_id)

        logger.info("Draft created: %s for rule %s by %s", version_id, rule_id, author_id)
        return version

    def submit_for_review(
        self,
        version_id: str,
        submitter_id: str,
    ) -> tuple[RuleVersion | None, str | None]:
        """Submit a draft for review. Submitter must be the author."""
        version = self._versions.get(version_id)
        if version is None:
            return None, f"Version {version_id!r} not found"

        if version.stage != RuleStage.DRAFT:
            return None, f"Cannot submit: version is in {version.stage.value}, expected draft"

        if version.author_id != submitter_id:
            return None, f"Only the author ({version.author_id}) can submit for review"

        version.stage = RuleStage.REVIEW
        version.promoted_at = datetime.utcnow()
        self._record_promotion(version, RuleStage.DRAFT, RuleStage.REVIEW, submitter_id, "Submitted for review")
        logger.info("Submitted for review: %s by %s", version_id, submitter_id)
        return version, None

    def approve(
        self,
        version_id: str,
        reviewer_id: str,
    ) -> tuple[RuleVersion | None, str | None]:
        """Approve a rule under review. Reviewer must NOT be the author."""
        version = self._versions.get(version_id)
        if version is None:
            return None, f"Version {version_id!r} not found"

        if version.stage != RuleStage.REVIEW:
            return None, f"Cannot approve: version is in {version.stage.value}, expected review"

        if version.author_id == reviewer_id:
            return None, "Reviewer cannot be the same as the author"

        version.stage = RuleStage.ACTIVE
        version.reviewer_id = reviewer_id
        version.promoted_at = datetime.utcnow()
        self._record_promotion(version, RuleStage.REVIEW, RuleStage.ACTIVE, reviewer_id, "Approved")

        # Push to PolicyEngine
        self._push_to_engine(version)

        logger.info("Approved and activated: %s by reviewer %s", version_id, reviewer_id)
        return version, None

    def reject(
        self,
        version_id: str,
        reviewer_id: str,
        reason: str = "",
    ) -> tuple[RuleVersion | None, str | None]:
        """Reject a rule under review."""
        version = self._versions.get(version_id)
        if version is None:
            return None, f"Version {version_id!r} not found"

        if version.stage != RuleStage.REVIEW:
            return None, f"Cannot reject: version is in {version.stage.value}, expected review"

        version.stage = RuleStage.REJECTED
        version.reviewer_id = reviewer_id
        version.promoted_at = datetime.utcnow()
        self._record_promotion(version, RuleStage.REVIEW, RuleStage.REJECTED, reviewer_id, reason or "Rejected")

        logger.info("Rejected: %s by %s — %s", version_id, reviewer_id, reason)
        return version, None

    def activate(
        self,
        version_id: str,
        operator_id: str,
    ) -> tuple[RuleVersion | None, str | None]:
        """Directly activate a reviewed rule.

        Normally approve() handles this, but this allows re-activation
        of a previously active rule version.
        """
        version = self._versions.get(version_id)
        if version is None:
            return None, f"Version {version_id!r} not found"

        if version.stage not in (RuleStage.REVIEW, RuleStage.RETIRED):
            return None, f"Cannot activate from {version.stage.value}"

        old_stage = version.stage
        version.stage = RuleStage.ACTIVE
        version.promoted_at = datetime.utcnow()
        self._record_promotion(version, old_stage, RuleStage.ACTIVE, operator_id, "Activated")
        self._push_to_engine(version)

        logger.info("Activated: %s by %s", version_id, operator_id)
        return version, None

    def retire(
        self,
        version_id: str,
        operator_id: str,
        reason: str = "",
    ) -> tuple[RuleVersion | None, str | None]:
        """Retire an active rule, removing it from the policy engine."""
        version = self._versions.get(version_id)
        if version is None:
            return None, f"Version {version_id!r} not found"

        if version.stage != RuleStage.ACTIVE:
            return None, f"Cannot retire: version is in {version.stage.value}, expected active"

        version.stage = RuleStage.RETIRED
        version.promoted_at = datetime.utcnow()
        self._record_promotion(version, RuleStage.ACTIVE, RuleStage.RETIRED, operator_id, reason or "Retired")

        # Remove from PolicyEngine
        self._remove_from_engine(version)

        logger.info("Retired: %s by %s", version_id, operator_id)
        return version, None

    def get_version(self, version_id: str) -> RuleVersion | None:
        return self._versions.get(version_id)

    def get_versions(self, rule_id: str) -> list[RuleVersion]:
        ids = self._rule_versions.get(rule_id, [])
        return [self._versions[vid] for vid in ids if vid in self._versions]

    def get_promotions(self, rule_id: str) -> list[RulePromotion]:
        return list(self._promotions.get(rule_id, []))

    def diff_versions(
        self,
        version_id_a: str,
        version_id_b: str,
    ) -> dict[str, Any] | None:
        """Compare two rule versions and return differences."""
        a = self._versions.get(version_id_a)
        b = self._versions.get(version_id_b)
        if a is None or b is None:
            return None

        sa = a.rule_snapshot
        sb = b.rule_snapshot
        changes: dict[str, Any] = {}

        all_keys = set(sa.keys()) | set(sb.keys())
        for key in all_keys:
            va = sa.get(key)
            vb = sb.get(key)
            if va != vb:
                changes[key] = {"old": va, "new": vb}

        return {
            "version_a": version_id_a,
            "version_b": version_id_b,
            "rule_id_a": a.rule_id,
            "rule_id_b": b.rule_id,
            "changes": changes,
            "identical": len(changes) == 0,
        }

    @property
    def version_count(self) -> int:
        return len(self._versions)

    @property
    def active_rules(self) -> list[RuleVersion]:
        return [v for v in self._versions.values() if v.stage == RuleStage.ACTIVE]

    @property
    def draft_rules(self) -> list[RuleVersion]:
        return [v for v in self._versions.values() if v.stage == RuleStage.DRAFT]

    @property
    def review_rules(self) -> list[RuleVersion]:
        return [v for v in self._versions.values() if v.stage == RuleStage.REVIEW]

    # --- Internal helpers ---

    def _record_promotion(
        self,
        version: RuleVersion,
        from_stage: RuleStage,
        to_stage: RuleStage,
        promoted_by: str,
        reason: str,
    ) -> None:
        promotion = RulePromotion(
            promotion_id=f"promo_{secrets.token_hex(8)}",
            version_id=version.version_id,
            rule_id=version.rule_id,
            from_stage=from_stage,
            to_stage=to_stage,
            promoted_by=promoted_by,
            reason=reason,
        )
        if version.rule_id not in self._promotions:
            self._promotions[version.rule_id] = []
        self._promotions[version.rule_id].append(promotion)

    def _push_to_engine(self, version: RuleVersion) -> None:
        """Push a rule version into the V10D policy engine."""
        from src.kortana.services.policy_engine import (
            PolicyRule,
            RuleAction,
            RulePriority,
            get_policy_engine,
        )

        engine = get_policy_engine()

        try:
            rule_action = RuleAction(version.action)
        except ValueError:
            rule_action = RuleAction.HOLD

        # Map priority
        for p in RulePriority:
            if version.priority <= p.value:
                rule_priority = p
                break
        else:
            rule_priority = RulePriority.DEFAULT

        rule = PolicyRule(
            rule_id=version.rule_id,
            name=version.name,
            description=version.description,
            conditions=version.conditions,
            action=rule_action,
            priority=rule_priority,
            enabled=True,
        )

        # Remove old version first, then add new
        engine.remove_rule(version.rule_id)
        engine.add_rule(rule)
        logger.info("Rule pushed to engine: %s", version.rule_id)

    def _remove_from_engine(self, version: RuleVersion) -> None:
        """Remove a rule from the V10D policy engine."""
        from src.kortana.services.policy_engine import get_policy_engine

        engine = get_policy_engine()
        engine.remove_rule(version.rule_id)
        logger.info("Rule removed from engine: %s", version.rule_id)


# Module-level singleton
_manager = RuleLifecycleManager()


def get_rule_lifecycle_manager() -> RuleLifecycleManager:
    """Return the module-level rule lifecycle manager."""
    return _manager
