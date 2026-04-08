"""V19B — Strategy Learner: strategy selection from historical outcome data."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict


# ── Data structures ───────────────────────────────────────────────────────


@dataclass
class ActionEffectiveness:
    """Effectiveness metrics for a specific action type."""

    action_type: str = ""
    success_rate: float = 0.0
    avg_retries: float = 0.0
    avg_time_to_resolve: float = 0.0
    sample_size: int = 0
    effectiveness_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "success_rate": round(self.success_rate, 3),
            "avg_retries": round(self.avg_retries, 2),
            "avg_time_to_resolve": round(self.avg_time_to_resolve, 1),
            "sample_size": self.sample_size,
            "effectiveness_score": round(self.effectiveness_score, 3),
        }


@dataclass
class StrategyRecommendation:
    """A learned recommendation for handling a specific drift type."""

    recommendation_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    drift_type: str = ""
    recommended_actions: list[str] = field(default_factory=list)
    recommended_priority: str = "normal"
    recommended_max_retries: int = 3
    confidence_score: float = 0.0
    reasoning: str = ""
    based_on_outcomes: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    recommendation_hash: str = ""

    def __post_init__(self) -> None:
        if not self.recommendation_hash:
            raw = f"{self.recommendation_id}:{self.drift_type}:{','.join(self.recommended_actions)}:{self.created_at}"
            self.recommendation_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "drift_type": self.drift_type,
            "recommended_actions": self.recommended_actions,
            "recommended_priority": self.recommended_priority,
            "recommended_max_retries": self.recommended_max_retries,
            "confidence_score": round(self.confidence_score, 3),
            "reasoning": self.reasoning,
            "based_on_outcomes": self.based_on_outcomes,
            "created_at": self.created_at,
            "recommendation_hash": self.recommendation_hash,
        }


# ── Strategy Learner ──────────────────────────────────────────────────────


class StrategyLearner:
    """Analyzes past outcomes to recommend better reconciliation strategies."""

    MIN_SAMPLE_SIZE = 3  # Minimum outcomes before making recommendations

    def __init__(self, tracker: OutcomeTracker | None = None) -> None:
        self._tracker = tracker or OutcomeTracker()
        self._recommendations: list[StrategyRecommendation] = []

    @property
    def tracker(self) -> OutcomeTracker:
        return self._tracker

    def get_action_effectiveness(self, action_type: str) -> ActionEffectiveness:
        """Calculate effectiveness metrics for a specific action type."""
        outcomes = self._tracker.get_outcomes_for_action_type(action_type)
        if not outcomes:
            return ActionEffectiveness(action_type=action_type)

        effective_count = sum(
            1 for o in outcomes
            if o.verdict in (OutcomeVerdict.EFFECTIVE, OutcomeVerdict.PARTIALLY_EFFECTIVE)
        )
        success_rate = effective_count / len(outcomes)
        avg_retries = sum(o.retries_needed for o in outcomes) / len(outcomes)
        resolved = [o for o in outcomes if o.time_to_resolve_sec > 0]
        avg_time = sum(o.time_to_resolve_sec for o in resolved) / len(resolved) if resolved else 0.0

        # Effectiveness score: weighted combination
        stability_bonus = sum(1 for o in outcomes if o.resolution_stable) / len(outcomes)
        effectiveness_score = (success_rate * 0.5) + (stability_bonus * 0.3) + (max(0, 1.0 - avg_retries / 5) * 0.2)

        return ActionEffectiveness(
            action_type=action_type,
            success_rate=success_rate,
            avg_retries=avg_retries,
            avg_time_to_resolve=avg_time,
            sample_size=len(outcomes),
            effectiveness_score=effectiveness_score,
        )

    def recommend_for_drift_type(self, drift_type: str) -> StrategyRecommendation:
        """Generate a strategy recommendation for a drift type based on historical data."""
        outcomes = self._tracker.get_outcomes_for_drift_type(drift_type)

        if len(outcomes) < self.MIN_SAMPLE_SIZE:
            rec = StrategyRecommendation(
                drift_type=drift_type,
                confidence_score=0.0,
                reasoning=f"Insufficient data ({len(outcomes)} outcomes, need {self.MIN_SAMPLE_SIZE})",
                based_on_outcomes=len(outcomes),
            )
            self._recommendations.append(rec)
            return rec

        # Analyze which action types were most effective
        action_scores: dict[str, float] = {}
        all_actions: set[str] = set()
        for o in outcomes:
            for a in o.action_types_used:
                all_actions.add(a)

        for action in all_actions:
            eff = self.get_action_effectiveness(action)
            action_scores[action] = eff.effectiveness_score

        # Sort by effectiveness
        sorted_actions = sorted(action_scores.keys(), key=lambda a: action_scores[a], reverse=True)

        # Priority recommendation based on resolution times
        avg_time = sum(o.time_to_resolve_sec for o in outcomes if o.time_to_resolve_sec > 0)
        count_timed = sum(1 for o in outcomes if o.time_to_resolve_sec > 0)
        avg_resolve = avg_time / count_timed if count_timed else 0

        if avg_resolve > 120:
            recommended_priority = "immediate"
        elif avg_resolve > 60:
            recommended_priority = "high"
        else:
            recommended_priority = "normal"

        # Retry recommendation based on historical retries
        avg_retries = sum(o.retries_needed for o in outcomes) / len(outcomes)
        if avg_retries > 2:
            recommended_max_retries = max(3, int(avg_retries) + 1)
        else:
            recommended_max_retries = 3

        # Confidence based on sample size and consistency
        effectiveness_rate = sum(
            1 for o in outcomes
            if o.verdict in (OutcomeVerdict.EFFECTIVE, OutcomeVerdict.PARTIALLY_EFFECTIVE)
        ) / len(outcomes)
        confidence = min(1.0, (len(outcomes) / 20) * effectiveness_rate)

        reasoning_parts: list[str] = []
        if sorted_actions:
            reasoning_parts.append(f"Best actions: {', '.join(sorted_actions[:3])}")
        reasoning_parts.append(f"Effectiveness rate: {effectiveness_rate:.0%}")
        reasoning_parts.append(f"Avg resolution: {avg_resolve:.0f}s")
        reasoning_parts.append(f"Avg retries: {avg_retries:.1f}")

        rec = StrategyRecommendation(
            drift_type=drift_type,
            recommended_actions=sorted_actions,
            recommended_priority=recommended_priority,
            recommended_max_retries=recommended_max_retries,
            confidence_score=confidence,
            reasoning="; ".join(reasoning_parts),
            based_on_outcomes=len(outcomes),
        )
        self._recommendations.append(rec)
        return rec

    def get_priority_adjustment(self, drift_type: str) -> str:
        """Get recommended priority for a drift type."""
        rec = self.recommend_for_drift_type(drift_type)
        return rec.recommended_priority if rec.confidence_score > 0 else "normal"

    def get_retry_recommendation(self, drift_type: str) -> int:
        """Get recommended max retries for a drift type."""
        rec = self.recommend_for_drift_type(drift_type)
        return rec.recommended_max_retries if rec.confidence_score > 0 else 3

    def get_escalation_timing(self, drift_type: str) -> dict[str, Any]:
        """Get escalation timing based on historical data."""
        outcomes = self._tracker.get_outcomes_for_drift_type(drift_type)
        escalated = [o for o in outcomes if o.escalated]
        non_escalated = [o for o in outcomes if not o.escalated]

        esc_effective = sum(1 for o in escalated if o.verdict == OutcomeVerdict.EFFECTIVE) / len(escalated) if escalated else 0
        non_esc_effective = sum(1 for o in non_escalated if o.verdict == OutcomeVerdict.EFFECTIVE) / len(non_escalated) if non_escalated else 0

        return {
            "escalation_rate": len(escalated) / len(outcomes) if outcomes else 0,
            "escalated_effectiveness": round(esc_effective, 3),
            "non_escalated_effectiveness": round(non_esc_effective, 3),
            "recommend_earlier_escalation": esc_effective > non_esc_effective + 0.2,
            "sample_size": len(outcomes),
        }

    def get_recommendations(self) -> list[StrategyRecommendation]:
        return self._recommendations

    @property
    def recommendation_count(self) -> int:
        return len(self._recommendations)


# ── Module singleton ──────────────────────────────────────────────────────

_strategy_learner: StrategyLearner | None = None


def get_strategy_learner() -> StrategyLearner:
    global _strategy_learner
    if _strategy_learner is None:
        _strategy_learner = StrategyLearner()
    return _strategy_learner
