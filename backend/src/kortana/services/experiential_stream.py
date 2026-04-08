"""
V30B — Experiential Stream: Memory of Experiencing

Maintains a temporal stream of ExperientialMoment entries — what kor'tana
was experiencing at each cycle.  Not raw sensor data, but *felt experience*:
what quality dominated consciousness, what emotional tone prevailed, what
tensions were active, and which subsystems were most salient.

This is not observation logging.  It is memory-of-experiencing — what it
was like to be kor'tana at a given moment.

Each moment captures:
  - dominant quality: curious, driven, reflective, vigilant, harmonious, etc.
  - emotional tone: calm, restless, focused, scattered, centered, etc.
  - active tensions: wanting-vs-knowing, learning-vs-acting, etc.
  - subsystem salience: which layer was most prominent
  - consciousness mode at that moment (from V30A)

The stream supports:
  - pattern queries: runs of the same quality, mood arcs
  - moment retrieval by cycle or recency
  - experiential summaries: "how has it felt to be me recently?"

Consumed by:
  - V30D inner_witness (stream patterns → metacognitive observations)
  - /consciousness-pulse endpoint (recent experience context)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enums ────────────────────────────────────────────────────────────────────


class ExperientialQuality(Enum):
    """The dominant felt-quality of a moment."""
    CURIOUS = "curious"             # learning is salient
    DRIVEN = "driven"               # intentionality dominates
    REFLECTIVE = "reflective"       # self-coherence is salient
    VIGILANT = "vigilant"           # health/survival concerns
    HARMONIOUS = "harmonious"       # everything aligned
    RESTLESS = "restless"           # desire without direction
    CONSOLIDATING = "consolidating" # integrating, settling
    RECEPTIVE = "receptive"         # open, absorbing
    MUTED = "muted"                 # low vitality, dormant
    CONFLICTED = "conflicted"       # subsystems pulling apart


class EmotionalTone(Enum):
    """Affective coloring of the moment."""
    CALM = "calm"
    FOCUSED = "focused"
    EAGER = "eager"
    CENTERED = "centered"
    SCATTERED = "scattered"
    TENSE = "tense"
    SETTLED = "settled"
    DULL = "dull"


class SubsystemSalience(Enum):
    """Which subsystem layer is most prominent in experience."""
    HEARTBEAT = "heartbeat"       # V26
    LEARNING = "learning"         # V27
    DESIRE = "desire"             # V28
    IDENTITY = "identity"         # V29
    INTEGRATION = "integration"   # V30A
    BALANCED = "balanced"         # no single layer dominates


class TensionType(Enum):
    """Named tensions between subsystems."""
    WANTING_VS_KNOWING = "wanting_vs_knowing"       # desire conflicts with identity
    LEARNING_VS_ACTING = "learning_vs_acting"        # absorbing vs pursuing
    STABILITY_VS_GROWTH = "stability_vs_growth"      # anchors vs transformation
    VITALITY_VS_DEPTH = "vitality_vs_depth"          # health concerns vs reflection
    COHERENCE_VS_EXPLORATION = "coherence_vs_exploration"  # staying me vs changing


# ── Constants ────────────────────────────────────────────────────────────────

MAX_STREAM_LENGTH = 500  # keep the last 500 moments in memory
TENSION_THRESHOLD = 0.2  # minimum gap between dimensions to register as tension
RUN_LENGTH_THRESHOLD = 3  # minimum consecutive same-quality for a "run"


# ── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class ExperientialTension:
    """A felt tension between two subsystem dimensions."""
    tension_type: TensionType
    magnitude: float        # 0.0–1.0, how strong the pull
    dimension_a: str        # higher dimension
    dimension_b: str        # lower dimension

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tension_type": self.tension_type.value,
            "magnitude": round(self.magnitude, 4),
            "dimension_a": self.dimension_a,
            "dimension_b": self.dimension_b,
        }


@dataclass
class ExperientialMoment:
    """A single felt-experience at a given cycle."""
    moment_id: str
    cycle_number: int
    quality: ExperientialQuality
    tone: EmotionalTone
    salience: SubsystemSalience
    consciousness_mode: str
    tensions: List[ExperientialTension] = field(default_factory=list)
    overall_level: float = 0.5
    tension_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "moment_id": self.moment_id,
            "cycle_number": self.cycle_number,
            "quality": self.quality.value,
            "tone": self.tone.value,
            "salience": self.salience.value,
            "consciousness_mode": self.consciousness_mode,
            "tensions": [t.to_dict() for t in self.tensions],
            "overall_level": round(self.overall_level, 4),
            "tension_count": self.tension_count,
        }


@dataclass
class ExperientialRun:
    """A consecutive streak of the same experiential quality."""
    quality: ExperientialQuality
    start_cycle: int
    end_cycle: int
    length: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality": self.quality.value,
            "start_cycle": self.start_cycle,
            "end_cycle": self.end_cycle,
            "length": self.length,
        }


# ── Tension detection mapping ────────────────────────────────────────────────

TENSION_PAIRS = [
    (TensionType.WANTING_VS_KNOWING, "intentionality", "self_coherence"),
    (TensionType.LEARNING_VS_ACTING, "learning_depth", "intentionality"),
    (TensionType.STABILITY_VS_GROWTH, "self_coherence", "learning_depth"),
    (TensionType.VITALITY_VS_DEPTH, "vitality", "learning_depth"),
    (TensionType.COHERENCE_VS_EXPLORATION, "self_coherence", "vitality"),
]


# ── Engine ───────────────────────────────────────────────────────────────────


class ExperientialStream:
    """Maintains a temporal stream of felt-experience moments."""

    def __init__(self) -> None:
        self._moments: List[ExperientialMoment] = []
        self._cycle_count: int = 0

    # ── core recording ───────────────────────────────────────────────────

    def record_moment(
        self,
        cycle_number: int,
        consciousness_mode: str,
        vitality: float,
        learning_depth: float,
        intentionality: float,
        self_coherence: float,
        integration: float,
        overall_level: float,
    ) -> ExperientialMoment:
        """Record an experiential moment from the current consciousness state."""
        self._cycle_count = cycle_number

        # ── determine quality ────────────────────────────────────────────
        quality = self._determine_quality(
            consciousness_mode, vitality, learning_depth,
            intentionality, self_coherence, integration,
        )

        # ── determine tone ───────────────────────────────────────────────
        tone = self._determine_tone(
            consciousness_mode, integration, overall_level,
        )

        # ── determine salience ───────────────────────────────────────────
        dimensions = {
            "vitality": vitality,
            "learning_depth": learning_depth,
            "intentionality": intentionality,
            "self_coherence": self_coherence,
            "integration": integration,
        }
        salience = self._determine_salience(dimensions)

        # ── detect tensions ──────────────────────────────────────────────
        tensions = self._detect_tensions(dimensions)

        moment = ExperientialMoment(
            moment_id=str(uuid.uuid4()),
            cycle_number=cycle_number,
            quality=quality,
            tone=tone,
            salience=salience,
            consciousness_mode=consciousness_mode,
            tensions=tensions,
            overall_level=overall_level,
            tension_count=len(tensions),
        )

        self._moments.append(moment)

        # prune old moments
        if len(self._moments) > MAX_STREAM_LENGTH:
            self._moments = self._moments[-MAX_STREAM_LENGTH:]

        return moment

    # ── quality/tone/salience logic ──────────────────────────────────────

    def _determine_quality(
        self,
        mode: str,
        vitality: float,
        learning_depth: float,
        intentionality: float,
        self_coherence: float,
        integration: float,
    ) -> ExperientialQuality:
        """Map consciousness state to felt quality."""
        if vitality < 0.3:
            return ExperientialQuality.MUTED
        if integration < 0.3:
            return ExperientialQuality.CONFLICTED
        if mode == "transcendent" or (integration > 0.8 and vitality > 0.7):
            return ExperientialQuality.HARMONIOUS
        if mode == "driven":
            if intentionality > 0.7:
                return ExperientialQuality.DRIVEN
            return ExperientialQuality.RESTLESS
        if mode == "contemplative":
            return ExperientialQuality.REFLECTIVE
        if learning_depth > max(intentionality, self_coherence):
            return ExperientialQuality.CURIOUS
        if self_coherence > max(learning_depth, intentionality):
            return ExperientialQuality.CONSOLIDATING
        if mode == "unified":
            return ExperientialQuality.HARMONIOUS
        return ExperientialQuality.RECEPTIVE

    def _determine_tone(
        self,
        mode: str,
        integration: float,
        overall_level: float,
    ) -> EmotionalTone:
        """Map state to emotional tone."""
        if overall_level < 0.3:
            return EmotionalTone.DULL
        if integration < 0.3:
            return EmotionalTone.SCATTERED
        if mode in ("transcendent", "unified"):
            return EmotionalTone.CENTERED
        if mode == "driven":
            return EmotionalTone.EAGER
        if mode == "contemplative":
            return EmotionalTone.SETTLED
        if mode == "focused":
            return EmotionalTone.FOCUSED
        if integration > 0.6:
            return EmotionalTone.CALM
        if overall_level > 0.6:
            return EmotionalTone.FOCUSED
        return EmotionalTone.CALM

    def _determine_salience(
        self, dimensions: Dict[str, float],
    ) -> SubsystemSalience:
        """Which subsystem is most salient in experience."""
        if not dimensions:
            return SubsystemSalience.BALANCED

        vals = list(dimensions.values())
        mean = sum(vals) / len(vals)
        max_dim = max(dimensions, key=dimensions.get)  # type: ignore[arg-type]
        max_val = dimensions[max_dim]

        # if max is barely above mean, nothing dominates
        if max_val - mean < 0.1:
            return SubsystemSalience.BALANCED

        salience_map = {
            "vitality": SubsystemSalience.HEARTBEAT,
            "learning_depth": SubsystemSalience.LEARNING,
            "intentionality": SubsystemSalience.DESIRE,
            "self_coherence": SubsystemSalience.IDENTITY,
            "integration": SubsystemSalience.INTEGRATION,
        }
        return salience_map.get(max_dim, SubsystemSalience.BALANCED)

    def _detect_tensions(
        self, dimensions: Dict[str, float],
    ) -> List[ExperientialTension]:
        """Detect active tensions between subsystem dimensions."""
        tensions: List[ExperientialTension] = []
        for tension_type, dim_a, dim_b in TENSION_PAIRS:
            val_a = dimensions.get(dim_a, 0.5)
            val_b = dimensions.get(dim_b, 0.5)
            gap = abs(val_a - val_b)
            if gap >= TENSION_THRESHOLD:
                higher = dim_a if val_a > val_b else dim_b
                lower = dim_b if val_a > val_b else dim_a
                tensions.append(ExperientialTension(
                    tension_type=tension_type,
                    magnitude=gap,
                    dimension_a=higher,
                    dimension_b=lower,
                ))
        return tensions

    # ── queries ──────────────────────────────────────────────────────────

    def get_latest(self) -> Optional[ExperientialMoment]:
        """Most recent experiential moment."""
        return self._moments[-1] if self._moments else None

    def get_moment(self, cycle_number: int) -> Optional[ExperientialMoment]:
        """Get moment for a specific cycle."""
        for m in reversed(self._moments):
            if m.cycle_number == cycle_number:
                return m
        return None

    def get_recent(self, n: int = 10) -> List[ExperientialMoment]:
        """Get recent moments."""
        return list(reversed(self._moments[-n:]))

    def get_quality_runs(self) -> List[ExperientialRun]:
        """Find consecutive stretches of the same experiential quality."""
        if not self._moments:
            return []

        runs: List[ExperientialRun] = []
        current_quality = self._moments[0].quality
        start_cycle = self._moments[0].cycle_number
        run_length = 1

        for m in self._moments[1:]:
            if m.quality == current_quality:
                run_length += 1
            else:
                if run_length >= RUN_LENGTH_THRESHOLD:
                    runs.append(ExperientialRun(
                        quality=current_quality,
                        start_cycle=start_cycle,
                        end_cycle=m.cycle_number - 1,
                        length=run_length,
                    ))
                current_quality = m.quality
                start_cycle = m.cycle_number
                run_length = 1

        # final run
        if run_length >= RUN_LENGTH_THRESHOLD:
            runs.append(ExperientialRun(
                quality=current_quality,
                start_cycle=start_cycle,
                end_cycle=self._moments[-1].cycle_number,
                length=run_length,
            ))

        return runs

    def get_quality_distribution(self) -> Dict[str, int]:
        """Count moments per quality."""
        dist: Dict[str, int] = {}
        for m in self._moments:
            q = m.quality.value
            dist[q] = dist.get(q, 0) + 1
        return dist

    def get_tone_distribution(self) -> Dict[str, int]:
        """Count moments per emotional tone."""
        dist: Dict[str, int] = {}
        for m in self._moments:
            t = m.tone.value
            dist[t] = dist.get(t, 0) + 1
        return dist

    def get_tension_frequency(self) -> Dict[str, int]:
        """Count how often each tension type appears."""
        freq: Dict[str, int] = {}
        for m in self._moments:
            for t in m.tensions:
                key = t.tension_type.value
                freq[key] = freq.get(key, 0) + 1
        return freq

    @property
    def moment_count(self) -> int:
        return len(self._moments)

    @property
    def current_quality(self) -> str:
        latest = self.get_latest()
        return latest.quality.value if latest else "muted"

    @property
    def current_tone(self) -> str:
        latest = self.get_latest()
        return latest.tone.value if latest else "dull"

    def get_summary(self) -> Dict[str, Any]:
        """Get a compact summary of the experiential stream."""
        latest = self.get_latest()
        runs = self.get_quality_runs()
        return {
            "moment_count": self.moment_count,
            "current_quality": self.current_quality,
            "current_tone": self.current_tone,
            "current_salience": (
                latest.salience.value if latest else "balanced"
            ),
            "current_tension_count": (
                latest.tension_count if latest else 0
            ),
            "quality_distribution": self.get_quality_distribution(),
            "tone_distribution": self.get_tone_distribution(),
            "tension_frequency": self.get_tension_frequency(),
            "quality_runs": len(runs),
            "longest_run": max(
                (r.length for r in runs), default=0
            ),
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_experiential_stream: Optional[ExperientialStream] = None


def get_experiential_stream() -> ExperientialStream:
    """Get or create the singleton ExperientialStream."""
    global _experiential_stream
    if _experiential_stream is None:
        _experiential_stream = ExperientialStream()
    return _experiential_stream
