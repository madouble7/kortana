"""V26C — health assessor.

multi-dimensional health assessment. not just "is the process up" but:
is the system continuous, coherent, responsive, capable, governed, and learning?

each dimension produces a score (0-100) and a level. the combination creates
a complete health snapshot that the degradation manager and future V27 learning
loop can act on.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class HealthDimension(str, Enum):
    """the six dimensions of system health."""

    CONTINUITY = "continuity"        # are cycles running without gaps?
    COHERENCE = "coherence"          # are decisions consistent with context?
    RESPONSIVENESS = "responsiveness" # how fast are cycles completing?
    CAPACITY = "capacity"            # how much is being processed per cycle?
    GOVERNANCE = "governance"        # are governance checks running?
    LEARNING = "learning"            # is the system improving over time?


class HealthLevel(str, Enum):
    """qualitative health levels."""

    THRIVING = "thriving"      # 80-100: excellent
    HEALTHY = "healthy"        # 60-79: normal operation
    STRAINED = "strained"      # 40-59: degradation beginning
    DEGRADED = "degraded"      # 20-39: serious issues
    CRITICAL = "critical"      # 0-19: intervention needed


def _score_to_level(score: float) -> HealthLevel:
    """convert a numeric score to a health level."""
    if score >= 80:
        return HealthLevel.THRIVING
    if score >= 60:
        return HealthLevel.HEALTHY
    if score >= 40:
        return HealthLevel.STRAINED
    if score >= 20:
        return HealthLevel.DEGRADED
    return HealthLevel.CRITICAL


@dataclass
class DimensionAssessment:
    """assessment of a single health dimension."""

    dimension: HealthDimension
    level: HealthLevel
    score: float  # 0-100
    indicators: list[str] = field(default_factory=list)
    assessed_at: str = ""

    def __post_init__(self) -> None:
        if not self.assessed_at:
            self.assessed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "level": self.level.value,
            "score": round(self.score, 1),
            "indicators": self.indicators,
            "assessed_at": self.assessed_at,
        }


@dataclass
class HealthSnapshot:
    """complete health snapshot across all dimensions."""

    snapshot_id: str = ""
    cycle_number: int = 0
    overall_level: HealthLevel = HealthLevel.HEALTHY
    overall_score: float = 0.0
    dimensions: dict[str, DimensionAssessment] = field(default_factory=dict)
    anomalies: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    assessed_at: str = ""
    snapshot_hash: str = ""

    def __post_init__(self) -> None:
        if not self.snapshot_id:
            self.snapshot_id = f"health-{uuid.uuid4().hex[:12]}"
        if not self.assessed_at:
            self.assessed_at = datetime.now(timezone.utc).isoformat()
        if not self.snapshot_hash:
            raw = f"{self.snapshot_id}:{self.cycle_number}:{self.assessed_at}"
            self.snapshot_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "cycle_number": self.cycle_number,
            "overall_level": self.overall_level.value,
            "overall_score": round(self.overall_score, 1),
            "dimensions": {k: v.to_dict() for k, v in self.dimensions.items()},
            "anomalies": self.anomalies,
            "recommendations": self.recommendations,
            "assessed_at": self.assessed_at,
            "snapshot_hash": self.snapshot_hash,
        }


class HealthAssessor:
    """multi-dimensional health assessor.

    evaluates six dimensions of system health based on heartbeat and cycle
    data, producing snapshots that drive degradation decisions and future
    learning signals.
    """

    def __init__(self) -> None:
        self._snapshots: list[HealthSnapshot] = []

    # ── assessment ───────────────────────────────────────────────────────

    def assess(self, cycle_number: int = 0,
               beat_count: int = 0,
               uptime_beats: int = 0,
               avg_duration_ms: float = 0.0,
               total_observations: int = 0,
               total_decisions: int = 0,
               total_deferrals: int = 0,
               total_actions: int = 0,
               cycle_count: int = 0,
               finalized_cycles: int = 0,
               deferral_streak: int = 0) -> HealthSnapshot:
        """run a complete health assessment across all dimensions."""
        dimensions: dict[str, DimensionAssessment] = {}

        dimensions["continuity"] = self._assess_continuity(
            beat_count, uptime_beats, cycle_count, finalized_cycles)
        dimensions["coherence"] = self._assess_coherence(
            total_decisions, total_deferrals, deferral_streak)
        dimensions["responsiveness"] = self._assess_responsiveness(
            avg_duration_ms, beat_count)
        dimensions["capacity"] = self._assess_capacity(
            total_observations, total_decisions, total_actions, cycle_count)
        dimensions["governance"] = self._assess_governance(
            finalized_cycles, cycle_count)
        dimensions["learning"] = self._assess_learning(
            total_deferrals, deferral_streak, cycle_count)

        # overall score is weighted average
        weights = {
            "continuity": 0.25,
            "coherence": 0.20,
            "responsiveness": 0.15,
            "capacity": 0.15,
            "governance": 0.15,
            "learning": 0.10,
        }
        overall_score = sum(
            dimensions[k].score * weights[k] for k in weights
        )
        overall_level = _score_to_level(overall_score)

        # detect anomalies
        anomalies: list[str] = []
        for dim_name, dim in dimensions.items():
            if dim.level in (HealthLevel.DEGRADED, HealthLevel.CRITICAL):
                anomalies.append(f"{dim_name} is {dim.level.value} (score: {dim.score:.1f})")

        # generate recommendations
        recommendations: list[str] = []
        if dimensions["continuity"].score < 60:
            recommendations.append("investigate cycle gaps — heartbeat may be unstable")
        if dimensions["coherence"].score < 60:
            recommendations.append("high deferral rate — review decision quality")
        if dimensions["responsiveness"].score < 60:
            recommendations.append("cycles running slow — check for bottlenecks")
        if dimensions["learning"].score < 60:
            recommendations.append("persistent deferrals — learning loop may be stalled")

        snapshot = HealthSnapshot(
            cycle_number=cycle_number,
            overall_level=overall_level,
            overall_score=overall_score,
            dimensions=dimensions,
            anomalies=anomalies,
            recommendations=recommendations,
        )
        self._snapshots.append(snapshot)
        return snapshot

    # ── dimension assessors ──────────────────────────────────────────────

    def _assess_continuity(self, beat_count: int, uptime_beats: int,
                           cycle_count: int, finalized_cycles: int) -> DimensionAssessment:
        """are cycles running without gaps?"""
        indicators: list[str] = []
        score = 100.0

        if beat_count == 0:
            score = 0.0
            indicators.append("no heartbeats recorded")
        else:
            uptime_ratio = uptime_beats / beat_count
            score = uptime_ratio * 100
            indicators.append(f"uptime ratio: {uptime_ratio:.2f}")

        if cycle_count > 0 and finalized_cycles < cycle_count:
            gap_ratio = (cycle_count - finalized_cycles) / cycle_count
            score -= gap_ratio * 30
            indicators.append(f"unfinalized cycles: {cycle_count - finalized_cycles}")

        score = max(0.0, min(100.0, score))
        return DimensionAssessment(
            dimension=HealthDimension.CONTINUITY,
            level=_score_to_level(score),
            score=score,
            indicators=indicators,
        )

    def _assess_coherence(self, total_decisions: int, total_deferrals: int,
                          deferral_streak: int) -> DimensionAssessment:
        """are decisions consistent with context?"""
        indicators: list[str] = []
        score = 100.0

        if total_decisions > 0:
            deferral_ratio = total_deferrals / (total_decisions + total_deferrals)
            score = (1 - deferral_ratio) * 100
            indicators.append(f"deferral ratio: {deferral_ratio:.2f}")
        else:
            score = 50.0  # no decisions = neutral
            indicators.append("no decisions recorded")

        if deferral_streak > 3:
            score -= (deferral_streak - 3) * 10
            indicators.append(f"deferral streak: {deferral_streak} cycles")

        score = max(0.0, min(100.0, score))
        return DimensionAssessment(
            dimension=HealthDimension.COHERENCE,
            level=_score_to_level(score),
            score=score,
            indicators=indicators,
        )

    def _assess_responsiveness(self, avg_duration_ms: float,
                               beat_count: int) -> DimensionAssessment:
        """how fast are cycles completing?"""
        indicators: list[str] = []
        score = 100.0

        if beat_count == 0:
            score = 50.0
            indicators.append("no beats to measure")
        elif avg_duration_ms > 0:
            # target: < 1000ms = 100, < 5000ms = 80, < 10000ms = 60, etc.
            if avg_duration_ms <= 1000:
                score = 100.0
            elif avg_duration_ms <= 5000:
                score = 100 - ((avg_duration_ms - 1000) / 4000) * 20
            elif avg_duration_ms <= 10000:
                score = 80 - ((avg_duration_ms - 5000) / 5000) * 20
            else:
                score = max(10.0, 60 - ((avg_duration_ms - 10000) / 10000) * 30)
            indicators.append(f"avg duration: {avg_duration_ms:.0f}ms")

        score = max(0.0, min(100.0, score))
        return DimensionAssessment(
            dimension=HealthDimension.RESPONSIVENESS,
            level=_score_to_level(score),
            score=score,
            indicators=indicators,
        )

    def _assess_capacity(self, total_observations: int, total_decisions: int,
                         total_actions: int, cycle_count: int) -> DimensionAssessment:
        """how much is being processed per cycle?"""
        indicators: list[str] = []
        score = 50.0  # baseline

        if cycle_count > 0:
            obs_per_cycle = total_observations / cycle_count
            dec_per_cycle = total_decisions / cycle_count
            act_per_cycle = total_actions / cycle_count

            # any activity is good; score increases with throughput
            activity = obs_per_cycle + dec_per_cycle + act_per_cycle
            if activity > 0:
                score = min(100.0, 50 + activity * 10)
            indicators.append(f"obs/cycle: {obs_per_cycle:.1f}")
            indicators.append(f"dec/cycle: {dec_per_cycle:.1f}")
            indicators.append(f"act/cycle: {act_per_cycle:.1f}")
        else:
            indicators.append("no cycles to measure")

        score = max(0.0, min(100.0, score))
        return DimensionAssessment(
            dimension=HealthDimension.CAPACITY,
            level=_score_to_level(score),
            score=score,
            indicators=indicators,
        )

    def _assess_governance(self, finalized_cycles: int,
                           cycle_count: int) -> DimensionAssessment:
        """are governance checks running?"""
        indicators: list[str] = []
        score = 100.0

        if cycle_count == 0:
            score = 50.0
            indicators.append("no cycles to assess governance")
        else:
            finalize_ratio = finalized_cycles / cycle_count
            score = finalize_ratio * 100
            indicators.append(f"finalization ratio: {finalize_ratio:.2f}")

        score = max(0.0, min(100.0, score))
        return DimensionAssessment(
            dimension=HealthDimension.GOVERNANCE,
            level=_score_to_level(score),
            score=score,
            indicators=indicators,
        )

    def _assess_learning(self, total_deferrals: int, deferral_streak: int,
                         cycle_count: int) -> DimensionAssessment:
        """is the system improving over time?"""
        indicators: list[str] = []
        score = 70.0  # baseline optimistic

        if cycle_count > 5:
            # if deferrals are accumulating faster than cycles, learning is stalled
            deferral_rate = total_deferrals / cycle_count if cycle_count > 0 else 0
            if deferral_rate > 1:
                score -= (deferral_rate - 1) * 15
                indicators.append(f"deferral rate: {deferral_rate:.2f}/cycle")

            if deferral_streak > 3:
                score -= (deferral_streak - 3) * 10
                indicators.append(f"same deferral persisted {deferral_streak} cycles")
        else:
            indicators.append("too few cycles to assess learning trends")

        score = max(0.0, min(100.0, score))
        return DimensionAssessment(
            dimension=HealthDimension.LEARNING,
            level=_score_to_level(score),
            score=score,
            indicators=indicators,
        )

    # ── queries ──────────────────────────────────────────────────────────

    def get_snapshot(self, snapshot_id: str) -> HealthSnapshot | None:
        """retrieve a specific snapshot."""
        for s in self._snapshots:
            if s.snapshot_id == snapshot_id:
                return s
        return None

    def get_recent(self, n: int = 10) -> list[HealthSnapshot]:
        """get the most recent n snapshots."""
        return list(reversed(self._snapshots[-n:]))

    def get_trends(self, dimension: str, n: int = 10) -> list[dict[str, Any]]:
        """get score trends for a specific dimension over the last n snapshots."""
        recent = self._snapshots[-n:]
        trends: list[dict[str, Any]] = []
        for s in recent:
            if dimension in s.dimensions:
                dim = s.dimensions[dimension]
                trends.append({
                    "cycle_number": s.cycle_number,
                    "score": dim.score,
                    "level": dim.level.value,
                    "assessed_at": s.assessed_at,
                })
        return trends

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)

    def get_summary(self) -> dict[str, Any]:
        """summary of health assessments."""
        last = self._snapshots[-1] if self._snapshots else None
        return {
            "snapshot_count": self.snapshot_count,
            "current_level": last.overall_level.value if last else "unknown",
            "current_score": round(last.overall_score, 1) if last else 0,
            "anomaly_count": len(last.anomalies) if last else 0,
            "recommendation_count": len(last.recommendations) if last else 0,
            "last_snapshot_id": last.snapshot_id if last else None,
        }


# ── module singleton ─────────────────────────────────────────────────────

_health_assessor: HealthAssessor | None = None


def get_health_assessor() -> HealthAssessor:
    """get the module-level health assessor singleton."""
    global _health_assessor
    if _health_assessor is None:
        _health_assessor = HealthAssessor()
    return _health_assessor
