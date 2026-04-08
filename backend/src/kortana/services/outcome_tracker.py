"""V19A — Outcome Tracker: reconciliation outcome recording & analysis."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ── Enums ─────────────────────────────────────────────────────────────────


class OutcomeVerdict(Enum):
    """Verdict on how effective a reconciliation was."""

    EFFECTIVE = "effective"
    PARTIALLY_EFFECTIVE = "partially_effective"
    INEFFECTIVE = "ineffective"
    COUNTERPRODUCTIVE = "counterproductive"
    INCONCLUSIVE = "inconclusive"


# ── Data structures ───────────────────────────────────────────────────────


@dataclass
class ReconciliationOutcome:
    """Recorded outcome of a reconciliation execution."""

    outcome_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    execution_id: str = ""
    plan_id: str = ""
    drift_type: str = ""
    action_types_used: list[str] = field(default_factory=list)
    verdict: OutcomeVerdict = OutcomeVerdict.INCONCLUSIVE
    time_to_resolve_sec: float = 0.0
    retries_needed: int = 0
    escalated: bool = False
    resolution_stable: bool = True
    learning_applied: bool = False
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    outcome_hash: str = ""

    def __post_init__(self) -> None:
        if not self.outcome_hash:
            raw = f"{self.outcome_id}:{self.execution_id}:{self.verdict.value}:{self.drift_type}:{self.recorded_at}"
            self.outcome_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "execution_id": self.execution_id,
            "plan_id": self.plan_id,
            "drift_type": self.drift_type,
            "action_types_used": self.action_types_used,
            "verdict": self.verdict.value,
            "time_to_resolve_sec": self.time_to_resolve_sec,
            "retries_needed": self.retries_needed,
            "escalated": self.escalated,
            "resolution_stable": self.resolution_stable,
            "learning_applied": self.learning_applied,
            "recorded_at": self.recorded_at,
            "outcome_hash": self.outcome_hash,
        }


# ── Outcome Tracker ──────────────────────────────────────────────────────


class OutcomeTracker:
    """Records and analyzes reconciliation outcomes."""

    def __init__(self) -> None:
        self._outcomes: list[ReconciliationOutcome] = []

    def record_outcome(
        self,
        execution_id: str,
        plan_id: str,
        drift_type: str,
        action_types_used: list[str],
        verdict: OutcomeVerdict,
        time_to_resolve_sec: float = 0.0,
        retries_needed: int = 0,
        escalated: bool = False,
        resolution_stable: bool = True,
        learning_applied: bool = False,
    ) -> ReconciliationOutcome:
        """Record the outcome of a reconciliation execution."""
        outcome = ReconciliationOutcome(
            execution_id=execution_id,
            plan_id=plan_id,
            drift_type=drift_type,
            action_types_used=action_types_used,
            verdict=verdict,
            time_to_resolve_sec=time_to_resolve_sec,
            retries_needed=retries_needed,
            escalated=escalated,
            resolution_stable=resolution_stable,
            learning_applied=learning_applied,
        )
        self._outcomes.append(outcome)
        return outcome

    # ── queries ───────────────────────────────────────────────────────

    def get_outcomes(
        self,
        verdict: OutcomeVerdict | None = None,
        learning_applied: bool | None = None,
    ) -> list[ReconciliationOutcome]:
        results = self._outcomes
        if verdict is not None:
            results = [o for o in results if o.verdict == verdict]
        if learning_applied is not None:
            results = [o for o in results if o.learning_applied == learning_applied]
        return results

    def get_outcomes_for_drift_type(self, drift_type: str) -> list[ReconciliationOutcome]:
        return [o for o in self._outcomes if o.drift_type == drift_type]

    def get_outcomes_for_action_type(self, action_type: str) -> list[ReconciliationOutcome]:
        return [o for o in self._outcomes if action_type in o.action_types_used]

    def get_effectiveness_rate(self, drift_type: str = "") -> float:
        """Get effectiveness rate (0.0-1.0) for outcomes, optionally filtered by drift type."""
        outcomes = self.get_outcomes_for_drift_type(drift_type) if drift_type else self._outcomes
        if not outcomes:
            return 0.0
        effective = sum(1 for o in outcomes if o.verdict in (OutcomeVerdict.EFFECTIVE, OutcomeVerdict.PARTIALLY_EFFECTIVE))
        return effective / len(outcomes)

    def get_avg_resolution_time(self, drift_type: str = "") -> float:
        """Get average resolution time in seconds."""
        outcomes = self.get_outcomes_for_drift_type(drift_type) if drift_type else self._outcomes
        resolved = [o for o in outcomes if o.time_to_resolve_sec > 0]
        if not resolved:
            return 0.0
        return sum(o.time_to_resolve_sec for o in resolved) / len(resolved)

    def get_avg_retries(self, drift_type: str = "") -> float:
        """Get average retries needed."""
        outcomes = self.get_outcomes_for_drift_type(drift_type) if drift_type else self._outcomes
        if not outcomes:
            return 0.0
        return sum(o.retries_needed for o in outcomes) / len(outcomes)

    def get_escalation_rate(self, drift_type: str = "") -> float:
        """Get rate of escalation to human."""
        outcomes = self.get_outcomes_for_drift_type(drift_type) if drift_type else self._outcomes
        if not outcomes:
            return 0.0
        return sum(1 for o in outcomes if o.escalated) / len(outcomes)

    def get_stability_rate(self, drift_type: str = "") -> float:
        """Get rate of resolutions that remained stable."""
        outcomes = self.get_outcomes_for_drift_type(drift_type) if drift_type else self._outcomes
        effective = [o for o in outcomes if o.verdict in (OutcomeVerdict.EFFECTIVE, OutcomeVerdict.PARTIALLY_EFFECTIVE)]
        if not effective:
            return 0.0
        return sum(1 for o in effective if o.resolution_stable) / len(effective)

    @property
    def outcome_count(self) -> int:
        return len(self._outcomes)

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_outcomes": self.outcome_count,
            "effectiveness_rate": round(self.get_effectiveness_rate(), 3),
            "avg_resolution_time_sec": round(self.get_avg_resolution_time(), 1),
            "avg_retries": round(self.get_avg_retries(), 2),
            "escalation_rate": round(self.get_escalation_rate(), 3),
            "stability_rate": round(self.get_stability_rate(), 3),
        }


# ── Module singleton ──────────────────────────────────────────────────────

_outcome_tracker: OutcomeTracker | None = None


def get_outcome_tracker() -> OutcomeTracker:
    global _outcome_tracker
    if _outcome_tracker is None:
        _outcome_tracker = OutcomeTracker()
    return _outcome_tracker
