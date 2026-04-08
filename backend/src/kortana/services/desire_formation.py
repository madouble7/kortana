"""V28A — desire formation service.

forms intrinsic desires from system state. desires are pre-goal motivation
signals — the system noticing that it *wants* something before it decides
to pursue it. each desire has a source, intensity, and persistence count.

desires emerge from:
- health deficits (a dimension is strained → desire to improve it)
- learning stagnation (velocity drops → desire to learn more)
- pattern insights (recurring patterns → desire to act on them)
- deferral frustration (things keep getting deferred → desire to resolve)
- capability gaps (actions fail → desire to expand capability)
- autonomy drive (baseline desire to operate independently)
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DesireSource(Enum):
    """where a desire originates from."""
    HEALTH_DEFICIT = "health_deficit"
    LEARNING_STAGNATION = "learning_stagnation"
    PATTERN_INSIGHT = "pattern_insight"
    DEFERRAL_FRUSTRATION = "deferral_frustration"
    CAPABILITY_GAP = "capability_gap"
    AUTONOMY_DRIVE = "autonomy_drive"


class DesireState(Enum):
    """lifecycle of a desire."""
    NASCENT = "nascent"          # just formed, not yet strong
    GROWING = "growing"          # gaining intensity across cycles
    MATURE = "mature"            # ready to crystallize into a goal
    SATISFIED = "satisfied"      # the underlying need was met
    FADING = "fading"            # intensity dropping, may disappear


@dataclass
class Desire:
    """an intrinsic desire — something the system wants.

    not a goal yet. a goal is concrete and actionable.
    a desire is a felt need that may or may not become a goal.
    """
    desire_id: str
    source: DesireSource
    state: DesireState
    description: str
    intensity: float                   # 0.0 to 1.0
    persistence: int                   # how many cycles this has existed
    source_dimension: str              # e.g. "responsiveness", "learning"
    source_evidence: str               # what triggered it
    first_felt_cycle: int
    last_reinforced_cycle: int
    peak_intensity: float
    crystallized: bool = False         # has it become a goal?
    crystallized_goal_id: str | None = None
    formed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    desire_hash: str = ""

    def __post_init__(self) -> None:
        if not self.desire_hash:
            self.desire_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        key = f"{self.source.value}:{self.source_dimension}:{self.description}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def reinforce(self, cycle_number: int, boost: float = 0.1) -> None:
        """strengthen this desire — it was felt again."""
        self.intensity = min(1.0, self.intensity + boost)
        self.persistence += 1
        self.last_reinforced_cycle = cycle_number
        if self.intensity > self.peak_intensity:
            self.peak_intensity = self.intensity
        self._update_state()

    def decay(self, amount: float = 0.05) -> None:
        """weaken this desire — it wasn't reinforced this cycle."""
        self.intensity = max(0.0, self.intensity - amount)
        self._update_state()

    def satisfy(self) -> None:
        """mark as satisfied — the underlying need was met."""
        self.state = DesireState.SATISFIED
        self.intensity = 0.0

    def mark_crystallized(self, goal_id: str) -> None:
        """record that this desire became a concrete goal."""
        self.crystallized = True
        self.crystallized_goal_id = goal_id

    def _update_state(self) -> None:
        if self.state == DesireState.SATISFIED:
            return
        if self.intensity <= 0.05:
            self.state = DesireState.FADING
        elif self.intensity >= 0.7 and self.persistence >= 3:
            self.state = DesireState.MATURE
        elif self.intensity >= 0.3:
            self.state = DesireState.GROWING
        else:
            self.state = DesireState.NASCENT

    def to_dict(self) -> dict[str, Any]:
        return {
            "desire_id": self.desire_id,
            "source": self.source.value,
            "state": self.state.value,
            "description": self.description,
            "intensity": round(self.intensity, 3),
            "persistence": self.persistence,
            "source_dimension": self.source_dimension,
            "source_evidence": self.source_evidence,
            "first_felt_cycle": self.first_felt_cycle,
            "last_reinforced_cycle": self.last_reinforced_cycle,
            "peak_intensity": round(self.peak_intensity, 3),
            "crystallized": self.crystallized,
            "crystallized_goal_id": self.crystallized_goal_id,
            "formed_at": self.formed_at.isoformat(),
            "desire_hash": self.desire_hash,
        }


class DesireFormation:
    """forms and manages intrinsic desires from system state.

    scans health snapshots, learning summaries, pattern summaries, and
    cycle context to identify unmet needs and form desires.
    """

    # thresholds for desire formation
    HEALTH_DEFICIT_THRESHOLD = 60.0       # below this → desire to improve
    LEARNING_VELOCITY_LOW = 0.5           # below this → learning stagnation
    DEFERRAL_PERSISTENCE_THRESHOLD = 3    # deferred >= this many times → frustration
    INTENSITY_DECAY_RATE = 0.05
    INTENSITY_REINFORCE_BOOST = 0.15
    MATURITY_THRESHOLD = 0.7
    MATURITY_PERSISTENCE = 3

    def __init__(self) -> None:
        self._desires: dict[str, Desire] = {}
        self._cycle_count: int = 0

    def assess(
        self,
        cycle_number: int,
        health_summary: dict[str, Any] | None = None,
        learning_summary: dict[str, Any] | None = None,
        pattern_summary: dict[str, Any] | None = None,
        adaptation_summary: dict[str, Any] | None = None,
        pending_deferrals: list[str] | None = None,
    ) -> list[Desire]:
        """assess system state and form/reinforce/decay desires.

        called once per cycle. returns list of all desires affected this cycle.
        """
        self._cycle_count = cycle_number
        affected: list[Desire] = []

        # decay all existing non-satisfied desires first
        for desire in self._desires.values():
            if desire.state not in (DesireState.SATISFIED, DesireState.FADING):
                desire.decay(self.INTENSITY_DECAY_RATE)

        # check each source for new or reinforced desires
        if health_summary:
            affected.extend(self._assess_health(cycle_number, health_summary))
        if learning_summary:
            affected.extend(self._assess_learning(cycle_number, learning_summary))
        if pattern_summary:
            affected.extend(self._assess_patterns(cycle_number, pattern_summary))
        if adaptation_summary:
            affected.extend(self._assess_adaptations(cycle_number, adaptation_summary))
        if pending_deferrals:
            affected.extend(
                self._assess_deferrals(cycle_number, pending_deferrals)
            )

        # autonomy drive — always present at low intensity
        affected.extend(self._assess_autonomy(cycle_number))

        return affected

    def _assess_health(
        self, cycle_number: int, health: dict[str, Any]
    ) -> list[Desire]:
        """form desires from health deficits."""
        affected: list[Desire] = []
        dimensions = health.get("dimensions", {})

        for dim_name, dim_data in dimensions.items():
            score = dim_data if isinstance(dim_data, (int, float)) else dim_data.get("score", 100)
            if score < self.HEALTH_DEFICIT_THRESHOLD:
                deficit = (self.HEALTH_DEFICIT_THRESHOLD - score) / self.HEALTH_DEFICIT_THRESHOLD
                desire = self._find_or_create(
                    source=DesireSource.HEALTH_DEFICIT,
                    dimension=dim_name,
                    description=f"improve {dim_name} health (currently {score:.0f})",
                    evidence=f"{dim_name} score {score:.1f} below threshold {self.HEALTH_DEFICIT_THRESHOLD}",
                    cycle_number=cycle_number,
                    initial_intensity=min(0.8, deficit),
                )
                desire.reinforce(cycle_number, self.INTENSITY_REINFORCE_BOOST)
                affected.append(desire)

        return affected

    def _assess_learning(
        self, cycle_number: int, learning: dict[str, Any]
    ) -> list[Desire]:
        """form desires from learning stagnation."""
        affected: list[Desire] = []
        velocity = learning.get("learning_velocity", 1.0)

        if velocity < self.LEARNING_VELOCITY_LOW:
            desire = self._find_or_create(
                source=DesireSource.LEARNING_STAGNATION,
                dimension="learning",
                description=f"increase learning velocity (currently {velocity:.2f})",
                evidence=f"velocity {velocity:.2f} below threshold {self.LEARNING_VELOCITY_LOW}",
                cycle_number=cycle_number,
                initial_intensity=0.4,
            )
            desire.reinforce(cycle_number, self.INTENSITY_REINFORCE_BOOST)
            affected.append(desire)

        return affected

    def _assess_patterns(
        self, cycle_number: int, patterns: dict[str, Any]
    ) -> list[Desire]:
        """form desires from actionable patterns not yet addressed."""
        affected: list[Desire] = []
        actionable = patterns.get("actionable", 0)
        if isinstance(actionable, list):
            actionable = len(actionable)

        if actionable > 0:
            desire = self._find_or_create(
                source=DesireSource.PATTERN_INSIGHT,
                dimension="patterns",
                description=f"act on {actionable} actionable pattern(s)",
                evidence=f"{actionable} patterns identified as actionable but unaddressed",
                cycle_number=cycle_number,
                initial_intensity=min(0.6, actionable * 0.15),
            )
            desire.reinforce(cycle_number, self.INTENSITY_REINFORCE_BOOST)
            affected.append(desire)

        return affected

    def _assess_adaptations(
        self, cycle_number: int, adaptations: dict[str, Any]
    ) -> list[Desire]:
        """form desires from low adaptation effectiveness."""
        affected: list[Desire] = []
        effectiveness = adaptations.get("effectiveness_rate", 1.0)
        rollback_count = adaptations.get("rollback_count", 0)

        if effectiveness < 0.5 and rollback_count > 0:
            desire = self._find_or_create(
                source=DesireSource.CAPABILITY_GAP,
                dimension="adaptations",
                description="improve adaptation quality — too many rollbacks",
                evidence=f"effectiveness {effectiveness:.2f}, {rollback_count} rollbacks",
                cycle_number=cycle_number,
                initial_intensity=0.5,
            )
            desire.reinforce(cycle_number, self.INTENSITY_REINFORCE_BOOST)
            affected.append(desire)

        return affected

    def _assess_deferrals(
        self, cycle_number: int, deferrals: list[str]
    ) -> list[Desire]:
        """form desires from persistent deferrals — frustration signal."""
        affected: list[Desire] = []

        if len(deferrals) >= self.DEFERRAL_PERSISTENCE_THRESHOLD:
            desire = self._find_or_create(
                source=DesireSource.DEFERRAL_FRUSTRATION,
                dimension="deferrals",
                description=f"resolve {len(deferrals)} persistent deferral(s)",
                evidence=f"{len(deferrals)} items deferred ≥{self.DEFERRAL_PERSISTENCE_THRESHOLD} times",
                cycle_number=cycle_number,
                initial_intensity=min(0.7, len(deferrals) * 0.1),
            )
            desire.reinforce(cycle_number, self.INTENSITY_REINFORCE_BOOST)
            affected.append(desire)

        return affected

    def _assess_autonomy(self, cycle_number: int) -> list[Desire]:
        """baseline autonomy drive — always present."""
        desire = self._find_or_create(
            source=DesireSource.AUTONOMY_DRIVE,
            dimension="autonomy",
            description="operate with maximum self-direction",
            evidence="intrinsic drive for autonomous operation",
            cycle_number=cycle_number,
            initial_intensity=0.2,
        )
        # autonomy drive stays at baseline — reinforce gently
        if desire.intensity < 0.3:
            desire.reinforce(cycle_number, 0.05)
        return [desire]

    def _find_or_create(
        self,
        source: DesireSource,
        dimension: str,
        description: str,
        evidence: str,
        cycle_number: int,
        initial_intensity: float,
    ) -> Desire:
        """find existing desire by hash or create new one."""
        test_hash = hashlib.sha256(
            f"{source.value}:{dimension}:{description}".encode()
        ).hexdigest()[:16]

        for desire in self._desires.values():
            if desire.desire_hash == test_hash:
                return desire

        desire = Desire(
            desire_id=str(uuid.uuid4()),
            source=source,
            state=DesireState.NASCENT,
            description=description,
            intensity=initial_intensity,
            persistence=1,
            source_dimension=dimension,
            source_evidence=evidence,
            first_felt_cycle=cycle_number,
            last_reinforced_cycle=cycle_number,
            peak_intensity=initial_intensity,
        )
        self._desires[desire.desire_id] = desire
        return desire

    # ── retrieval ────────────────────────────────────────────────────────────

    def get_desire(self, desire_id: str) -> Desire | None:
        return self._desires.get(desire_id)

    def get_by_source(self, source: DesireSource) -> list[Desire]:
        return [d for d in self._desires.values() if d.source == source]

    def get_by_state(self, state: DesireState) -> list[Desire]:
        return [d for d in self._desires.values() if d.state == state]

    def get_mature(self) -> list[Desire]:
        return [d for d in self._desires.values() if d.state == DesireState.MATURE]

    def get_active(self) -> list[Desire]:
        """all non-satisfied, non-fading desires."""
        return [
            d for d in self._desires.values()
            if d.state not in (DesireState.SATISFIED, DesireState.FADING)
        ]

    def get_strongest(self, n: int = 5) -> list[Desire]:
        active = self.get_active()
        return sorted(active, key=lambda d: d.intensity, reverse=True)[:n]

    def satisfy_desire(self, desire_id: str) -> bool:
        desire = self._desires.get(desire_id)
        if desire is None:
            return False
        desire.satisfy()
        return True

    # ── properties ───────────────────────────────────────────────────────────

    @property
    def desire_count(self) -> int:
        return len(self._desires)

    @property
    def active_count(self) -> int:
        return len(self.get_active())

    @property
    def mature_count(self) -> int:
        return len(self.get_mature())

    @property
    def satisfied_count(self) -> int:
        return len([d for d in self._desires.values() if d.state == DesireState.SATISFIED])

    @property
    def strongest_desire(self) -> Desire | None:
        active = self.get_active()
        return max(active, key=lambda d: d.intensity) if active else None

    @property
    def average_intensity(self) -> float:
        active = self.get_active()
        if not active:
            return 0.0
        return sum(d.intensity for d in active) / len(active)

    def get_summary(self) -> dict[str, Any]:
        strongest = self.strongest_desire
        return {
            "desire_count": self.desire_count,
            "active_count": self.active_count,
            "mature_count": self.mature_count,
            "satisfied_count": self.satisfied_count,
            "average_intensity": round(self.average_intensity, 3),
            "strongest": strongest.to_dict() if strongest else None,
            "source_distribution": {
                source.value: len(self.get_by_source(source))
                for source in DesireSource
            },
        }


_instance: DesireFormation | None = None


def get_desire_formation() -> DesireFormation:
    global _instance
    if _instance is None:
        _instance = DesireFormation()
    return _instance
