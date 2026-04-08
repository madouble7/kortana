"""V19D — Improvement Tracker: self-improvement metrics & feedback loop."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict


# ── Enums ─────────────────────────────────────────────────────────────────


class LearningMaturity(Enum):
    """Maturity level of the learning system."""

    NASCENT = "nascent"
    DEVELOPING = "developing"
    MATURE = "mature"
    EXPERT = "expert"


# ── Data structures ───────────────────────────────────────────────────────


@dataclass
class ImprovementMetric:
    """Comparison between default and learned plan performance."""

    metric_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    drift_type: str = ""
    default_effectiveness_rate: float = 0.0
    learned_effectiveness_rate: float = 0.0
    improvement_pct: float = 0.0
    default_avg_time: float = 0.0
    learned_avg_time: float = 0.0
    time_improvement_pct: float = 0.0
    default_sample_size: int = 0
    learned_sample_size: int = 0
    metric_hash: str = ""

    def __post_init__(self) -> None:
        if not self.metric_hash:
            raw = f"{self.metric_id}:{self.drift_type}:{self.improvement_pct}"
            self.metric_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "drift_type": self.drift_type,
            "default_effectiveness_rate": round(self.default_effectiveness_rate, 3),
            "learned_effectiveness_rate": round(self.learned_effectiveness_rate, 3),
            "improvement_pct": round(self.improvement_pct, 1),
            "default_avg_time": round(self.default_avg_time, 1),
            "learned_avg_time": round(self.learned_avg_time, 1),
            "time_improvement_pct": round(self.time_improvement_pct, 1),
            "default_sample_size": self.default_sample_size,
            "learned_sample_size": self.learned_sample_size,
            "metric_hash": self.metric_hash,
        }


@dataclass
class ImprovementReport:
    """Overall improvement report."""

    report_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    metrics: list[ImprovementMetric] = field(default_factory=list)
    overall_improvement_pct: float = 0.0
    learning_maturity: LearningMaturity = LearningMaturity.NASCENT
    total_outcomes_analyzed: int = 0
    total_default_outcomes: int = 0
    total_learned_outcomes: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    report_hash: str = ""

    def __post_init__(self) -> None:
        if not self.report_hash:
            raw = f"{self.report_id}:{self.overall_improvement_pct}:{self.learning_maturity.value}:{self.created_at}"
            self.report_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "metrics": [m.to_dict() for m in self.metrics],
            "overall_improvement_pct": round(self.overall_improvement_pct, 1),
            "learning_maturity": self.learning_maturity.value,
            "total_outcomes_analyzed": self.total_outcomes_analyzed,
            "total_default_outcomes": self.total_default_outcomes,
            "total_learned_outcomes": self.total_learned_outcomes,
            "created_at": self.created_at,
            "report_hash": self.report_hash,
        }


# ── Improvement Tracker ──────────────────────────────────────────────────


class ImprovementTracker:
    """Tracks how learning improves recovery over time."""

    def __init__(self, tracker: OutcomeTracker | None = None) -> None:
        self._tracker = tracker or OutcomeTracker()
        self._reports: list[ImprovementReport] = []

    @property
    def tracker(self) -> OutcomeTracker:
        return self._tracker

    def generate_report(self) -> ImprovementReport:
        """Generate an improvement report comparing default vs learned outcomes."""
        all_outcomes = self._tracker.get_outcomes()
        default_outcomes = [o for o in all_outcomes if not o.learning_applied]
        learned_outcomes = [o for o in all_outcomes if o.learning_applied]

        # Compute per-drift-type metrics
        drift_types: set[str] = {o.drift_type for o in all_outcomes if o.drift_type}
        metrics: list[ImprovementMetric] = []

        for dt in sorted(drift_types):
            dt_default = [o for o in default_outcomes if o.drift_type == dt]
            dt_learned = [o for o in learned_outcomes if o.drift_type == dt]

            def _effectiveness(outcomes: list) -> float:
                if not outcomes:
                    return 0.0
                return sum(
                    1 for o in outcomes
                    if o.verdict in (OutcomeVerdict.EFFECTIVE, OutcomeVerdict.PARTIALLY_EFFECTIVE)
                ) / len(outcomes)

            def _avg_time(outcomes: list) -> float:
                timed = [o for o in outcomes if o.time_to_resolve_sec > 0]
                if not timed:
                    return 0.0
                return sum(o.time_to_resolve_sec for o in timed) / len(timed)

            d_eff = _effectiveness(dt_default)
            l_eff = _effectiveness(dt_learned)
            d_time = _avg_time(dt_default)
            l_time = _avg_time(dt_learned)

            improvement = ((l_eff - d_eff) / d_eff * 100) if d_eff > 0 else 0.0
            time_improvement = ((d_time - l_time) / d_time * 100) if d_time > 0 else 0.0

            metrics.append(ImprovementMetric(
                drift_type=dt,
                default_effectiveness_rate=d_eff,
                learned_effectiveness_rate=l_eff,
                improvement_pct=improvement,
                default_avg_time=d_time,
                learned_avg_time=l_time,
                time_improvement_pct=time_improvement,
                default_sample_size=len(dt_default),
                learned_sample_size=len(dt_learned),
            ))

        # Overall improvement
        d_eff_all = sum(1 for o in default_outcomes if o.verdict in (OutcomeVerdict.EFFECTIVE, OutcomeVerdict.PARTIALLY_EFFECTIVE)) / len(default_outcomes) if default_outcomes else 0.0
        l_eff_all = sum(1 for o in learned_outcomes if o.verdict in (OutcomeVerdict.EFFECTIVE, OutcomeVerdict.PARTIALLY_EFFECTIVE)) / len(learned_outcomes) if learned_outcomes else 0.0
        overall_improvement = ((l_eff_all - d_eff_all) / d_eff_all * 100) if d_eff_all > 0 else 0.0

        maturity = self._compute_maturity(len(all_outcomes), len(learned_outcomes), overall_improvement)

        report = ImprovementReport(
            metrics=metrics,
            overall_improvement_pct=overall_improvement,
            learning_maturity=maturity,
            total_outcomes_analyzed=len(all_outcomes),
            total_default_outcomes=len(default_outcomes),
            total_learned_outcomes=len(learned_outcomes),
        )
        self._reports.append(report)
        return report

    def get_learning_maturity(self) -> LearningMaturity:
        """Get current learning maturity level."""
        all_outcomes = self._tracker.get_outcomes()
        learned = [o for o in all_outcomes if o.learning_applied]
        if not self._reports:
            return self._compute_maturity(len(all_outcomes), len(learned), 0.0)
        return self._reports[-1].learning_maturity

    def get_improvement_trend(self) -> list[dict[str, Any]]:
        """Get improvement trend across reports."""
        return [
            {
                "report_id": r.report_id,
                "overall_improvement_pct": round(r.overall_improvement_pct, 1),
                "maturity": r.learning_maturity.value,
                "outcomes_analyzed": r.total_outcomes_analyzed,
                "created_at": r.created_at,
            }
            for r in self._reports
        ]

    def get_reports(self) -> list[ImprovementReport]:
        return self._reports

    def get_latest_report(self) -> ImprovementReport | None:
        return self._reports[-1] if self._reports else None

    @property
    def report_count(self) -> int:
        return len(self._reports)

    @staticmethod
    def _compute_maturity(
        total_outcomes: int,
        learned_outcomes: int,
        overall_improvement: float,
    ) -> LearningMaturity:
        if total_outcomes < 5:
            return LearningMaturity.NASCENT
        if learned_outcomes < 3 or overall_improvement < 5:
            return LearningMaturity.DEVELOPING
        if overall_improvement >= 20 and learned_outcomes >= 10:
            return LearningMaturity.EXPERT
        return LearningMaturity.MATURE


# ── Module singleton ──────────────────────────────────────────────────────

_improvement_tracker: ImprovementTracker | None = None


def get_improvement_tracker() -> ImprovementTracker:
    global _improvement_tracker
    if _improvement_tracker is None:
        _improvement_tracker = ImprovementTracker()
    return _improvement_tracker
