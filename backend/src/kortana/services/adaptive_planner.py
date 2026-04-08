"""V19C — Adaptive Planner: learning-enhanced reconciliation planning."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.kortana.services.drift_detector import DriftSignal
from src.kortana.services.reconciliation_planner import (
    ReconciliationPlanner,
    ReconciliationAction,
    ReconciliationActionType,
    PlanPriority,
    PlanStatus,
)
from src.kortana.services.strategy_learner import StrategyLearner


# ── Data structures ───────────────────────────────────────────────────────


@dataclass
class AdaptiveOverride:
    """A specific override applied from learning data."""

    field_name: str = ""
    original_value: str = ""
    learned_value: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "original_value": self.original_value,
            "learned_value": self.learned_value,
            "confidence": round(self.confidence, 3),
        }


@dataclass
class AdaptivePlan:
    """A reconciliation plan enhanced with learning data."""

    plan_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    base_plan_id: str = ""
    status: PlanStatus = PlanStatus.CREATED
    priority: PlanPriority = PlanPriority.NORMAL
    drift_signal_ids: list[str] = field(default_factory=list)
    actions: list[ReconciliationAction] = field(default_factory=list)
    description: str = ""
    learning_applied: bool = False
    confidence_score: float = 0.0
    overrides_applied: list[AdaptiveOverride] = field(default_factory=list)
    recommendation_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    plan_hash: str = ""

    def __post_init__(self) -> None:
        if not self.plan_hash:
            raw = f"{self.plan_id}:{self.learning_applied}:{self.confidence_score}:{self.created_at}"
            self.plan_hash = hashlib.sha256(raw.encode()).hexdigest()

    @property
    def action_count(self) -> int:
        return len(self.actions)

    @property
    def override_count(self) -> int:
        return len(self.overrides_applied)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "base_plan_id": self.base_plan_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "drift_signal_ids": self.drift_signal_ids,
            "actions": [a.to_dict() for a in self.actions],
            "description": self.description,
            "learning_applied": self.learning_applied,
            "confidence_score": round(self.confidence_score, 3),
            "overrides_applied": [o.to_dict() for o in self.overrides_applied],
            "recommendation_id": self.recommendation_id,
            "action_count": self.action_count,
            "override_count": self.override_count,
            "created_at": self.created_at,
            "plan_hash": self.plan_hash,
        }


# ── Priority mapping ─────────────────────────────────────────────────────

_PRIORITY_MAP: dict[str, PlanPriority] = {
    "immediate": PlanPriority.IMMEDIATE,
    "high": PlanPriority.HIGH,
    "normal": PlanPriority.NORMAL,
    "low": PlanPriority.LOW,
    "deferred": PlanPriority.DEFERRED,
}

_ACTION_TYPE_MAP: dict[str, ReconciliationActionType] = {v.value: v for v in ReconciliationActionType}


# ── Adaptive Planner ─────────────────────────────────────────────────────


class AdaptivePlanner:
    """Wraps ReconciliationPlanner with learned strategy overrides."""

    def __init__(
        self,
        base_planner: ReconciliationPlanner | None = None,
        learner: StrategyLearner | None = None,
    ) -> None:
        self._base_planner = base_planner or ReconciliationPlanner()
        self._learner = learner or StrategyLearner()
        self._adaptive_plans: list[AdaptivePlan] = []

    @property
    def base_planner(self) -> ReconciliationPlanner:
        return self._base_planner

    @property
    def learner(self) -> StrategyLearner:
        return self._learner

    def plan_from_drift_adaptive(self, signal: DriftSignal) -> AdaptivePlan:
        """Generate an adaptive plan from a drift signal, applying learned overrides."""
        base_plan = self._base_planner.plan_from_drift(signal)
        recommendation = self._learner.recommend_for_drift_type(signal.drift_type.value)

        overrides: list[AdaptiveOverride] = []
        learning_applied = False

        # Apply learning if confidence is sufficient
        if recommendation.confidence_score > 0.3:
            learning_applied = True

            # Override priority if learned
            if recommendation.recommended_priority != base_plan.priority.value:
                new_priority = _PRIORITY_MAP.get(recommendation.recommended_priority, base_plan.priority)
                overrides.append(AdaptiveOverride(
                    field_name="priority",
                    original_value=base_plan.priority.value,
                    learned_value=new_priority.value,
                    confidence=recommendation.confidence_score,
                ))
                base_plan.priority = new_priority

            # Override action ordering if learned
            if recommendation.recommended_actions:
                learned_actions: list[ReconciliationAction] = []
                for action_name in recommendation.recommended_actions:
                    action_type = _ACTION_TYPE_MAP.get(action_name)
                    if action_type:
                        learned_actions.append(ReconciliationAction(
                            action_type=action_type,
                            target_provider=signal.provider_name,
                            priority=base_plan.priority,
                            source_drift_id=signal.signal_id,
                        ))
                if learned_actions:
                    original_actions = ",".join(a.action_type.value for a in base_plan.actions)
                    new_actions = ",".join(a.action_type.value for a in learned_actions)
                    if original_actions != new_actions:
                        overrides.append(AdaptiveOverride(
                            field_name="actions",
                            original_value=original_actions,
                            learned_value=new_actions,
                            confidence=recommendation.confidence_score,
                        ))
                        base_plan.actions = learned_actions

        adaptive = AdaptivePlan(
            base_plan_id=base_plan.plan_id,
            status=base_plan.status,
            priority=base_plan.priority,
            drift_signal_ids=base_plan.drift_signal_ids,
            actions=base_plan.actions,
            description=f"Adaptive: {base_plan.description}" if learning_applied else base_plan.description,
            learning_applied=learning_applied,
            confidence_score=recommendation.confidence_score,
            overrides_applied=overrides,
            recommendation_id=recommendation.recommendation_id,
        )
        self._adaptive_plans.append(adaptive)
        return adaptive

    def plan_from_batch_adaptive(self, signals: list[DriftSignal]) -> list[AdaptivePlan]:
        """Generate adaptive plans for multiple drift signals."""
        return [self.plan_from_drift_adaptive(s) for s in signals]

    def get_learning_stats(self) -> dict[str, Any]:
        """Get statistics on how learning has been applied."""
        total = len(self._adaptive_plans)
        learned = sum(1 for p in self._adaptive_plans if p.learning_applied)
        overridden = sum(p.override_count for p in self._adaptive_plans)
        avg_confidence = (
            sum(p.confidence_score for p in self._adaptive_plans) / total
            if total > 0 else 0.0
        )
        return {
            "total_plans": total,
            "learning_applied_count": learned,
            "learning_application_rate": round(learned / total, 3) if total > 0 else 0.0,
            "total_overrides": overridden,
            "avg_confidence": round(avg_confidence, 3),
        }

    def get_adaptive_plans(
        self,
        learning_applied: bool | None = None,
    ) -> list[AdaptivePlan]:
        results = self._adaptive_plans
        if learning_applied is not None:
            results = [p for p in results if p.learning_applied == learning_applied]
        return results

    @property
    def plan_count(self) -> int:
        return len(self._adaptive_plans)


# ── Module singleton ──────────────────────────────────────────────────────

_adaptive_planner: AdaptivePlanner | None = None


def get_adaptive_planner() -> AdaptivePlanner:
    global _adaptive_planner
    if _adaptive_planner is None:
        _adaptive_planner = AdaptivePlanner()
    return _adaptive_planner
