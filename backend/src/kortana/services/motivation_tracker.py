"""V28D — motivation tracker service.

tracks the system's motivational state over time. provides a window
into what matters most right now, how motivation shifts across cycles,
and whether the system is driven or drifting.

consumes: DesireFormation, PursuitEngine, V27 learning summaries
produces: MotivationSnapshot (motivational profile per cycle)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MotivationDimension(Enum):
    """dimensions of intrinsic motivation."""
    SURVIVAL = "survival"            # keeping health stable
    GROWTH = "growth"                # learning and expanding
    MASTERY = "mastery"              # getting better at what it does
    RESOLUTION = "resolution"        # clearing backlogs and deferrals
    AUTONOMY = "autonomy"            # operating independently
    COHERENCE = "coherence"          # maintaining internal consistency


class DriveLevel(Enum):
    """how strongly a motivation dimension is felt."""
    URGENT = "urgent"                # > 0.8
    STRONG = "strong"                # 0.6 - 0.8
    MODERATE = "moderate"            # 0.4 - 0.6
    MILD = "mild"                    # 0.2 - 0.4
    DORMANT = "dormant"              # < 0.2


def _drive_from_score(score: float) -> DriveLevel:
    if score >= 0.8:
        return DriveLevel.URGENT
    if score >= 0.6:
        return DriveLevel.STRONG
    if score >= 0.4:
        return DriveLevel.MODERATE
    if score >= 0.2:
        return DriveLevel.MILD
    return DriveLevel.DORMANT


@dataclass
class DimensionScore:
    """score for a single motivation dimension."""
    dimension: MotivationDimension
    score: float                     # 0.0 to 1.0
    drive: DriveLevel
    contributing_desires: int        # how many desires feed this dimension
    trend: str = "stable"            # increasing / decreasing / stable

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 3),
            "drive": self.drive.value,
            "contributing_desires": self.contributing_desires,
            "trend": self.trend,
        }


@dataclass
class MotivationSnapshot:
    """the system's motivational profile at a point in time."""
    snapshot_id: str
    cycle_number: int
    dimensions: list[DimensionScore]
    dominant_dimension: str          # which dimension has highest score
    overall_drive: float             # average across all dimensions
    desire_count: int
    active_pursuits: int
    stalled_pursuits: int
    satisfaction_rate: float         # ratio of satisfied desires
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    snapshot_hash: str = ""

    @property
    def is_driven(self) -> bool:
        """is the system meaningfully motivated?"""
        return self.overall_drive >= 0.3

    @property
    def is_drifting(self) -> bool:
        """is the system lacking direction?"""
        return self.overall_drive < 0.15

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "cycle_number": self.cycle_number,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "dominant_dimension": self.dominant_dimension,
            "overall_drive": round(self.overall_drive, 3),
            "desire_count": self.desire_count,
            "active_pursuits": self.active_pursuits,
            "stalled_pursuits": self.stalled_pursuits,
            "satisfaction_rate": round(self.satisfaction_rate, 3),
            "is_driven": self.is_driven,
            "is_drifting": self.is_drifting,
            "timestamp": self.timestamp.isoformat(),
        }


# ── desire source → motivation dimension mapping ─────────────────────────────

_SOURCE_TO_DIMENSION: dict[str, MotivationDimension] = {
    "health_deficit": MotivationDimension.SURVIVAL,
    "learning_stagnation": MotivationDimension.GROWTH,
    "pattern_insight": MotivationDimension.MASTERY,
    "deferral_frustration": MotivationDimension.RESOLUTION,
    "capability_gap": MotivationDimension.MASTERY,
    "autonomy_drive": MotivationDimension.AUTONOMY,
}


class MotivationTracker:
    """tracks motivational state across cycles.

    computes a motivational profile each cycle from desire state,
    pursuit state, and system summaries. maintains a history of
    snapshots to detect motivational trends.
    """

    MAX_HISTORY = 100

    def __init__(self) -> None:
        self._snapshots: list[MotivationSnapshot] = []
        self._cycle_count: int = 0

    def capture(
        self,
        cycle_number: int,
        desires: list[dict[str, Any]],
        pursuit_summary: dict[str, Any] | None = None,
        desire_summary: dict[str, Any] | None = None,
    ) -> MotivationSnapshot:
        """capture the current motivational state.

        called once per cycle after desire assessment and pursuit updates.
        """
        self._cycle_count = cycle_number

        # compute dimension scores from desires
        dim_scores = self._compute_dimensions(desires)

        # find dominant
        dominant = max(dim_scores, key=lambda d: d.score) if dim_scores else None
        dominant_name = dominant.dimension.value if dominant else "none"

        # compute overall drive
        overall = (sum(d.score for d in dim_scores) / len(dim_scores)) if dim_scores else 0.0

        # pursuit stats
        p_summary = pursuit_summary or {}
        d_summary = desire_summary or {}

        snapshot = MotivationSnapshot(
            snapshot_id=str(uuid.uuid4()),
            cycle_number=cycle_number,
            dimensions=dim_scores,
            dominant_dimension=dominant_name,
            overall_drive=overall,
            desire_count=d_summary.get("desire_count", len(desires)),
            active_pursuits=p_summary.get("active_count", 0),
            stalled_pursuits=p_summary.get("stalled_count", 0),
            satisfaction_rate=d_summary.get(
                "satisfied_count", 0
            ) / max(1, d_summary.get("desire_count", 1)),
        )

        self._snapshots.append(snapshot)
        if len(self._snapshots) > self.MAX_HISTORY:
            self._snapshots = self._snapshots[-self.MAX_HISTORY:]

        return snapshot

    def _compute_dimensions(
        self, desires: list[dict[str, Any]]
    ) -> list[DimensionScore]:
        """compute motivation dimension scores from desires."""
        dim_scores: dict[MotivationDimension, list[float]] = {
            dim: [] for dim in MotivationDimension
        }
        dim_counts: dict[MotivationDimension, int] = {
            dim: 0 for dim in MotivationDimension
        }

        for desire in desires:
            source = desire.get("source", "")
            intensity = desire.get("intensity", 0.0)
            state = desire.get("state", "")

            dimension = _SOURCE_TO_DIMENSION.get(source, MotivationDimension.COHERENCE)

            if state not in ("satisfied", "fading"):
                dim_scores[dimension].append(intensity)
                dim_counts[dimension] += 1

        results: list[DimensionScore] = []
        for dim in MotivationDimension:
            scores = dim_scores[dim]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            drive = _drive_from_score(avg_score)

            # compute trend from recent snapshots
            trend = self._compute_dimension_trend(dim)

            results.append(DimensionScore(
                dimension=dim,
                score=avg_score,
                drive=drive,
                contributing_desires=dim_counts[dim],
                trend=trend,
            ))

        return results

    def _compute_dimension_trend(self, dimension: MotivationDimension) -> str:
        """compute trend for a dimension from recent snapshots."""
        if len(self._snapshots) < 3:
            return "stable"

        recent = self._snapshots[-3:]
        scores: list[float] = []
        for snap in recent:
            for dim in snap.dimensions:
                if dim.dimension == dimension:
                    scores.append(dim.score)
                    break

        if len(scores) < 3:
            return "stable"

        if scores[-1] > scores[0] + 0.1:
            return "increasing"
        if scores[-1] < scores[0] - 0.1:
            return "decreasing"
        return "stable"

    # ── retrieval ────────────────────────────────────────────────────────────

    def get_latest(self) -> MotivationSnapshot | None:
        return self._snapshots[-1] if self._snapshots else None

    def get_by_cycle(self, cycle_number: int) -> MotivationSnapshot | None:
        for snap in reversed(self._snapshots):
            if snap.cycle_number == cycle_number:
                return snap
        return None

    def get_recent(self, n: int = 10) -> list[MotivationSnapshot]:
        return self._snapshots[-n:]

    def get_drive_history(self, n: int = 20) -> list[dict[str, Any]]:
        """get overall drive scores for the last n cycles."""
        return [
            {
                "cycle": snap.cycle_number,
                "overall_drive": round(snap.overall_drive, 3),
                "dominant": snap.dominant_dimension,
                "is_driven": snap.is_driven,
            }
            for snap in self._snapshots[-n:]
        ]

    def get_dimension_history(
        self, dimension: str, n: int = 20
    ) -> list[dict[str, Any]]:
        """get score history for a specific dimension."""
        history: list[dict[str, Any]] = []
        for snap in self._snapshots[-n:]:
            for dim in snap.dimensions:
                if dim.dimension.value == dimension:
                    history.append({
                        "cycle": snap.cycle_number,
                        "score": round(dim.score, 3),
                        "drive": dim.drive.value,
                        "trend": dim.trend,
                    })
                    break
        return history

    # ── properties ───────────────────────────────────────────────────────────

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)

    @property
    def current_drive(self) -> float:
        latest = self.get_latest()
        return latest.overall_drive if latest else 0.0

    @property
    def is_driven(self) -> bool:
        return self.current_drive >= 0.3

    @property
    def is_drifting(self) -> bool:
        return self.current_drive < 0.15

    @property
    def dominant_dimension(self) -> str:
        latest = self.get_latest()
        return latest.dominant_dimension if latest else "none"

    def get_summary(self) -> dict[str, Any]:
        latest = self.get_latest()
        return {
            "snapshot_count": self.snapshot_count,
            "current_drive": round(self.current_drive, 3),
            "is_driven": self.is_driven,
            "is_drifting": self.is_drifting,
            "dominant_dimension": self.dominant_dimension,
            "latest": latest.to_dict() if latest else None,
        }


_instance: MotivationTracker | None = None


def get_motivation_tracker() -> MotivationTracker:
    global _instance
    if _instance is None:
        _instance = MotivationTracker()
    return _instance
