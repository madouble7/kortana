"""V10D — Policy Engine: policy-as-data with explicit rule evaluation.

Replaces logic spread across services with a declarative rule engine.
Rules are defined as data (PolicyRule), evaluated in priority order,
and produce a deterministic ActionDecision with full trace.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger("kortana.policy_engine")


# ---------------------------------------------------------------------------
# Rule primitives
# ---------------------------------------------------------------------------


class RuleAction(str, Enum):
    """Actions a policy rule can prescribe."""

    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"
    DE_ESCALATE = "de-escalate"
    HOLD = "hold"
    ROLLBACK = "rollback"
    ALERT = "alert"


class RulePriority(int, Enum):
    """Priority levels — lower number = higher priority."""

    CRITICAL = 0
    HIGH = 10
    MEDIUM = 20
    LOW = 30
    DEFAULT = 100


@dataclass
class PolicyRule:
    """A single declarative policy rule.

    Rules are evaluated against a fact set.  If all conditions in
    `conditions` match the facts, the rule fires and produces
    its prescribed `action`.
    """

    rule_id: str
    name: str
    description: str
    conditions: dict[str, Any]        # key=fact_name, value=expected
    action: RuleAction
    priority: RulePriority = RulePriority.DEFAULT
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def evaluate(self, facts: dict[str, Any]) -> bool:
        """Check if all conditions match the given facts."""
        if not self.enabled:
            return False

        for key, expected in self.conditions.items():
            actual = facts.get(key)

            # Support operators in conditions
            if isinstance(expected, dict):
                op = expected.get("op")
                val = expected.get("value")
                if op == "eq" and actual != val:
                    return False
                if op == "ne" and actual == val:
                    return False
                if op == "gt" and (actual is None or actual <= val):
                    return False
                if op == "lt" and (actual is None or actual >= val):
                    return False
                if op == "gte" and (actual is None or actual < val):
                    return False
                if op == "lte" and (actual is None or actual > val):
                    return False
                if op == "in" and actual not in val:
                    return False
                if op == "not_in" and actual in val:
                    return False
                if op == "is_true" and not actual:
                    return False
                if op == "is_false" and actual:
                    return False
            else:
                # Simple equality
                if actual != expected:
                    return False

        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "action": self.action.value,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Evaluation result
# ---------------------------------------------------------------------------


@dataclass
class RuleEvaluation:
    """Result of evaluating a single rule against facts."""

    rule_id: str
    rule_name: str
    matched: bool
    action: str | None
    priority: int
    conditions_checked: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "matched": self.matched,
            "action": self.action,
            "priority": self.priority,
            "conditions_checked": self.conditions_checked,
        }


@dataclass
class PolicyDecision:
    """Aggregate result of evaluating all rules against facts."""

    action: str
    reason: str
    matched_rules: list[RuleEvaluation] = field(default_factory=list)
    all_evaluations: list[RuleEvaluation] = field(default_factory=list)
    facts_snapshot: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    decision_hash: str = ""

    def __post_init__(self) -> None:
        if not self.decision_hash:
            self.decision_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "action": self.action,
                "matched_rules": [r.to_dict() for r in self.matched_rules],
                "facts": self.facts_snapshot,
                "timestamp": self.timestamp,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "reason": self.reason,
            "matched_rules": [r.to_dict() for r in self.matched_rules],
            "all_evaluations": [r.to_dict() for r in self.all_evaluations],
            "facts_snapshot": self.facts_snapshot,
            "timestamp": self.timestamp,
            "decision_hash": self.decision_hash,
        }


# ---------------------------------------------------------------------------
# Policy engine
# ---------------------------------------------------------------------------


class PolicyEngine:
    """Evaluates declarative policy rules against a fact set.

    Rules are sorted by priority (ascending = highest priority first).
    The first matching rule determines the decision, but all rules
    are evaluated for the full trace.
    """

    def __init__(self) -> None:
        self._rules: dict[str, PolicyRule] = {}

    def add_rule(self, rule: PolicyRule) -> None:
        """Register a policy rule."""
        self._rules[rule.rule_id] = rule
        logger.info("Policy rule added: %s (%s)", rule.rule_id, rule.name)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule. Returns True if found."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get_rule(self, rule_id: str) -> PolicyRule | None:
        return self._rules.get(rule_id)

    def evaluate(self, facts: dict[str, Any]) -> PolicyDecision:
        """Evaluate all rules against facts and return a decision.

        The highest-priority matching rule determines the action.
        All rules are evaluated for the trace (all_evaluations).
        """
        sorted_rules = sorted(
            self._rules.values(),
            key=lambda r: (r.priority.value, r.rule_id),
        )

        all_evals: list[RuleEvaluation] = []
        matched: list[RuleEvaluation] = []
        winning_action: str | None = None
        winning_reason: str = "No matching rules — holding"

        for rule in sorted_rules:
            hit = rule.evaluate(facts)
            evaluation = RuleEvaluation(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                matched=hit,
                action=rule.action.value if hit else None,
                priority=rule.priority.value,
                conditions_checked=len(rule.conditions),
            )
            all_evals.append(evaluation)

            if hit:
                matched.append(evaluation)
                if winning_action is None:
                    winning_action = rule.action.value
                    winning_reason = (
                        f"Rule {rule.rule_id!r} ({rule.name}): "
                        f"{rule.description}"
                    )

        decision = PolicyDecision(
            action=winning_action or "hold",
            reason=winning_reason,
            matched_rules=matched,
            all_evaluations=all_evals,
            facts_snapshot=facts,
        )

        logger.info(
            "Policy engine: action=%s, %d/%d rules matched, hash=%s",
            decision.action,
            len(matched),
            len(all_evals),
            decision.decision_hash[:12],
        )

        return decision

    @property
    def rules(self) -> list[dict[str, Any]]:
        """Return all rules as dicts, sorted by priority."""
        return [
            r.to_dict()
            for r in sorted(
                self._rules.values(),
                key=lambda r: (r.priority.value, r.rule_id),
            )
        ]

    @property
    def count(self) -> int:
        return len(self._rules)


# ---------------------------------------------------------------------------
# Default governance rules
# ---------------------------------------------------------------------------


def create_default_engine() -> PolicyEngine:
    """Create a policy engine loaded with the default governance rules."""
    engine = PolicyEngine()

    engine.add_rule(PolicyRule(
        rule_id="gov-001",
        name="Override blocks deploy",
        description="Active human override prevents automated deployment changes",
        conditions={"override_active": True, "deploy_requested": True},
        action=RuleAction.DENY,
        priority=RulePriority.CRITICAL,
    ))

    engine.add_rule(PolicyRule(
        rule_id="gov-002",
        name="Cooldown blocks deploy",
        description="Rollback cooldown prevents new deployments",
        conditions={"in_cooldown": True, "deploy_requested": True},
        action=RuleAction.DENY,
        priority=RulePriority.CRITICAL,
    ))

    engine.add_rule(PolicyRule(
        rule_id="gov-003",
        name="Drill SLO violation blocks escalation",
        description="Failing drill SLOs prevent autonomy escalation",
        conditions={
            "drill_slos_met": False,
            "action_type": "escalate",
        },
        action=RuleAction.DENY,
        priority=RulePriority.HIGH,
    ))

    engine.add_rule(PolicyRule(
        rule_id="gov-004",
        name="Rate limit blocks actuation",
        description="Too many recent changes prevents new actuation",
        conditions={"rate_limited": True},
        action=RuleAction.HOLD,
        priority=RulePriority.HIGH,
    ))

    engine.add_rule(PolicyRule(
        rule_id="gov-005",
        name="Quorum pending warns",
        description="Pending quorum override suggests caution",
        conditions={"quorum_pending": {"op": "gt", "value": 0}},
        action=RuleAction.ALERT,
        priority=RulePriority.MEDIUM,
    ))

    engine.add_rule(PolicyRule(
        rule_id="gov-006",
        name="Default allow",
        description="If no blocking rules fire, allow the action",
        conditions={},
        action=RuleAction.ALLOW,
        priority=RulePriority.DEFAULT,
    ))

    return engine


# Module-level singleton
_engine = create_default_engine()


def get_policy_engine() -> PolicyEngine:
    """Return the module-level policy engine singleton."""
    return _engine
