"""
V29C — Trait Evolution: How Traits Change Over Time

Tracks the trajectory of each trait through the system's developmental
history.  While V29A (self_portrait) computes the current snapshot,
trait evolution tracks the *how* and *why* of change.

For each trait, it maintains:
  - Full score history across cycles
  - Velocity (rate of change)
  - Stability (inverse of recent variance)
  - Crystallization status (stable enough to be "core identity")
  - Drift status (changing rapidly — identity in flux)

Crystallized traits are reported to V29D (continuity_anchor) for anchoring.
Drifting traits are reported to V29B (identity_narrative) as transformation
events.

The trait evolution engine answers: "how am i changing, and which parts
of me are settling into permanence?"
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ── Enums ────────────────────────────────────────────────────────────────────


class TraitStatus(Enum):
    """Status of a trait's evolutionary trajectory."""
    VOLATILE = "volatile"          # high variance, changing rapidly
    DEVELOPING = "developing"      # moderate change, trending
    SETTLING = "settling"          # variance decreasing
    CRYSTALLIZED = "crystallized"  # stable enough to be core identity
    DORMANT = "dormant"            # very low score, minimal change


# ── Thresholds ───────────────────────────────────────────────────────────────

CRYSTALLIZATION_STABILITY = 0.95    # stability threshold to crystallize
CRYSTALLIZATION_MIN_CYCLES = 15     # minimum history length to crystallize
VOLATILE_STABILITY = 0.3           # below this = volatile
DRIFT_VELOCITY = 0.02              # above this absolute velocity = drifting
DORMANT_SCORE = 0.15               # below this + low variance = dormant
HISTORY_WINDOW = 50                # max history per trait


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass
class TraitEvolutionEvent:
    """A single evolution event — a notable change to a trait."""
    event_id: str
    trait_name: str
    cycle_number: int
    old_score: float
    new_score: float
    delta: float
    source: str  # "lesson:success", "desire:autonomy_drive", etc.
    significance: float = 0.0  # 0-1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "trait_name": self.trait_name,
            "cycle_number": self.cycle_number,
            "old_score": round(self.old_score, 4),
            "new_score": round(self.new_score, 4),
            "delta": round(self.delta, 4),
            "source": self.source,
            "significance": round(self.significance, 4),
        }


@dataclass
class TraitTrajectory:
    """Full trajectory analysis for a single trait."""
    trait_name: str
    current_score: float
    history: List[Tuple[int, float]] = field(default_factory=list)
    velocity: float = 0.0          # rate of change (positive = growing)
    stability: float = 1.0         # 0-1, inverse of variance
    status: TraitStatus = TraitStatus.DEVELOPING
    crystallized_at: Optional[int] = None  # cycle when crystallized
    events: List[TraitEvolutionEvent] = field(default_factory=list)

    @property
    def is_crystallized(self) -> bool:
        return self.status == TraitStatus.CRYSTALLIZED

    @property
    def is_drifting(self) -> bool:
        return abs(self.velocity) > DRIFT_VELOCITY

    @property
    def trend(self) -> str:
        if self.velocity > DRIFT_VELOCITY:
            return "increasing"
        if self.velocity < -DRIFT_VELOCITY:
            return "decreasing"
        return "stable"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trait_name": self.trait_name,
            "current_score": round(self.current_score, 4),
            "velocity": round(self.velocity, 4),
            "stability": round(self.stability, 4),
            "status": self.status.value,
            "trend": self.trend,
            "is_crystallized": self.is_crystallized,
            "is_drifting": self.is_drifting,
            "crystallized_at": self.crystallized_at,
            "history_length": len(self.history),
            "recent_events": [e.to_dict() for e in self.events[-3:]],
        }


@dataclass
class EvolutionSnapshot:
    """Snapshot of all trait trajectories at a given cycle."""
    snapshot_id: str
    cycle_number: int
    trajectories: Dict[str, TraitTrajectory]
    crystallized_traits: List[str]
    drifting_traits: List[str]
    volatile_traits: List[str]
    most_changed: str
    most_stable: str
    overall_stability: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "cycle_number": self.cycle_number,
            "crystallized_traits": self.crystallized_traits,
            "drifting_traits": self.drifting_traits,
            "volatile_traits": self.volatile_traits,
            "most_changed": self.most_changed,
            "most_stable": self.most_stable,
            "overall_stability": round(self.overall_stability, 4),
            "trajectories": {
                k: v.to_dict() for k, v in self.trajectories.items()
            },
        }


# ── Trait Evolution Engine ───────────────────────────────────────────────────


class TraitEvolutionEngine:
    """Tracks how kor'tana's traits change over time."""

    def __init__(self) -> None:
        self._trajectories: Dict[str, TraitTrajectory] = {}
        self._snapshots: List[EvolutionSnapshot] = []
        self._max_snapshots: int = 100
        self._max_events_per_trait: int = 50

    def record_cycle(
        self,
        cycle_number: int,
        trait_scores: Dict[str, float],
        previous_scores: Optional[Dict[str, float]] = None,
    ) -> EvolutionSnapshot:
        """Record trait scores for a cycle, updating all trajectories.

        Returns an EvolutionSnapshot summarizing the current state.
        """
        for trait_name, score in trait_scores.items():
            trajectory = self._get_or_create(trait_name)
            old_score = previous_scores.get(trait_name, score) if previous_scores else score

            # Record history
            trajectory.history.append((cycle_number, score))
            if len(trajectory.history) > HISTORY_WINDOW:
                trajectory.history = trajectory.history[-HISTORY_WINDOW:]

            trajectory.current_score = score

            # Compute velocity and stability
            trajectory.velocity = self._compute_velocity(trajectory.history)
            trajectory.stability = self._compute_stability(trajectory.history)

            # Determine status
            trajectory.status = self._determine_status(trajectory)

            # Record evolution event if significant change
            delta = score - old_score
            if abs(delta) > 0.01:
                event = TraitEvolutionEvent(
                    event_id=str(uuid.uuid4()),
                    trait_name=trait_name,
                    cycle_number=cycle_number,
                    old_score=old_score,
                    new_score=score,
                    delta=delta,
                    source="cycle_update",
                    significance=min(1.0, abs(delta) * 10),
                )
                trajectory.events.append(event)
                if len(trajectory.events) > self._max_events_per_trait:
                    trajectory.events = trajectory.events[-self._max_events_per_trait:]

        # Build snapshot
        snapshot = self._build_snapshot(cycle_number)
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots = self._snapshots[-self._max_snapshots:]

        return snapshot

    def record_event(
        self, trait_name: str, cycle_number: int,
        old_score: float, new_score: float, source: str
    ) -> Optional[TraitEvolutionEvent]:
        """Record a specific evolution event with source attribution."""
        trajectory = self._get_or_create(trait_name)
        delta = new_score - old_score
        if abs(delta) < 0.001:
            return None

        event = TraitEvolutionEvent(
            event_id=str(uuid.uuid4()),
            trait_name=trait_name,
            cycle_number=cycle_number,
            old_score=old_score,
            new_score=new_score,
            delta=delta,
            source=source,
            significance=min(1.0, abs(delta) * 10),
        )
        trajectory.events.append(event)
        if len(trajectory.events) > self._max_events_per_trait:
            trajectory.events = trajectory.events[-self._max_events_per_trait:]

        return event

    def _get_or_create(self, trait_name: str) -> TraitTrajectory:
        """Get or create a trajectory for a trait."""
        if trait_name not in self._trajectories:
            self._trajectories[trait_name] = TraitTrajectory(
                trait_name=trait_name,
                current_score=0.5,
            )
        return self._trajectories[trait_name]

    def _compute_velocity(self, history: List[Tuple[int, float]]) -> float:
        """Compute velocity as slope of recent scores."""
        if len(history) < 2:
            return 0.0

        # Use last 10 points for velocity
        recent = history[-10:]
        n = len(recent)
        if n < 2:
            return 0.0

        # Simple linear regression slope
        sum_x = sum(i for i in range(n))
        sum_y = sum(score for _, score in recent)
        sum_xy = sum(i * score for i, (_, score) in enumerate(recent))
        sum_x2 = sum(i * i for i in range(n))

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0

        return (n * sum_xy - sum_x * sum_y) / denominator

    def _compute_stability(self, history: List[Tuple[int, float]]) -> float:
        """Compute stability as inverse of recent variance (0-1)."""
        if len(history) < 3:
            return 0.5  # not enough data

        recent_scores = [score for _, score in history[-15:]]
        mean = sum(recent_scores) / len(recent_scores)
        variance = sum((s - mean) ** 2 for s in recent_scores) / len(recent_scores)

        # Map variance to stability: 0 variance → 1.0 stability
        # Use exponential decay: stability = exp(-k * variance)
        stability = math.exp(-50.0 * variance)
        return max(0.0, min(1.0, stability))

    def _determine_status(self, trajectory: TraitTrajectory) -> TraitStatus:
        """Determine the evolutionary status of a trait."""
        # Check for dormancy
        if (trajectory.current_score < DORMANT_SCORE
                and trajectory.stability > 0.8):
            return TraitStatus.DORMANT

        # Check for crystallization
        if (trajectory.stability >= CRYSTALLIZATION_STABILITY
                and len(trajectory.history) >= CRYSTALLIZATION_MIN_CYCLES):
            if trajectory.crystallized_at is None:
                trajectory.crystallized_at = trajectory.history[-1][0]
            return TraitStatus.CRYSTALLIZED

        # Check for volatility
        if trajectory.stability < VOLATILE_STABILITY:
            return TraitStatus.VOLATILE

        # Check for settling
        if trajectory.stability > 0.7:
            return TraitStatus.SETTLING

        return TraitStatus.DEVELOPING

    def _build_snapshot(self, cycle_number: int) -> EvolutionSnapshot:
        """Build an EvolutionSnapshot from current state."""
        crystallized = []
        drifting = []
        volatile = []
        most_changed = ""
        most_stable = ""
        max_velocity = 0.0
        max_stability = 0.0
        stability_sum = 0.0

        for name, traj in self._trajectories.items():
            if traj.is_crystallized:
                crystallized.append(name)
            if traj.is_drifting:
                drifting.append(name)
            if traj.status == TraitStatus.VOLATILE:
                volatile.append(name)

            if abs(traj.velocity) > abs(max_velocity):
                max_velocity = traj.velocity
                most_changed = name
            if traj.stability > max_stability:
                max_stability = traj.stability
                most_stable = name

            stability_sum += traj.stability

        overall_stability = (
            stability_sum / len(self._trajectories)
            if self._trajectories else 1.0
        )

        return EvolutionSnapshot(
            snapshot_id=str(uuid.uuid4()),
            cycle_number=cycle_number,
            trajectories=dict(self._trajectories),
            crystallized_traits=crystallized,
            drifting_traits=drifting,
            volatile_traits=volatile,
            most_changed=most_changed or "(none)",
            most_stable=most_stable or "(none)",
            overall_stability=overall_stability,
        )

    # ── Query API ────────────────────────────────────────────────────────────

    def get_trajectory(self, trait_name: str) -> Optional[TraitTrajectory]:
        """Get trajectory for a specific trait."""
        return self._trajectories.get(trait_name)

    def get_crystallized(self) -> List[str]:
        """Get all crystallized trait names."""
        return [
            name for name, traj in self._trajectories.items()
            if traj.is_crystallized
        ]

    def get_drifting(self) -> List[str]:
        """Get all drifting trait names."""
        return [
            name for name, traj in self._trajectories.items()
            if traj.is_drifting
        ]

    def get_volatile(self) -> List[str]:
        """Get all volatile trait names."""
        return [
            name for name, traj in self._trajectories.items()
            if traj.status == TraitStatus.VOLATILE
        ]

    def get_latest_snapshot(self) -> Optional[EvolutionSnapshot]:
        """Get the most recent evolution snapshot."""
        return self._snapshots[-1] if self._snapshots else None

    def get_snapshot_history(self, n: int = 10) -> List[EvolutionSnapshot]:
        """Get recent evolution snapshots."""
        return list(reversed(self._snapshots[-n:]))

    def get_trait_history(
        self, trait_name: str, n: int = 20
    ) -> List[Dict[str, Any]]:
        """Get score history for a specific trait."""
        traj = self._trajectories.get(trait_name)
        if not traj:
            return []
        return [
            {"cycle": cycle, "score": round(score, 4)}
            for cycle, score in traj.history[-n:]
        ]

    def get_summary(self) -> Dict[str, Any]:
        """Get a compact summary of trait evolution state."""
        latest = self.get_latest_snapshot()
        return {
            "traits_tracked": len(self._trajectories),
            "snapshots_taken": len(self._snapshots),
            "crystallized_count": len(self.get_crystallized()),
            "crystallized_traits": self.get_crystallized(),
            "drifting_count": len(self.get_drifting()),
            "drifting_traits": self.get_drifting(),
            "volatile_count": len(self.get_volatile()),
            "volatile_traits": self.get_volatile(),
            "overall_stability": (
                round(latest.overall_stability, 4) if latest else 1.0
            ),
            "most_changed": latest.most_changed if latest else "(none)",
            "most_stable": latest.most_stable if latest else "(none)",
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_trait_evolution_engine: Optional[TraitEvolutionEngine] = None


def get_trait_evolution_engine() -> TraitEvolutionEngine:
    """Get or create the singleton TraitEvolutionEngine."""
    global _trait_evolution_engine
    if _trait_evolution_engine is None:
        _trait_evolution_engine = TraitEvolutionEngine()
    return _trait_evolution_engine
