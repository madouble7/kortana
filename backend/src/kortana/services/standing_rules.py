"""V24A — standing rules: who may take constitutional procedural actions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ActorRole(Enum):
    """Roles that determine procedural standing."""

    CONSTITUTIONAL_AUTHORITY = "constitutional_authority"
    SENIOR_OPERATOR = "senior_operator"
    OPERATOR = "operator"
    OBSERVER = "observer"
    SYSTEM = "system"


class ActionType(Enum):
    """Types of constitutional actions that require standing."""

    FILE_APPEAL = "file_appeal"
    REQUEST_WAIVER = "request_waiver"
    DECLARE_EMERGENCY = "declare_emergency"
    CAST_VOTE = "cast_vote"
    REVIEW_DECISION = "review_decision"
    GRANT_WAIVER = "grant_waiver"
    DECIDE_APPEAL = "decide_appeal"
    SUBMIT_EMERGENCY_REVIEW = "submit_emergency_review"
    RECORD_PRECEDENT = "record_precedent"


@dataclass
class StandingRule:
    """A rule defining what role may take what action."""

    rule_id: str
    role: ActorRole
    allowed_actions: list[ActionType]
    restricted_areas: list[str] | None = None
    description: str = ""
    rule_hash: str = ""

    def __post_init__(self) -> None:
        if not self.rule_hash:
            blob = f"{self.rule_id}:{self.role.value}:{[a.value for a in self.allowed_actions]}"
            self.rule_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def allows(self, action: ActionType, policy_area: str | None = None) -> bool:
        """Check if this rule allows the given action, optionally in a specific area."""
        if action not in self.allowed_actions:
            return False
        if self.restricted_areas is not None and policy_area is not None:
            return policy_area in self.restricted_areas
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "role": self.role.value,
            "allowed_actions": [a.value for a in self.allowed_actions],
            "restricted_areas": self.restricted_areas,
            "description": self.description,
            "rule_hash": self.rule_hash,
        }


@dataclass
class StandingResult:
    """Result of a standing check."""

    allowed: bool
    actor: str
    role: ActorRole
    action: ActionType
    reason: str
    checked_at: str = ""

    def __post_init__(self) -> None:
        if not self.checked_at:
            self.checked_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "actor": self.actor,
            "role": self.role.value,
            "action": self.action.value,
            "reason": self.reason,
            "checked_at": self.checked_at,
        }


def _default_rules() -> list[StandingRule]:
    """Default standing rules — who may do what."""
    return [
        StandingRule(
            rule_id="sr-001",
            role=ActorRole.CONSTITUTIONAL_AUTHORITY,
            allowed_actions=list(ActionType),
            description="Full constitutional authority — may take any procedural action",
        ),
        StandingRule(
            rule_id="sr-002",
            role=ActorRole.SENIOR_OPERATOR,
            allowed_actions=[
                ActionType.FILE_APPEAL,
                ActionType.REQUEST_WAIVER,
                ActionType.CAST_VOTE,
                ActionType.REVIEW_DECISION,
                ActionType.SUBMIT_EMERGENCY_REVIEW,
            ],
            description="Senior operator — may appeal, request waivers, vote, and review",
        ),
        StandingRule(
            rule_id="sr-003",
            role=ActorRole.OPERATOR,
            allowed_actions=[
                ActionType.FILE_APPEAL,
                ActionType.CAST_VOTE,
            ],
            description="Operator — may file appeals and cast votes",
        ),
        StandingRule(
            rule_id="sr-004",
            role=ActorRole.OBSERVER,
            allowed_actions=[],
            description="Observer — read-only, no procedural standing",
        ),
        StandingRule(
            rule_id="sr-005",
            role=ActorRole.SYSTEM,
            allowed_actions=[
                ActionType.DECLARE_EMERGENCY,
                ActionType.RECORD_PRECEDENT,
            ],
            description="System — may declare emergencies and record precedents",
        ),
    ]


class StandingRules:
    """Manages procedural standing — who may take which constitutional actions."""

    def __init__(self, load_defaults: bool = True) -> None:
        self._rules: list[StandingRule] = []
        self._actor_roles: dict[str, ActorRole] = {}
        self._checks: list[StandingResult] = []
        if load_defaults:
            self._rules = _default_rules()

    def register_actor(self, actor: str, role: ActorRole) -> None:
        """Register an actor with a specific role."""
        self._actor_roles[actor] = role

    def get_actor_role(self, actor: str) -> ActorRole:
        """Get an actor's role, defaulting to OBSERVER."""
        return self._actor_roles.get(actor, ActorRole.OBSERVER)

    def add_rule(self, rule: StandingRule) -> None:
        """Add or replace a standing rule for a role."""
        self._rules = [r for r in self._rules if r.role != rule.role]
        self._rules.append(rule)

    def get_rule(self, role: ActorRole) -> StandingRule | None:
        """Get the standing rule for a role."""
        for r in self._rules:
            if r.role == role:
                return r
        return None

    def check_standing(
        self,
        actor: str,
        action: ActionType,
        policy_area: str | None = None,
    ) -> StandingResult:
        """Check if an actor has standing to take a procedural action."""
        role = self.get_actor_role(actor)
        rule = self.get_rule(role)

        if rule is None:
            result = StandingResult(
                allowed=False,
                actor=actor,
                role=role,
                action=action,
                reason=f"No standing rule defined for role {role.value}",
            )
            self._checks.append(result)
            return result

        if rule.allows(action, policy_area):
            result = StandingResult(
                allowed=True,
                actor=actor,
                role=role,
                action=action,
                reason=f"Standing granted via rule {rule.rule_id} ({rule.description})",
            )
        else:
            result = StandingResult(
                allowed=False,
                actor=actor,
                role=role,
                action=action,
                reason=f"Role {role.value} does not have standing for {action.value}",
            )
        self._checks.append(result)
        return result

    def get_checks(self, actor: str | None = None) -> list[StandingResult]:
        result = list(self._checks)
        if actor is not None:
            result = [c for c in result if c.actor == actor]
        return result

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    @property
    def actor_count(self) -> int:
        return len(self._actor_roles)

    @property
    def check_count(self) -> int:
        return len(self._checks)

    def get_summary(self) -> dict[str, Any]:
        by_role: dict[str, int] = {}
        for a, r in self._actor_roles.items():
            by_role[r.value] = by_role.get(r.value, 0) + 1
        total_checks = len(self._checks)
        allowed = sum(1 for c in self._checks if c.allowed)
        return {
            "total_rules": len(self._rules),
            "registered_actors": len(self._actor_roles),
            "actors_by_role": by_role,
            "total_checks": total_checks,
            "allowed_checks": allowed,
            "denied_checks": total_checks - allowed,
        }


_standing: StandingRules | None = None


def get_standing_rules() -> StandingRules:
    """Module singleton."""
    global _standing
    if _standing is None:
        _standing = StandingRules()
    return _standing
