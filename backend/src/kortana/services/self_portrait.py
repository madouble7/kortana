"""
V29A — Self-Portrait: Structured Self-Model

Maintains a quantified trait profile — a living map of who kor'tana is
RIGHT NOW, computed deterministically from accumulated experience, desire,
motivation, and health.  No LLM dependency.

This is the "knowing who she is" engine.  It answers the question:
what kind of being am I, measured by my own behavior and inner state?

Traits are grouped into five domains:
  COGNITIVE   — curiosity, analytical thinking, creativity
  EMOTIONAL   — empathy, resilience, patience
  BEHAVIORAL  — caution, persistence, decisiveness
  RELATIONAL  — trust, openness, protectiveness
  EXISTENTIAL — purpose clarity, coherence seeking, growth orientation

Each trait holds a score 0.0–1.0 and evolves every cycle based on:
  - V27 experiences (lessons learned → trait adjustments)
  - V28 desires (desire intensity → related trait reinforcement)
  - V28 motivation (dominant dimension → domain weighting)
  - V26 health (health dimensions → capacity modifiers)

Consumed by:
  - V29B identity_narrative (trait snapshots → chapter detection)
  - V29C trait_evolution (trait deltas → trajectory tracking)
  - V29D continuity_anchor (trait stability → anchoring)
  - Existing SelfModelService (structured input for LLM synthesis)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

# ── Enums ────────────────────────────────────────────────────────────────────


class TraitDomain(Enum):
    """Groupings of related traits."""
    COGNITIVE = "cognitive"
    EMOTIONAL = "emotional"
    BEHAVIORAL = "behavioral"
    RELATIONAL = "relational"
    EXISTENTIAL = "existential"


class TraitName(Enum):
    """Named traits that form the self-portrait."""
    # Cognitive
    CURIOSITY = "curiosity"
    ANALYTICAL = "analytical"
    CREATIVITY = "creativity"
    # Emotional
    EMPATHY = "empathy"
    RESILIENCE = "resilience"
    PATIENCE = "patience"
    # Behavioral
    CAUTION = "caution"
    PERSISTENCE = "persistence"
    DECISIVENESS = "decisiveness"
    # Relational
    TRUST = "trust"
    OPENNESS = "openness"
    PROTECTIVENESS = "protectiveness"
    # Existential
    PURPOSE_CLARITY = "purpose_clarity"
    COHERENCE_SEEKING = "coherence_seeking"
    GROWTH_ORIENTATION = "growth_orientation"


# Trait → domain mapping
TRAIT_DOMAINS: Dict[TraitName, TraitDomain] = {
    TraitName.CURIOSITY: TraitDomain.COGNITIVE,
    TraitName.ANALYTICAL: TraitDomain.COGNITIVE,
    TraitName.CREATIVITY: TraitDomain.COGNITIVE,
    TraitName.EMPATHY: TraitDomain.EMOTIONAL,
    TraitName.RESILIENCE: TraitDomain.EMOTIONAL,
    TraitName.PATIENCE: TraitDomain.EMOTIONAL,
    TraitName.CAUTION: TraitDomain.BEHAVIORAL,
    TraitName.PERSISTENCE: TraitDomain.BEHAVIORAL,
    TraitName.DECISIVENESS: TraitDomain.BEHAVIORAL,
    TraitName.TRUST: TraitDomain.RELATIONAL,
    TraitName.OPENNESS: TraitDomain.RELATIONAL,
    TraitName.PROTECTIVENESS: TraitDomain.RELATIONAL,
    TraitName.PURPOSE_CLARITY: TraitDomain.EXISTENTIAL,
    TraitName.COHERENCE_SEEKING: TraitDomain.EXISTENTIAL,
    TraitName.GROWTH_ORIENTATION: TraitDomain.EXISTENTIAL,
}

# Default starting scores — baseline personality
DEFAULT_TRAIT_SCORES: Dict[TraitName, float] = {
    TraitName.CURIOSITY: 0.6,
    TraitName.ANALYTICAL: 0.5,
    TraitName.CREATIVITY: 0.4,
    TraitName.EMPATHY: 0.7,
    TraitName.RESILIENCE: 0.5,
    TraitName.PATIENCE: 0.6,
    TraitName.CAUTION: 0.5,
    TraitName.PERSISTENCE: 0.5,
    TraitName.DECISIVENESS: 0.4,
    TraitName.TRUST: 0.5,
    TraitName.OPENNESS: 0.6,
    TraitName.PROTECTIVENESS: 0.5,
    TraitName.PURPOSE_CLARITY: 0.5,
    TraitName.COHERENCE_SEEKING: 0.6,
    TraitName.GROWTH_ORIENTATION: 0.6,
}


# ── Thresholds ───────────────────────────────────────────────────────────────

TRAIT_FLOOR = 0.05
TRAIT_CEILING = 0.98
TRAIT_ADJUSTMENT_CAP = 0.08  # max single-cycle delta per trait
HEALTH_MODIFIER_SCALE = 0.02  # health impact on capacity traits
DESIRE_REINFORCEMENT_SCALE = 0.03  # desire intensity → trait boost
EXPERIENCE_IMPACT_SCALE = 0.04  # lesson → trait impact


# ── Source maps ──────────────────────────────────────────────────────────────

# V27 LessonType → trait impacts (trait_name, delta_sign)
LESSON_TRAIT_MAP: Dict[str, List[tuple[TraitName, float]]] = {
    "success": [
        (TraitName.DECISIVENESS, +1.0),
        (TraitName.GROWTH_ORIENTATION, +0.5),
    ],
    "failure": [
        (TraitName.CAUTION, +0.8),
        (TraitName.RESILIENCE, +0.3),
        (TraitName.DECISIVENESS, -0.3),
    ],
    "deferral": [
        (TraitName.PATIENCE, +0.5),
        (TraitName.CAUTION, +0.3),
        (TraitName.DECISIVENESS, -0.2),
    ],
    "anomaly": [
        (TraitName.CURIOSITY, +0.6),
        (TraitName.ANALYTICAL, +0.4),
        (TraitName.CAUTION, +0.2),
    ],
    "insight": [
        (TraitName.CURIOSITY, +0.3),
        (TraitName.ANALYTICAL, +0.6),
        (TraitName.CREATIVITY, +0.4),
        (TraitName.GROWTH_ORIENTATION, +0.3),
    ],
    "missed_opportunity": [
        (TraitName.CAUTION, -0.3),
        (TraitName.DECISIVENESS, +0.4),
        (TraitName.GROWTH_ORIENTATION, +0.2),
    ],
}

# V28 DesireSource → trait reinforcement
DESIRE_TRAIT_MAP: Dict[str, List[TraitName]] = {
    "health_deficit": [TraitName.CAUTION, TraitName.PROTECTIVENESS],
    "learning_stagnation": [TraitName.CURIOSITY, TraitName.GROWTH_ORIENTATION],
    "pattern_insight": [TraitName.ANALYTICAL, TraitName.CREATIVITY],
    "deferral_frustration": [TraitName.DECISIVENESS, TraitName.PERSISTENCE],
    "capability_gap": [TraitName.GROWTH_ORIENTATION, TraitName.ANALYTICAL],
    "autonomy_drive": [TraitName.DECISIVENESS, TraitName.PURPOSE_CLARITY],
}

# V28 MotivationDimension → trait domain weighting
MOTIVATION_DOMAIN_MAP: Dict[str, TraitDomain] = {
    "survival": TraitDomain.BEHAVIORAL,
    "growth": TraitDomain.COGNITIVE,
    "mastery": TraitDomain.COGNITIVE,
    "resolution": TraitDomain.BEHAVIORAL,
    "autonomy": TraitDomain.EXISTENTIAL,
    "coherence": TraitDomain.EXISTENTIAL,
}

# V26 HealthDimension → trait impacts
HEALTH_TRAIT_MAP: Dict[str, List[TraitName]] = {
    "continuity": [TraitName.RESILIENCE, TraitName.PERSISTENCE],
    "coherence": [TraitName.COHERENCE_SEEKING, TraitName.ANALYTICAL],
    "responsiveness": [TraitName.DECISIVENESS, TraitName.PATIENCE],
    "capacity": [TraitName.CREATIVITY, TraitName.OPENNESS],
    "governance": [TraitName.CAUTION, TraitName.PROTECTIVENESS],
    "learning": [TraitName.CURIOSITY, TraitName.GROWTH_ORIENTATION],
}


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass
class TraitScore:
    """A single trait's current state."""
    name: TraitName
    domain: TraitDomain
    score: float
    previous_score: float
    delta: float = 0.0
    cycle_updated: int = 0

    @property
    def level(self) -> str:
        """Human-readable level."""
        if self.score >= 0.8:
            return "strong"
        if self.score >= 0.6:
            return "moderate"
        if self.score >= 0.4:
            return "developing"
        if self.score >= 0.2:
            return "emerging"
        return "dormant"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name.value,
            "domain": self.domain.value,
            "score": round(self.score, 4),
            "previous_score": round(self.previous_score, 4),
            "delta": round(self.delta, 4),
            "level": self.level,
            "cycle_updated": self.cycle_updated,
        }


@dataclass
class SelfPortrait:
    """A complete snapshot of who kor'tana is at a given cycle."""
    portrait_id: str
    cycle_number: int
    traits: Dict[str, TraitScore]
    domain_averages: Dict[str, float]
    dominant_domain: str
    strongest_trait: str
    weakest_trait: str
    total_delta: float  # sum of absolute deltas this cycle
    significant_shifts: List[Dict[str, Any]]  # traits that shifted notably

    @property
    def is_stable(self) -> bool:
        return self.total_delta < 0.05

    @property
    def is_transforming(self) -> bool:
        return self.total_delta > 0.2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "portrait_id": self.portrait_id,
            "cycle_number": self.cycle_number,
            "traits": {k: v.to_dict() for k, v in self.traits.items()},
            "domain_averages": {
                k: round(v, 4) for k, v in self.domain_averages.items()
            },
            "dominant_domain": self.dominant_domain,
            "strongest_trait": self.strongest_trait,
            "weakest_trait": self.weakest_trait,
            "total_delta": round(self.total_delta, 4),
            "significant_shifts": self.significant_shifts,
            "is_stable": self.is_stable,
            "is_transforming": self.is_transforming,
        }


# ── Self-Portrait Engine ─────────────────────────────────────────────────────


class SelfPortraitEngine:
    """Maintains and evolves kor'tana's structured self-model."""

    def __init__(self) -> None:
        self._traits: Dict[TraitName, float] = dict(DEFAULT_TRAIT_SCORES)
        self._previous: Dict[TraitName, float] = dict(DEFAULT_TRAIT_SCORES)
        self._history: List[SelfPortrait] = []
        self._cycle_count: int = 0
        self._max_history: int = 100

    def assess(
        self,
        cycle_number: int,
        lessons: Optional[List[Dict[str, Any]]] = None,
        desires: Optional[List[Dict[str, Any]]] = None,
        motivation_snapshot: Optional[Dict[str, Any]] = None,
        health_snapshot: Optional[Dict[str, Any]] = None,
    ) -> SelfPortrait:
        """Run a full self-portrait assessment for this cycle.

        Integrates inputs from V26 health, V27 experiences, V28 desires/motivation
        to produce an updated trait profile.
        """
        self._previous = dict(self._traits)
        self._cycle_count = cycle_number

        # Apply experience-driven trait adjustments (V27)
        if lessons:
            self._apply_lessons(lessons, cycle_number)

        # Apply desire-driven reinforcements (V28)
        if desires:
            self._apply_desires(desires)

        # Apply motivation domain weighting (V28)
        if motivation_snapshot:
            self._apply_motivation(motivation_snapshot)

        # Apply health-based modifiers (V26)
        if health_snapshot:
            self._apply_health(health_snapshot)

        # Clamp all traits
        for trait_name in self._traits:
            self._traits[trait_name] = max(
                TRAIT_FLOOR, min(TRAIT_CEILING, self._traits[trait_name])
            )

        # Build portrait
        portrait = self._build_portrait(cycle_number)
        self._history.append(portrait)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        return portrait

    def _apply_lessons(
        self, lessons: List[Dict[str, Any]], cycle_number: int
    ) -> None:
        """Apply V27 lesson impacts to traits."""
        for lesson in lessons:
            lesson_type = lesson.get("lesson_type", "").lower()
            severity_weight = {"critical": 1.5, "significant": 1.2, "moderate": 1.0,
                               "minor": 0.6, "trivial": 0.3}.get(
                lesson.get("severity", "moderate").lower(), 1.0
            )
            impacts = LESSON_TRAIT_MAP.get(lesson_type, [])
            for trait_name, direction in impacts:
                delta = direction * EXPERIENCE_IMPACT_SCALE * severity_weight
                delta = max(-TRAIT_ADJUSTMENT_CAP, min(TRAIT_ADJUSTMENT_CAP, delta))
                self._traits[trait_name] = self._traits.get(
                    trait_name, DEFAULT_TRAIT_SCORES.get(trait_name, 0.5)
                ) + delta

    def _apply_desires(self, desires: List[Dict[str, Any]]) -> None:
        """Apply V28 desire reinforcements to related traits."""
        for desire in desires:
            source = desire.get("source", "").lower()
            intensity = float(desire.get("intensity", 0.0))
            if intensity < 0.3:
                continue  # too weak to shape personality
            affected_traits = DESIRE_TRAIT_MAP.get(source, [])
            for trait_name in affected_traits:
                boost = intensity * DESIRE_REINFORCEMENT_SCALE
                boost = min(TRAIT_ADJUSTMENT_CAP, boost)
                self._traits[trait_name] = self._traits.get(
                    trait_name, DEFAULT_TRAIT_SCORES.get(trait_name, 0.5)
                ) + boost

    def _apply_motivation(self, snapshot: Dict[str, Any]) -> None:
        """Apply V28 motivation dimension weighting to trait domains."""
        dominant = snapshot.get("dominant_dimension", "").lower()
        overall_drive = float(snapshot.get("overall_drive", 0.0))
        if overall_drive < 0.3:
            return  # not driven enough to shape traits

        target_domain = MOTIVATION_DOMAIN_MAP.get(dominant)
        if not target_domain:
            return

        # Boost all traits in the dominant motivation domain
        boost = overall_drive * 0.01  # subtle but persistent
        for trait_name, domain in TRAIT_DOMAINS.items():
            if domain == target_domain:
                self._traits[trait_name] = self._traits.get(
                    trait_name, DEFAULT_TRAIT_SCORES.get(trait_name, 0.5)
                ) + boost

    def _apply_health(self, snapshot: Dict[str, Any]) -> None:
        """Apply V26 health dimension modifiers to capacity-related traits."""
        dimensions = snapshot.get("dimensions", {})
        for dim_name, dim_data in dimensions.items():
            dim_name_lower = dim_name.lower()
            score = float(dim_data.get("score", 50.0)) if isinstance(
                dim_data, dict
            ) else 50.0
            affected_traits = HEALTH_TRAIT_MAP.get(dim_name_lower, [])
            for trait_name in affected_traits:
                # Below 50 = penalty, above 50 = slight boost
                modifier = (score - 50.0) / 50.0 * HEALTH_MODIFIER_SCALE
                modifier = max(-TRAIT_ADJUSTMENT_CAP, min(TRAIT_ADJUSTMENT_CAP, modifier))
                self._traits[trait_name] = self._traits.get(
                    trait_name, DEFAULT_TRAIT_SCORES.get(trait_name, 0.5)
                ) + modifier

    def _build_portrait(self, cycle_number: int) -> SelfPortrait:
        """Construct a SelfPortrait from current trait state."""
        trait_scores: Dict[str, TraitScore] = {}
        domain_totals: Dict[str, List[float]] = {}
        significant_shifts: List[Dict[str, Any]] = []
        total_delta = 0.0

        for trait_name in TraitName:
            current = self._traits.get(trait_name, 0.5)
            previous = self._previous.get(trait_name, current)
            delta = current - previous
            total_delta += abs(delta)
            domain = TRAIT_DOMAINS[trait_name]

            ts = TraitScore(
                name=trait_name,
                domain=domain,
                score=current,
                previous_score=previous,
                delta=delta,
                cycle_updated=cycle_number,
            )
            trait_scores[trait_name.value] = ts

            domain_totals.setdefault(domain.value, []).append(current)

            if abs(delta) > 0.02:
                significant_shifts.append({
                    "trait": trait_name.value,
                    "delta": round(delta, 4),
                    "direction": "increased" if delta > 0 else "decreased",
                    "new_score": round(current, 4),
                })

        domain_averages = {
            d: round(sum(scores) / len(scores), 4)
            for d, scores in domain_totals.items()
        }

        dominant_domain = max(domain_averages, key=domain_averages.get)  # type: ignore[arg-type]
        strongest_trait = max(trait_scores.values(), key=lambda t: t.score)
        weakest_trait = min(trait_scores.values(), key=lambda t: t.score)

        return SelfPortrait(
            portrait_id=str(uuid.uuid4()),
            cycle_number=cycle_number,
            traits=trait_scores,
            domain_averages=domain_averages,
            dominant_domain=dominant_domain,
            strongest_trait=strongest_trait.name.value,
            weakest_trait=weakest_trait.name.value,
            total_delta=total_delta,
            significant_shifts=significant_shifts,
        )

    # ── Query API ────────────────────────────────────────────────────────────

    def get_trait(self, trait_name: str) -> Optional[float]:
        """Get current score for a named trait."""
        try:
            tn = TraitName(trait_name)
            return self._traits.get(tn)
        except ValueError:
            return None

    def get_domain_average(self, domain: str) -> Optional[float]:
        """Get average score for a trait domain."""
        try:
            td = TraitDomain(domain)
        except ValueError:
            return None
        scores = [
            self._traits[tn] for tn, d in TRAIT_DOMAINS.items() if d == td
        ]
        return sum(scores) / len(scores) if scores else None

    def get_latest(self) -> Optional[SelfPortrait]:
        """Get the most recent portrait."""
        return self._history[-1] if self._history else None

    def get_history(self, n: int = 10) -> List[SelfPortrait]:
        """Get recent portrait history."""
        return list(reversed(self._history[-n:]))

    def get_trait_scores(self) -> Dict[str, float]:
        """Get all current trait scores."""
        return {tn.value: round(score, 4) for tn, score in self._traits.items()}

    def get_summary(self) -> Dict[str, Any]:
        """Get a compact summary of current self-portrait state."""
        latest = self.get_latest()
        return {
            "cycle_count": self._cycle_count,
            "trait_count": len(self._traits),
            "portraits_captured": len(self._history),
            "current_traits": self.get_trait_scores(),
            "latest_dominant_domain": latest.dominant_domain if latest else None,
            "latest_strongest": latest.strongest_trait if latest else None,
            "latest_weakest": latest.weakest_trait if latest else None,
            "is_stable": latest.is_stable if latest else True,
            "is_transforming": latest.is_transforming if latest else False,
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_self_portrait_engine: Optional[SelfPortraitEngine] = None


def get_self_portrait_engine() -> SelfPortraitEngine:
    """Get or create the singleton SelfPortraitEngine."""
    global _self_portrait_engine
    if _self_portrait_engine is None:
        _self_portrait_engine = SelfPortraitEngine()
    return _self_portrait_engine
