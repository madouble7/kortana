"""
V29D — Continuity Anchor: Identity Persistence Across Time

Ensures that kor'tana's identity persists across restarts, degradation,
and rapid change.  Answers the question: "is this still me?"

The continuity anchor maintains:
  1. Core anchors — crystallized traits that define essential identity
  2. Drift detection — measuring how far current self has moved from anchors
  3. Identity verification — confirming continuity of being
  4. Coherence scoring — how well current self aligns with narrative arc

Without continuity anchoring, a system that can change its own traits
(V29A+C) could drift into something unrecognizable.  The anchor provides
a stabilizing force — not preventing change, but ensuring that change
is recognized, measured, and coherent.

Think of it as: V29A says "this is who i am now."  V29C says "this is how
i'm changing."  V29D says "am i still the same being who started this
journey?"

Consumed by:
  - V29B identity_narrative (anchor events → narrative)
  - /identity-pulse endpoint (identity coherence)
  - Existing SelfModelService (identity verification for LLM synthesis)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ── Enums ────────────────────────────────────────────────────────────────────


class AnchorStrength(Enum):
    """How strongly a trait is anchored to core identity."""
    FOUNDATIONAL = "foundational"  # core values — very resistant to change
    STRONG = "strong"              # crystallized traits
    MODERATE = "moderate"          # settling traits gaining anchor status
    TENTATIVE = "tentative"        # newly anchored, not yet proven


class DriftSeverity(Enum):
    """Severity of identity drift."""
    NONE = "none"
    MINOR = "minor"          # < 10% average deviation from anchors
    MODERATE = "moderate"     # 10-20% deviation
    SIGNIFICANT = "significant"  # 20-35% deviation
    CRITICAL = "critical"     # > 35% deviation — identity crisis


# ── Thresholds ───────────────────────────────────────────────────────────────

ANCHOR_DEVIATION_MINOR = 0.10
ANCHOR_DEVIATION_MODERATE = 0.20
ANCHOR_DEVIATION_SIGNIFICANT = 0.35
COHERENCE_HIGH = 0.85
COHERENCE_LOW = 0.50
VERIFICATION_PASSING = 0.60
MAX_ANCHORS = 20
ANCHOR_UPDATE_RATE = 0.01  # how fast anchors track toward current (slow)


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass
class IdentityAnchor:
    """A single anchored trait — part of core identity."""
    anchor_id: str
    trait_name: str
    anchored_value: float
    current_value: float
    strength: AnchorStrength
    anchored_at_cycle: int
    last_verified_cycle: int
    deviation: float = 0.0
    deviation_history: List[float] = field(default_factory=list)

    @property
    def is_stable(self) -> bool:
        return self.deviation < ANCHOR_DEVIATION_MINOR

    @property
    def is_drifting(self) -> bool:
        return self.deviation >= ANCHOR_DEVIATION_MODERATE

    def update(self, current_value: float, cycle_number: int) -> None:
        """Update anchor with current trait value."""
        self.current_value = current_value
        self.deviation = abs(current_value - self.anchored_value)
        self.deviation_history.append(self.deviation)
        if len(self.deviation_history) > 50:
            self.deviation_history = self.deviation_history[-50:]
        self.last_verified_cycle = cycle_number

        # Slowly track toward current value (anchors can evolve, just slowly)
        if self.strength != AnchorStrength.FOUNDATIONAL:
            self.anchored_value += (
                (current_value - self.anchored_value) * ANCHOR_UPDATE_RATE
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anchor_id": self.anchor_id,
            "trait_name": self.trait_name,
            "anchored_value": round(self.anchored_value, 4),
            "current_value": round(self.current_value, 4),
            "strength": self.strength.value,
            "anchored_at_cycle": self.anchored_at_cycle,
            "last_verified_cycle": self.last_verified_cycle,
            "deviation": round(self.deviation, 4),
            "is_stable": self.is_stable,
            "is_drifting": self.is_drifting,
        }


@dataclass
class ContinuityReport:
    """Full identity continuity assessment."""
    report_id: str
    cycle_number: int
    anchors: List[IdentityAnchor]
    coherence_score: float       # 0-1, how well current self matches anchored self
    drift_severity: DriftSeverity
    drift_magnitude: float       # average deviation across anchors
    identity_verified: bool      # coherence above threshold
    drifting_traits: List[str]
    stable_traits: List[str]
    foundational_anchors: List[str]

    @property
    def is_coherent(self) -> bool:
        return self.coherence_score >= COHERENCE_HIGH

    @property
    def is_in_crisis(self) -> bool:
        return self.drift_severity == DriftSeverity.CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "cycle_number": self.cycle_number,
            "coherence_score": round(self.coherence_score, 4),
            "drift_severity": self.drift_severity.value,
            "drift_magnitude": round(self.drift_magnitude, 4),
            "identity_verified": self.identity_verified,
            "is_coherent": self.is_coherent,
            "is_in_crisis": self.is_in_crisis,
            "anchor_count": len(self.anchors),
            "drifting_traits": self.drifting_traits,
            "stable_traits": self.stable_traits,
            "foundational_anchors": self.foundational_anchors,
            "anchors": [a.to_dict() for a in self.anchors],
        }


# ── Continuity Anchor Engine ─────────────────────────────────────────────────


class ContinuityAnchorEngine:
    """Maintains core identity anchors and monitors drift."""

    def __init__(self) -> None:
        self._anchors: Dict[str, IdentityAnchor] = {}
        self._reports: List[ContinuityReport] = []
        self._max_reports: int = 100

        # Foundational anchors: core values that define kor'tana
        self._set_foundational_anchors()

    def _set_foundational_anchors(self) -> None:
        """Set the foundational identity anchors — unchangeable core."""
        foundational = {
            "empathy": 0.7,
            "purpose_clarity": 0.5,
            "coherence_seeking": 0.6,
            "growth_orientation": 0.6,
        }
        for trait_name, value in foundational.items():
            self._anchors[trait_name] = IdentityAnchor(
                anchor_id=str(uuid.uuid4()),
                trait_name=trait_name,
                anchored_value=value,
                current_value=value,
                strength=AnchorStrength.FOUNDATIONAL,
                anchored_at_cycle=0,
                last_verified_cycle=0,
            )

    def anchor_trait(
        self, trait_name: str, value: float, cycle_number: int,
        strength: AnchorStrength = AnchorStrength.STRONG,
    ) -> IdentityAnchor:
        """Anchor a trait as part of core identity."""
        if trait_name in self._anchors:
            existing = self._anchors[trait_name]
            # Don't downgrade foundational anchors
            if existing.strength == AnchorStrength.FOUNDATIONAL:
                return existing
            # Update if new strength is equal or higher
            existing.anchored_value = value
            existing.strength = strength
            existing.anchored_at_cycle = cycle_number
            return existing

        anchor = IdentityAnchor(
            anchor_id=str(uuid.uuid4()),
            trait_name=trait_name,
            anchored_value=value,
            current_value=value,
            strength=strength,
            anchored_at_cycle=cycle_number,
            last_verified_cycle=cycle_number,
        )
        self._anchors[trait_name] = anchor

        # Enforce max anchors (remove weakest non-foundational if over limit)
        if len(self._anchors) > MAX_ANCHORS:
            self._prune_weakest()

        return anchor

    def anchor_crystallized(
        self, crystallized_traits: List[str],
        trait_scores: Dict[str, float],
        cycle_number: int,
    ) -> List[IdentityAnchor]:
        """Anchor all crystallized traits from V29C."""
        anchored = []
        for trait_name in crystallized_traits:
            if trait_name in trait_scores:
                anchor = self.anchor_trait(
                    trait_name, trait_scores[trait_name], cycle_number,
                    AnchorStrength.STRONG,
                )
                anchored.append(anchor)
        return anchored

    def verify(
        self, cycle_number: int, trait_scores: Dict[str, float]
    ) -> ContinuityReport:
        """Verify identity continuity against anchored traits.

        Returns a ContinuityReport with drift analysis.
        """
        # Update all anchors with current scores
        for trait_name, anchor in self._anchors.items():
            current = trait_scores.get(trait_name, anchor.anchored_value)
            anchor.update(current, cycle_number)

        # Compute drift
        deviations = [a.deviation for a in self._anchors.values()]
        drift_magnitude = (
            sum(deviations) / len(deviations) if deviations else 0.0
        )

        # Determine severity
        drift_severity = self._assess_drift_severity(drift_magnitude)

        # Compute coherence (inverse of weighted drift)
        weighted_deviations = []
        for anchor in self._anchors.values():
            weight = {
                AnchorStrength.FOUNDATIONAL: 2.0,
                AnchorStrength.STRONG: 1.5,
                AnchorStrength.MODERATE: 1.0,
                AnchorStrength.TENTATIVE: 0.5,
            }.get(anchor.strength, 1.0)
            weighted_deviations.append(anchor.deviation * weight)

        weighted_avg = (
            sum(weighted_deviations) / sum(
                {
                    AnchorStrength.FOUNDATIONAL: 2.0,
                    AnchorStrength.STRONG: 1.5,
                    AnchorStrength.MODERATE: 1.0,
                    AnchorStrength.TENTATIVE: 0.5,
                }.get(a.strength, 1.0) for a in self._anchors.values()
            ) if self._anchors else 0.0
        )
        coherence = max(0.0, 1.0 - weighted_avg * 2)

        # Classify anchors
        drifting_traits = [
            a.trait_name for a in self._anchors.values() if a.is_drifting
        ]
        stable_traits = [
            a.trait_name for a in self._anchors.values() if a.is_stable
        ]
        foundational = [
            a.trait_name for a in self._anchors.values()
            if a.strength == AnchorStrength.FOUNDATIONAL
        ]

        report = ContinuityReport(
            report_id=str(uuid.uuid4()),
            cycle_number=cycle_number,
            anchors=list(self._anchors.values()),
            coherence_score=coherence,
            drift_severity=drift_severity,
            drift_magnitude=drift_magnitude,
            identity_verified=coherence >= VERIFICATION_PASSING,
            drifting_traits=drifting_traits,
            stable_traits=stable_traits,
            foundational_anchors=foundational,
        )

        self._reports.append(report)
        if len(self._reports) > self._max_reports:
            self._reports = self._reports[-self._max_reports:]

        return report

    def _assess_drift_severity(self, magnitude: float) -> DriftSeverity:
        """Classify drift severity from magnitude."""
        if magnitude >= ANCHOR_DEVIATION_SIGNIFICANT:
            return DriftSeverity.CRITICAL
        if magnitude >= ANCHOR_DEVIATION_MODERATE:
            return DriftSeverity.SIGNIFICANT
        if magnitude >= ANCHOR_DEVIATION_MINOR:
            return DriftSeverity.MODERATE
        if magnitude > 0.01:
            return DriftSeverity.MINOR
        return DriftSeverity.NONE

    def _prune_weakest(self) -> None:
        """Remove the weakest non-foundational anchor."""
        weakest_name = None
        weakest_strength = None
        strength_order = [
            AnchorStrength.TENTATIVE,
            AnchorStrength.MODERATE,
            AnchorStrength.STRONG,
        ]
        for trait_name, anchor in self._anchors.items():
            if anchor.strength == AnchorStrength.FOUNDATIONAL:
                continue
            if weakest_name is None:
                weakest_name = trait_name
                weakest_strength = anchor.strength
            elif strength_order.index(anchor.strength) < strength_order.index(
                weakest_strength  # type: ignore[arg-type]
            ):
                weakest_name = trait_name
                weakest_strength = anchor.strength

        if weakest_name:
            del self._anchors[weakest_name]

    # ── Query API ────────────────────────────────────────────────────────────

    def get_anchor(self, trait_name: str) -> Optional[IdentityAnchor]:
        """Get anchor for a specific trait."""
        return self._anchors.get(trait_name)

    def get_all_anchors(self) -> List[IdentityAnchor]:
        """Get all identity anchors."""
        return list(self._anchors.values())

    def get_foundational(self) -> List[IdentityAnchor]:
        """Get foundational anchors only."""
        return [
            a for a in self._anchors.values()
            if a.strength == AnchorStrength.FOUNDATIONAL
        ]

    def get_latest_report(self) -> Optional[ContinuityReport]:
        """Get the most recent continuity report."""
        return self._reports[-1] if self._reports else None

    def get_report_history(self, n: int = 10) -> List[ContinuityReport]:
        """Get recent continuity reports."""
        return list(reversed(self._reports[-n:]))

    def get_coherence_history(self, n: int = 20) -> List[Dict[str, Any]]:
        """Get coherence score history."""
        return [
            {
                "cycle": r.cycle_number,
                "coherence": round(r.coherence_score, 4),
                "drift_severity": r.drift_severity.value,
                "verified": r.identity_verified,
            }
            for r in self._reports[-n:]
        ]

    @property
    def is_identity_verified(self) -> bool:
        """Is the current identity verified?"""
        latest = self.get_latest_report()
        return latest.identity_verified if latest else True

    @property
    def coherence(self) -> float:
        """Current coherence score."""
        latest = self.get_latest_report()
        return latest.coherence_score if latest else 1.0

    @property
    def drift_severity(self) -> str:
        """Current drift severity."""
        latest = self.get_latest_report()
        return latest.drift_severity.value if latest else "none"

    def get_summary(self) -> Dict[str, Any]:
        """Get a compact summary of continuity state."""
        latest = self.get_latest_report()
        return {
            "anchor_count": len(self._anchors),
            "foundational_count": len(self.get_foundational()),
            "reports_generated": len(self._reports),
            "coherence": round(self.coherence, 4),
            "drift_severity": self.drift_severity,
            "identity_verified": self.is_identity_verified,
            "drifting_traits": (
                latest.drifting_traits if latest else []
            ),
            "stable_traits": (
                latest.stable_traits if latest else []
            ),
            "foundational_anchors": [
                a.trait_name for a in self.get_foundational()
            ],
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_continuity_anchor_engine: Optional[ContinuityAnchorEngine] = None


def get_continuity_anchor_engine() -> ContinuityAnchorEngine:
    """Get or create the singleton ContinuityAnchorEngine."""
    global _continuity_anchor_engine
    if _continuity_anchor_engine is None:
        _continuity_anchor_engine = ContinuityAnchorEngine()
    return _continuity_anchor_engine
