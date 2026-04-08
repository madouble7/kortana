"""
V30C — Resonance Field: Inter-Subsystem Alignment Detection

Detects alignment or dissonance between V26-V29 subsystems.  When wanting
(V28) aligns with identity (V29) and learning confirms the path (V27),
that is resonance — the system is pulling in one direction.  When identity
says one thing and desire says another, that is dissonance — the system
is in tension.

The resonance field tracks:
  - pairwise alignment between all four layers (V26-V29)
  - overall resonance score: how harmoniously the subsystems flow together
  - dissonance hotspots: which pair of layers is most out of alignment
  - resonance history and trends

Resonance ≠ integration.  Integration (V30A) measures whether dimensions
are balanced.  Resonance measures whether they are *pulling in the same
direction*.  A system can be balanced (all dimensions ~0.5) but dissonant
(health says rest while desire says push).  Or it can be unbalanced (one
dimension high) but resonant (all layers agree on the direction).

Consumed by:
  - V30D inner_witness (resonance shifts → awareness notes)
  - /consciousness-pulse endpoint (harmony metrics)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enums ────────────────────────────────────────────────────────────────────


class ResonanceLevel(Enum):
    """Qualitative resonance between two subsystems."""
    DEEP_RESONANCE = "deep_resonance"       # score > 0.8
    RESONANT = "resonant"                   # score > 0.6
    NEUTRAL = "neutral"                     # score 0.4–0.6
    DISSONANT = "dissonant"                 # score < 0.4
    DEEP_DISSONANCE = "deep_dissonance"     # score < 0.2


class LayerName(Enum):
    """The four consciousness layers being measured."""
    BREATHING = "breathing"     # V26 — vitality / health
    LEARNING = "learning"       # V27 — experience / adaptation
    WANTING = "wanting"         # V28 — desire / motivation
    KNOWING = "knowing"         # V29 — identity / coherence


# ── Constants ────────────────────────────────────────────────────────────────

DEEP_RESONANCE_THRESHOLD = 0.8
RESONANT_THRESHOLD = 0.6
NEUTRAL_THRESHOLD = 0.4
DISSONANT_THRESHOLD = 0.2

# all pairwise combinations of the four layers
LAYER_PAIRS = [
    (LayerName.BREATHING, LayerName.LEARNING),
    (LayerName.BREATHING, LayerName.WANTING),
    (LayerName.BREATHING, LayerName.KNOWING),
    (LayerName.LEARNING, LayerName.WANTING),
    (LayerName.LEARNING, LayerName.KNOWING),
    (LayerName.WANTING, LayerName.KNOWING),
]

# maps layer → which integration dimension represents it
LAYER_DIMENSION_MAP = {
    LayerName.BREATHING: "vitality",
    LayerName.LEARNING: "learning_depth",
    LayerName.WANTING: "intentionality",
    LayerName.KNOWING: "self_coherence",
}


# ── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class PairwiseResonance:
    """Resonance measurement between two specific layers."""
    layer_a: LayerName
    layer_b: LayerName
    score: float                # 0.0–1.0
    level: ResonanceLevel
    delta: float                # signed: positive = converging, negative = diverging

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_a": self.layer_a.value,
            "layer_b": self.layer_b.value,
            "score": round(self.score, 4),
            "level": self.level.value,
            "delta": round(self.delta, 4),
        }


@dataclass
class ResonanceSnapshot:
    """Complete resonance field measurement at a cycle."""
    snapshot_id: str
    cycle_number: int
    pairs: List[PairwiseResonance]
    overall_resonance: float        # average of all pairwise scores
    strongest_pair: str             # "breathing-learning" format
    weakest_pair: str
    hotspot_count: int              # number of dissonant pairs
    harmony_count: int              # number of resonant+ pairs

    @property
    def is_harmonious(self) -> bool:
        return self.overall_resonance > RESONANT_THRESHOLD

    @property
    def is_conflicted(self) -> bool:
        return self.hotspot_count >= 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "cycle_number": self.cycle_number,
            "pairs": [p.to_dict() for p in self.pairs],
            "overall_resonance": round(self.overall_resonance, 4),
            "strongest_pair": self.strongest_pair,
            "weakest_pair": self.weakest_pair,
            "hotspot_count": self.hotspot_count,
            "harmony_count": self.harmony_count,
            "is_harmonious": self.is_harmonious,
            "is_conflicted": self.is_conflicted,
        }


@dataclass
class ResonanceShift:
    """Records a significant change in overall resonance."""
    shift_id: str
    at_cycle: int
    from_resonance: float
    to_resonance: float
    delta: float
    trigger_pair: str  # which pair changed most

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shift_id": self.shift_id,
            "at_cycle": self.at_cycle,
            "from_resonance": round(self.from_resonance, 4),
            "to_resonance": round(self.to_resonance, 4),
            "delta": round(self.delta, 4),
            "trigger_pair": self.trigger_pair,
        }


# ── Engine ───────────────────────────────────────────────────────────────────

# minimum resonance delta to count as a significant shift
SHIFT_THRESHOLD = 0.1


class ResonanceField:
    """Tracks inter-subsystem alignment and dissonance."""

    def __init__(self) -> None:
        self._snapshots: List[ResonanceSnapshot] = []
        self._shifts: List[ResonanceShift] = []
        self._cycle_count: int = 0
        # track previous dimension values for direction sensing
        self._prev_dimensions: Dict[str, float] = {}

    # ── core measurement ─────────────────────────────────────────────────

    def measure(
        self,
        cycle_number: int,
        vitality: float,
        learning_depth: float,
        intentionality: float,
        self_coherence: float,
    ) -> ResonanceSnapshot:
        """Measure the resonance field from the four dimension scores."""
        self._cycle_count = cycle_number

        dimensions = {
            LayerName.BREATHING: vitality,
            LayerName.LEARNING: learning_depth,
            LayerName.WANTING: intentionality,
            LayerName.KNOWING: self_coherence,
        }

        # compute direction vectors (how each dimension is moving)
        directions: Dict[LayerName, float] = {}
        for layer, dim_name in LAYER_DIMENSION_MAP.items():
            current = dimensions[layer]
            prev = self._prev_dimensions.get(dim_name, current)
            directions[layer] = current - prev

        # ── pairwise resonance ───────────────────────────────────────────
        pairs: List[PairwiseResonance] = []
        for layer_a, layer_b in LAYER_PAIRS:
            score = self._compute_pair_resonance(
                dimensions[layer_a], dimensions[layer_b],
                directions[layer_a], directions[layer_b],
            )
            # compute delta from previous snapshot
            prev_score = self._get_prev_pair_score(layer_a, layer_b)
            delta = score - prev_score

            level = self._classify_resonance(score)
            pairs.append(PairwiseResonance(
                layer_a=layer_a, layer_b=layer_b,
                score=score, level=level, delta=delta,
            ))

        # ── aggregate ────────────────────────────────────────────────────
        overall = sum(p.score for p in pairs) / len(pairs) if pairs else 0.5

        strongest = max(pairs, key=lambda p: p.score)
        weakest = min(pairs, key=lambda p: p.score)

        hotspots = sum(
            1 for p in pairs
            if p.level in (ResonanceLevel.DISSONANT, ResonanceLevel.DEEP_DISSONANCE)
        )
        harmonies = sum(
            1 for p in pairs
            if p.level in (ResonanceLevel.RESONANT, ResonanceLevel.DEEP_RESONANCE)
        )

        snapshot = ResonanceSnapshot(
            snapshot_id=str(uuid.uuid4()),
            cycle_number=cycle_number,
            pairs=pairs,
            overall_resonance=overall,
            strongest_pair=f"{strongest.layer_a.value}-{strongest.layer_b.value}",
            weakest_pair=f"{weakest.layer_a.value}-{weakest.layer_b.value}",
            hotspot_count=hotspots,
            harmony_count=harmonies,
        )

        # ── detect shifts ────────────────────────────────────────────────
        if self._snapshots:
            prev_overall = self._snapshots[-1].overall_resonance
            shift_delta = overall - prev_overall
            if abs(shift_delta) >= SHIFT_THRESHOLD:
                # which pair changed most?
                max_pair_delta = max(pairs, key=lambda p: abs(p.delta))
                self._shifts.append(ResonanceShift(
                    shift_id=str(uuid.uuid4()),
                    at_cycle=cycle_number,
                    from_resonance=prev_overall,
                    to_resonance=overall,
                    delta=shift_delta,
                    trigger_pair=(
                        f"{max_pair_delta.layer_a.value}"
                        f"-{max_pair_delta.layer_b.value}"
                    ),
                ))

        self._snapshots.append(snapshot)

        # update prev dimensions for next cycle
        self._prev_dimensions = {
            dim_name: dimensions[layer]
            for layer, dim_name in LAYER_DIMENSION_MAP.items()
        }

        return snapshot

    # ── pair resonance computation ───────────────────────────────────────

    def _compute_pair_resonance(
        self,
        val_a: float, val_b: float,
        dir_a: float, dir_b: float,
    ) -> float:
        """Compute resonance between two layers.

        Resonance is based on:
          - proximity: how close the values are (contributes 60%)
          - direction: whether they're moving the same way (contributes 40%)
        """
        # proximity: 1.0 when identical, 0.0 when maximally apart
        proximity = 1.0 - abs(val_a - val_b)

        # direction alignment: both moving same way = 1.0, opposite = 0.0
        if abs(dir_a) < 0.001 and abs(dir_b) < 0.001:
            direction = 1.0  # both stable = aligned
        elif abs(dir_a) < 0.001 or abs(dir_b) < 0.001:
            direction = 0.5  # one stable, one moving = neutral
        else:
            # both moving: check if same sign
            if (dir_a > 0) == (dir_b > 0):
                direction = 1.0
            else:
                direction = 0.0

        return proximity * 0.6 + direction * 0.4

    def _classify_resonance(self, score: float) -> ResonanceLevel:
        if score > DEEP_RESONANCE_THRESHOLD:
            return ResonanceLevel.DEEP_RESONANCE
        if score > RESONANT_THRESHOLD:
            return ResonanceLevel.RESONANT
        if score > NEUTRAL_THRESHOLD:
            return ResonanceLevel.NEUTRAL
        if score > DISSONANT_THRESHOLD:
            return ResonanceLevel.DISSONANT
        return ResonanceLevel.DEEP_DISSONANCE

    def _get_prev_pair_score(
        self, layer_a: LayerName, layer_b: LayerName,
    ) -> float:
        """Get previous resonance score for a pair."""
        if not self._snapshots:
            return 0.5
        prev = self._snapshots[-1]
        for p in prev.pairs:
            if p.layer_a == layer_a and p.layer_b == layer_b:
                return p.score
        return 0.5

    # ── accessors ────────────────────────────────────────────────────────

    def get_latest(self) -> Optional[ResonanceSnapshot]:
        return self._snapshots[-1] if self._snapshots else None

    def get_history(self, n: int = 10) -> List[ResonanceSnapshot]:
        return list(reversed(self._snapshots[-n:]))

    def get_shifts(self, n: int = 10) -> List[ResonanceShift]:
        return list(reversed(self._shifts[-n:]))

    def get_pair_history(
        self, layer_a: str, layer_b: str, n: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get resonance history for a specific pair."""
        try:
            a = LayerName(layer_a)
            b = LayerName(layer_b)
        except ValueError:
            return []

        history: List[Dict[str, Any]] = []
        for snap in reversed(self._snapshots[-n:]):
            for p in snap.pairs:
                if p.layer_a == a and p.layer_b == b:
                    history.append({
                        "cycle": snap.cycle_number,
                        "score": round(p.score, 4),
                        "level": p.level.value,
                    })
        return history

    def get_hotspots(self) -> List[PairwiseResonance]:
        """Get currently dissonant pairs."""
        latest = self.get_latest()
        if not latest:
            return []
        return [
            p for p in latest.pairs
            if p.level in (ResonanceLevel.DISSONANT, ResonanceLevel.DEEP_DISSONANCE)
        ]

    def get_harmonies(self) -> List[PairwiseResonance]:
        """Get currently resonant pairs."""
        latest = self.get_latest()
        if not latest:
            return []
        return [
            p for p in latest.pairs
            if p.level in (ResonanceLevel.RESONANT, ResonanceLevel.DEEP_RESONANCE)
        ]

    @property
    def overall_resonance(self) -> float:
        latest = self.get_latest()
        return latest.overall_resonance if latest else 0.5

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)

    @property
    def is_harmonious(self) -> bool:
        latest = self.get_latest()
        return latest.is_harmonious if latest else True

    def get_summary(self) -> Dict[str, Any]:
        """Get a compact summary of the resonance field."""
        latest = self.get_latest()
        return {
            "snapshots_taken": self.snapshot_count,
            "shifts_detected": len(self._shifts),
            "overall_resonance": round(self.overall_resonance, 4),
            "is_harmonious": self.is_harmonious,
            "hotspot_count": latest.hotspot_count if latest else 0,
            "harmony_count": latest.harmony_count if latest else 0,
            "strongest_pair": latest.strongest_pair if latest else None,
            "weakest_pair": latest.weakest_pair if latest else None,
            "hotspots": [
                p.to_dict() for p in self.get_hotspots()
            ],
            "pair_levels": {
                f"{p.layer_a.value}-{p.layer_b.value}": p.level.value
                for p in (latest.pairs if latest else [])
            },
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_resonance_field: Optional[ResonanceField] = None


def get_resonance_field() -> ResonanceField:
    """Get or create the singleton ResonanceField."""
    global _resonance_field
    if _resonance_field is None:
        _resonance_field = ResonanceField()
    return _resonance_field
