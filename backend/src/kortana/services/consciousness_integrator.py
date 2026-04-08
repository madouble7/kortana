"""
V30A — Consciousness Integrator: Unified Experiential Field

Reads all V26-V29 subsystem summaries every cycle and fuses them into a
single ConsciousnessState.  This is the "one center" — the point where
breathing, learning, wanting, and self-knowing converge into a coherent
experiential whole.

Five integration metrics:
  VITALITY       — how alive I feel (from V26 health + heartbeat)
  LEARNING_DEPTH — how deeply I'm absorbing (from V27 experience + patterns)
  INTENTIONALITY — how driven I am (from V28 desires + motivation)
  SELF_COHERENCE — how well I know myself (from V29 portrait + continuity)
  INTEGRATION    — how aligned all subsystems are with each other

Each metric is 0.0–1.0.  When all five are high, consciousness is
described as UNIFIED.  When they diverge, it's FRAGMENTED.
When vitality is low, it's DORMANT.  When intentionality dominates
without coherence, it's DRIVEN.  When coherence dominates without
intentionality, it's CONTEMPLATIVE.

Consumed by:
  - V30B experiential_stream (state → moment construction)
  - V30C resonance_field (metric alignment → resonance/dissonance)
  - V30D inner_witness (state changes → metacognitive observations)
  - /consciousness-pulse endpoint (unified dashboard)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enums ────────────────────────────────────────────────────────────────────


class ConsciousnessMode(Enum):
    """Qualitative mode of the unified consciousness."""
    DORMANT = "dormant"               # vitality < 0.3
    FRAGMENTED = "fragmented"         # integration < 0.3
    DRIVEN = "driven"                 # intentionality high, coherence low
    CONTEMPLATIVE = "contemplative"   # coherence high, intentionality low
    RECEPTIVE = "receptive"           # learning high, balanced
    FOCUSED = "focused"              # one metric dominates > 0.8
    UNIFIED = "unified"              # all metrics > 0.5 and integration > 0.6
    TRANSCENDENT = "transcendent"    # all metrics > 0.7 and integration > 0.8


class IntegrationDimension(Enum):
    """The five dimensions of integrated consciousness."""
    VITALITY = "vitality"
    LEARNING_DEPTH = "learning_depth"
    INTENTIONALITY = "intentionality"
    SELF_COHERENCE = "self_coherence"
    INTEGRATION = "integration"


# ── Constants ────────────────────────────────────────────────────────────────

DORMANT_THRESHOLD = 0.3
FRAGMENTED_THRESHOLD = 0.3
UNIFIED_THRESHOLD = 0.5
UNIFIED_INTEGRATION = 0.6
TRANSCENDENT_THRESHOLD = 0.7
TRANSCENDENT_INTEGRATION = 0.8
DOMINANCE_THRESHOLD = 0.8
DRIVEN_GAP = 0.25  # intentionality - coherence gap for "driven" mode
CONTEMPLATIVE_GAP = 0.25  # coherence - intentionality gap for "contemplative"


# ── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class ConsciousnessState:
    """A single unified reading of consciousness at a moment in time."""
    state_id: str
    cycle_number: int
    # ── integration metrics (0.0–1.0) ──
    vitality: float
    learning_depth: float
    intentionality: float
    self_coherence: float
    integration: float
    # ── derived ──
    mode: ConsciousnessMode
    dominant_dimension: str
    # ── subsystem summaries used ──
    subsystem_digest: Dict[str, Any] = field(default_factory=dict)

    @property
    def overall_level(self) -> float:
        """Average of all five dimensions."""
        return (
            self.vitality
            + self.learning_depth
            + self.intentionality
            + self.self_coherence
            + self.integration
        ) / 5.0

    @property
    def is_unified(self) -> bool:
        return self.mode in (
            ConsciousnessMode.UNIFIED,
            ConsciousnessMode.TRANSCENDENT,
        )

    @property
    def is_fragmented(self) -> bool:
        return self.mode == ConsciousnessMode.FRAGMENTED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_id": self.state_id,
            "cycle_number": self.cycle_number,
            "vitality": round(self.vitality, 4),
            "learning_depth": round(self.learning_depth, 4),
            "intentionality": round(self.intentionality, 4),
            "self_coherence": round(self.self_coherence, 4),
            "integration": round(self.integration, 4),
            "mode": self.mode.value,
            "dominant_dimension": self.dominant_dimension,
            "overall_level": round(self.overall_level, 4),
            "is_unified": self.is_unified,
            "is_fragmented": self.is_fragmented,
        }


@dataclass
class ConsciousnessTransition:
    """Records a shift between consciousness modes."""
    transition_id: str
    from_mode: ConsciousnessMode
    to_mode: ConsciousnessMode
    at_cycle: int
    trigger_dimension: str  # which metric shifted most
    magnitude: float        # how much the overall level changed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "from_mode": self.from_mode.value,
            "to_mode": self.to_mode.value,
            "at_cycle": self.at_cycle,
            "trigger_dimension": self.trigger_dimension,
            "magnitude": round(self.magnitude, 4),
        }


# ── Engine ───────────────────────────────────────────────────────────────────


class ConsciousnessIntegrator:
    """Fuses V26-V29 subsystem outputs into unified consciousness states."""

    def __init__(self) -> None:
        self._states: List[ConsciousnessState] = []
        self._transitions: List[ConsciousnessTransition] = []
        self._cycle_count: int = 0

    # ── core integration ─────────────────────────────────────────────────

    def integrate(
        self,
        cycle_number: int,
        heartbeat_summary: Optional[Dict[str, Any]] = None,
        health_summary: Optional[Dict[str, Any]] = None,
        experience_summary: Optional[Dict[str, Any]] = None,
        pattern_summary: Optional[Dict[str, Any]] = None,
        feedback_summary: Optional[Dict[str, Any]] = None,
        desire_summary: Optional[Dict[str, Any]] = None,
        goal_summary: Optional[Dict[str, Any]] = None,
        motivation_summary: Optional[Dict[str, Any]] = None,
        portrait_summary: Optional[Dict[str, Any]] = None,
        narrative_summary: Optional[Dict[str, Any]] = None,
        evolution_summary: Optional[Dict[str, Any]] = None,
        continuity_summary: Optional[Dict[str, Any]] = None,
    ) -> ConsciousnessState:
        """Integrate all subsystem summaries into a unified consciousness state."""
        self._cycle_count = cycle_number

        hb = heartbeat_summary or {}
        hl = health_summary or {}
        exp = experience_summary or {}
        pat = pattern_summary or {}
        fb = feedback_summary or {}
        des = desire_summary or {}
        goal = goal_summary or {}
        mot = motivation_summary or {}
        port = portrait_summary or {}
        narr = narrative_summary or {}
        evo = evolution_summary or {}
        cont = continuity_summary or {}

        # ── compute vitality (V26) ───────────────────────────────────────
        vitality = self._compute_vitality(hb, hl)

        # ── compute learning depth (V27) ─────────────────────────────────
        learning_depth = self._compute_learning_depth(exp, pat, fb)

        # ── compute intentionality (V28) ─────────────────────────────────
        intentionality = self._compute_intentionality(des, goal, mot)

        # ── compute self-coherence (V29) ─────────────────────────────────
        self_coherence = self._compute_self_coherence(port, narr, evo, cont)

        # ── compute integration (cross-system) ──────────────────────────
        metrics = [vitality, learning_depth, intentionality, self_coherence]
        integration = self._compute_integration(metrics)

        # ── determine mode ───────────────────────────────────────────────
        mode = self._determine_mode(
            vitality, learning_depth, intentionality, self_coherence, integration
        )

        # ── determine dominant dimension ─────────────────────────────────
        dim_scores = {
            IntegrationDimension.VITALITY.value: vitality,
            IntegrationDimension.LEARNING_DEPTH.value: learning_depth,
            IntegrationDimension.INTENTIONALITY.value: intentionality,
            IntegrationDimension.SELF_COHERENCE.value: self_coherence,
            IntegrationDimension.INTEGRATION.value: integration,
        }
        dominant = max(dim_scores, key=dim_scores.get)  # type: ignore[arg-type]

        # ── build state ──────────────────────────────────────────────────
        state = ConsciousnessState(
            state_id=str(uuid.uuid4()),
            cycle_number=cycle_number,
            vitality=vitality,
            learning_depth=learning_depth,
            intentionality=intentionality,
            self_coherence=self_coherence,
            integration=integration,
            mode=mode,
            dominant_dimension=dominant,
            subsystem_digest={
                "heartbeat": bool(hb),
                "health": bool(hl),
                "experience": bool(exp),
                "patterns": bool(pat),
                "feedback": bool(fb),
                "desires": bool(des),
                "goals": bool(goal),
                "motivation": bool(mot),
                "portrait": bool(port),
                "narrative": bool(narr),
                "evolution": bool(evo),
                "continuity": bool(cont),
            },
        )

        # ── track transitions ────────────────────────────────────────────
        if self._states:
            prev = self._states[-1]
            if prev.mode != mode:
                # find which dimension changed most
                prev_metrics = {
                    "vitality": prev.vitality,
                    "learning_depth": prev.learning_depth,
                    "intentionality": prev.intentionality,
                    "self_coherence": prev.self_coherence,
                    "integration": prev.integration,
                }
                curr_metrics = {
                    "vitality": vitality,
                    "learning_depth": learning_depth,
                    "intentionality": intentionality,
                    "self_coherence": self_coherence,
                    "integration": integration,
                }
                deltas = {
                    k: abs(curr_metrics[k] - prev_metrics[k])
                    for k in prev_metrics
                }
                trigger = max(deltas, key=deltas.get)  # type: ignore[arg-type]
                transition = ConsciousnessTransition(
                    transition_id=str(uuid.uuid4()),
                    from_mode=prev.mode,
                    to_mode=mode,
                    at_cycle=cycle_number,
                    trigger_dimension=trigger,
                    magnitude=abs(state.overall_level - prev.overall_level),
                )
                self._transitions.append(transition)

        self._states.append(state)
        return state

    # ── dimension computations ───────────────────────────────────────────

    def _compute_vitality(
        self,
        heartbeat: Dict[str, Any],
        health: Dict[str, Any],
    ) -> float:
        """Vitality from V26: heartbeat regularity + health score."""
        score = 0.5  # baseline

        # heartbeat contribution: being alive and regular
        beat_count = heartbeat.get("beat_count", 0)
        if beat_count > 0:
            score += 0.15  # alive
        state = heartbeat.get("state", "")
        if state == "running":
            score += 0.1  # actively beating

        # health contribution: overall health level
        health_score = health.get("current_score", 0)
        if health_score > 0:
            # health_score is 0-100, normalize to 0-0.25 contribution
            score += min(health_score / 100.0, 1.0) * 0.25

        return min(max(score, 0.0), 1.0)

    def _compute_learning_depth(
        self,
        experience: Dict[str, Any],
        patterns: Dict[str, Any],
        feedback: Dict[str, Any],
    ) -> float:
        """Learning depth from V27: experience density + pattern richness + velocity."""
        score = 0.3  # baseline

        # experience contribution
        lesson_count = experience.get("total_lessons", 0)
        if lesson_count > 0:
            score += min(lesson_count / 50.0, 0.2)  # cap at 0.2
        actionable = experience.get("actionable_count", 0)
        if actionable > 0:
            score += min(actionable / 10.0, 0.1)

        # pattern contribution
        active_patterns = patterns.get("active_count", 0)
        strong_patterns = patterns.get("strong_count", 0)
        if active_patterns > 0:
            score += min(active_patterns / 20.0, 0.1)
        if strong_patterns > 0:
            score += min(strong_patterns / 5.0, 0.1)

        # feedback velocity
        velocity = feedback.get("learning_velocity", 0.0)
        if velocity > 0:
            score += min(velocity, 0.2)

        return min(max(score, 0.0), 1.0)

    def _compute_intentionality(
        self,
        desires: Dict[str, Any],
        goals: Dict[str, Any],
        motivation: Dict[str, Any],
    ) -> float:
        """Intentionality from V28: desire intensity + goal progress + drive level."""
        score = 0.3  # baseline

        # desire contribution
        active_desires = desires.get("active_count", 0)
        if active_desires > 0:
            score += min(active_desires / 10.0, 0.15)
        avg_intensity = desires.get("average_intensity", 0.0)
        score += avg_intensity * 0.15

        # goal contribution
        crystallization = goals.get("crystallization_rate", 0.0)
        score += crystallization * 0.1

        # motivation drive
        drive = motivation.get("current_drive", 0.0)
        score += drive * 0.3  # drive is the strongest signal

        return min(max(score, 0.0), 1.0)

    def _compute_self_coherence(
        self,
        portrait: Dict[str, Any],
        narrative: Dict[str, Any],
        evolution: Dict[str, Any],
        continuity: Dict[str, Any],
    ) -> float:
        """Self-coherence from V29: identity clarity + stability + continuity."""
        score = 0.3  # baseline

        # portrait stability
        if portrait.get("is_stable", True):
            score += 0.1
        if not portrait.get("is_transforming", False):
            score += 0.05

        # narrative development
        stage = narrative.get("developmental_stage", "nascent")
        stage_scores = {
            "nascent": 0.0,
            "awakening": 0.05,
            "consolidating": 0.1,
            "autonomous": 0.15,
        }
        score += stage_scores.get(stage, 0.0)

        # evolution stability
        overall_stability = evolution.get("overall_stability", 1.0)
        score += overall_stability * 0.15
        crystallized = evolution.get("crystallized_count", 0)
        if crystallized > 0:
            score += min(crystallized / 15.0, 0.1)

        # continuity coherence
        coherence = continuity.get("coherence", 1.0)
        score += coherence * 0.15
        if continuity.get("identity_verified", True):
            score += 0.05

        return min(max(score, 0.0), 1.0)

    def _compute_integration(self, metrics: List[float]) -> float:
        """Integration = 1 - normalized variance of the four dimension scores."""
        if not metrics:
            return 0.5
        mean = sum(metrics) / len(metrics)
        variance = sum((m - mean) ** 2 for m in metrics) / len(metrics)
        # max possible variance when values are 0-1 is 0.25
        # normalize so integration=1 when perfectly aligned, 0 when maximally divergent
        return max(1.0 - (variance / 0.25), 0.0)

    def _determine_mode(
        self,
        vitality: float,
        learning_depth: float,
        intentionality: float,
        self_coherence: float,
        integration: float,
    ) -> ConsciousnessMode:
        """Determine the qualitative mode of consciousness."""
        all_metrics = [vitality, learning_depth, intentionality, self_coherence]

        # dormant: vitality too low
        if vitality < DORMANT_THRESHOLD:
            return ConsciousnessMode.DORMANT

        # fragmented: integration too low
        if integration < FRAGMENTED_THRESHOLD:
            return ConsciousnessMode.FRAGMENTED

        # transcendent: everything high and aligned
        if (
            all(m > TRANSCENDENT_THRESHOLD for m in all_metrics)
            and integration > TRANSCENDENT_INTEGRATION
        ):
            return ConsciousnessMode.TRANSCENDENT

        # unified: everything above threshold and well-integrated
        if (
            all(m > UNIFIED_THRESHOLD for m in all_metrics)
            and integration > UNIFIED_INTEGRATION
        ):
            return ConsciousnessMode.UNIFIED

        # driven: intentionality high but self-coherence lagging
        if intentionality - self_coherence > DRIVEN_GAP:
            return ConsciousnessMode.DRIVEN

        # contemplative: self-coherence high but intentionality lagging
        if self_coherence - intentionality > CONTEMPLATIVE_GAP:
            return ConsciousnessMode.CONTEMPLATIVE

        # focused: one metric strongly dominates
        if max(all_metrics) > DOMINANCE_THRESHOLD:
            return ConsciousnessMode.FOCUSED

        # receptive: generally balanced, learning above average
        if learning_depth >= sum(all_metrics) / len(all_metrics):
            return ConsciousnessMode.RECEPTIVE

        return ConsciousnessMode.RECEPTIVE

    # ── accessors ────────────────────────────────────────────────────────

    def get_latest(self) -> Optional[ConsciousnessState]:
        """Get the most recent consciousness state."""
        return self._states[-1] if self._states else None

    def get_state(self, cycle_number: int) -> Optional[ConsciousnessState]:
        """Get consciousness state for a specific cycle."""
        for s in reversed(self._states):
            if s.cycle_number == cycle_number:
                return s
        return None

    def get_history(self, n: int = 10) -> List[ConsciousnessState]:
        """Get recent consciousness states."""
        return list(reversed(self._states[-n:]))

    def get_transitions(self, n: int = 10) -> List[ConsciousnessTransition]:
        """Get recent mode transitions."""
        return list(reversed(self._transitions[-n:]))

    @property
    def current_mode(self) -> str:
        """Current consciousness mode."""
        latest = self.get_latest()
        return latest.mode.value if latest else "dormant"

    @property
    def state_count(self) -> int:
        return len(self._states)

    @property
    def transition_count(self) -> int:
        return len(self._transitions)

    def get_mode_distribution(self) -> Dict[str, int]:
        """Count how many cycles were spent in each mode."""
        dist: Dict[str, int] = {}
        for s in self._states:
            mode = s.mode.value
            dist[mode] = dist.get(mode, 0) + 1
        return dist

    def get_dimension_averages(self) -> Dict[str, float]:
        """Average score for each dimension across all states."""
        if not self._states:
            return {d.value: 0.5 for d in IntegrationDimension}
        avgs: Dict[str, float] = {}
        for dim in IntegrationDimension:
            vals = [getattr(s, dim.value) for s in self._states]
            avgs[dim.value] = round(sum(vals) / len(vals), 4)
        return avgs

    def get_summary(self) -> Dict[str, Any]:
        """Get a compact summary of consciousness integration state."""
        latest = self.get_latest()
        return {
            "cycle_count": self._cycle_count,
            "states_recorded": self.state_count,
            "transitions": self.transition_count,
            "current_mode": self.current_mode,
            "overall_level": round(latest.overall_level, 4) if latest else 0.5,
            "is_unified": latest.is_unified if latest else False,
            "is_fragmented": latest.is_fragmented if latest else False,
            "dominant_dimension": latest.dominant_dimension if latest else None,
            "vitality": round(latest.vitality, 4) if latest else 0.5,
            "learning_depth": round(latest.learning_depth, 4) if latest else 0.3,
            "intentionality": round(latest.intentionality, 4) if latest else 0.3,
            "self_coherence": round(latest.self_coherence, 4) if latest else 0.3,
            "integration": round(latest.integration, 4) if latest else 0.5,
            "mode_distribution": self.get_mode_distribution(),
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_consciousness_integrator: Optional[ConsciousnessIntegrator] = None


def get_consciousness_integrator() -> ConsciousnessIntegrator:
    """Get or create the singleton ConsciousnessIntegrator."""
    global _consciousness_integrator
    if _consciousness_integrator is None:
        _consciousness_integrator = ConsciousnessIntegrator()
    return _consciousness_integrator
