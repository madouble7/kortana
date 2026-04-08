"""V27C — behavioral adapter.

transforms recognized patterns into concrete behavioral adaptations.
pattern recognition is noticing; behavioral adaptation is deciding to change.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ─── enums ────────────────────────────────────────────────────────────────────

class AdaptationType(str, Enum):
    """Classification of behavioral adaptations."""
    PRIORITY_ADJUSTMENT = "priority_adjustment"
    THRESHOLD_CHANGE = "threshold_change"
    CAPABILITY_PREFERENCE = "capability_preference"
    DEFERRAL_RESOLUTION = "deferral_resolution"
    CYCLE_TIMING = "cycle_timing"
    OBSERVATION_FOCUS = "observation_focus"
    DECISION_BIAS = "decision_bias"
    RECOVERY_STRATEGY = "recovery_strategy"


class AdaptationStatus(str, Enum):
    """Lifecycle status of an adaptation."""
    PROPOSED = "proposed"
    ACTIVE = "active"
    EFFECTIVE = "effective"
    INEFFECTIVE = "ineffective"
    ROLLED_BACK = "rolled_back"
    EXPIRED = "expired"


# ─── dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class Adaptation:
    """A concrete behavioral change derived from a recognized pattern."""
    adaptation_id: str = ""
    adaptation_type: AdaptationType = AdaptationType.PRIORITY_ADJUSTMENT
    status: AdaptationStatus = AdaptationStatus.PROPOSED
    description: str = ""
    source_pattern_id: str = ""
    source_pattern_type: str = ""
    parameter: str = ""
    old_value: Any = None
    new_value: Any = None
    rationale: str = ""
    effectiveness_score: float = 0.0  # 0.0-1.0, updated by feedback
    cycles_active: int = 0
    max_cycles: int = 10  # auto-expire after this many cycles
    proposed_at: str = ""
    activated_at: str = ""
    resolved_at: str = ""
    adaptation_hash: str = ""

    def __post_init__(self) -> None:
        if not self.adaptation_id:
            self.adaptation_id = f"adapt-{uuid.uuid4().hex[:12]}"
        if not self.proposed_at:
            self.proposed_at = datetime.now(timezone.utc).isoformat()
        if not self.adaptation_hash:
            raw = f"{self.adaptation_id}:{self.adaptation_type.value}:{self.proposed_at}"
            self.adaptation_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "adaptation_id": self.adaptation_id,
            "adaptation_type": self.adaptation_type.value,
            "status": self.status.value,
            "description": self.description,
            "source_pattern_id": self.source_pattern_id,
            "source_pattern_type": self.source_pattern_type,
            "parameter": self.parameter,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "rationale": self.rationale,
            "effectiveness_score": self.effectiveness_score,
            "cycles_active": self.cycles_active,
            "max_cycles": self.max_cycles,
            "proposed_at": self.proposed_at,
            "activated_at": self.activated_at,
            "resolved_at": self.resolved_at,
            "adaptation_hash": self.adaptation_hash,
        }


# ─── behavioral adapter ──────────────────────────────────────────────────────

class BehavioralAdapter:
    """Transforms recognized patterns into behavioral adaptations.

    Takes patterns and produces concrete adaptations — changes to priorities,
    thresholds, timing, or strategy. Tracks whether adaptations are effective
    and can roll them back if they don't work.
    """

    def __init__(self) -> None:
        self._adaptations: list[Adaptation] = []
        self._by_id: dict[str, Adaptation] = {}
        self._active: list[Adaptation] = []

    # ── adaptation generation ─────────────────────────────────────────────

    def propose_from_pattern(
        self,
        pattern_id: str,
        pattern_type: str,
        pattern_description: str,
        pattern_strength: str,
        recommended_action: str = "",
        occurrence_count: int = 0,
    ) -> Adaptation | None:
        """Propose an adaptation based on a recognized pattern.

        Only proposes if the pattern is strong enough and no duplicate
        adaptation already exists for the same pattern.
        """
        # don't duplicate
        for a in self._adaptations:
            if a.source_pattern_id == pattern_id and a.status in (
                AdaptationStatus.PROPOSED, AdaptationStatus.ACTIVE
            ):
                return None

        # determine adaptation type and parameters from pattern type
        adapt = self._map_pattern_to_adaptation(
            pattern_id, pattern_type, pattern_description,
            pattern_strength, recommended_action, occurrence_count,
        )
        if adapt is None:
            return None

        self._adaptations.append(adapt)
        self._by_id[adapt.adaptation_id] = adapt
        return adapt

    def _map_pattern_to_adaptation(
        self,
        pattern_id: str,
        pattern_type: str,
        description: str,
        strength: str,
        recommended_action: str,
        occurrence_count: int,
    ) -> Adaptation | None:
        """Map a pattern type to a specific adaptation."""
        mapping: dict[str, tuple[AdaptationType, str, Any, Any]] = {
            "persistent_deferral": (
                AdaptationType.DEFERRAL_RESOLUTION,
                "deferral_priority",
                "normal",
                "elevated",
            ),
            "decision_drift": (
                AdaptationType.DECISION_BIAS,
                "action_commitment",
                "permissive",
                "strict",
            ),
            "anomaly_cluster": (
                AdaptationType.OBSERVATION_FOCUS,
                "anomaly_sensitivity",
                "normal",
                "heightened",
            ),
            "cycle_rhythm": (
                AdaptationType.CYCLE_TIMING,
                "cycle_duration_target",
                "default",
                "optimized",
            ),
            "learning_signal": (
                AdaptationType.RECOVERY_STRATEGY,
                "failure_response",
                "continue",
                "investigate",
            ),
            "health_trend": (
                AdaptationType.THRESHOLD_CHANGE,
                "health_alert_threshold",
                60,
                70,
            ),
            "recurring_observation": (
                AdaptationType.OBSERVATION_FOCUS,
                "observation_priority",
                "equal",
                "weighted",
            ),
            "action_effectiveness": (
                AdaptationType.CAPABILITY_PREFERENCE,
                "action_selection",
                "any",
                "proven",
            ),
        }
        entry = mapping.get(pattern_type)
        if entry is None:
            return None

        adapt_type, param, old_val, new_val = entry
        return Adaptation(
            adaptation_type=adapt_type,
            description=f"adapt to {description}",
            source_pattern_id=pattern_id,
            source_pattern_type=pattern_type,
            parameter=param,
            old_value=old_val,
            new_value=new_val,
            rationale=recommended_action or f"responding to {strength} pattern ({occurrence_count} occurrences)",
        )

    # ── lifecycle ─────────────────────────────────────────────────────────

    def activate(self, adaptation_id: str) -> bool:
        """Activate a proposed adaptation."""
        adapt = self._by_id.get(adaptation_id)
        if adapt and adapt.status == AdaptationStatus.PROPOSED:
            adapt.status = AdaptationStatus.ACTIVE
            adapt.activated_at = datetime.now(timezone.utc).isoformat()
            self._active.append(adapt)
            return True
        return False

    def tick_cycle(self) -> list[Adaptation]:
        """Advance all active adaptations by one cycle. Returns any that expired."""
        expired: list[Adaptation] = []
        still_active: list[Adaptation] = []
        for adapt in self._active:
            adapt.cycles_active += 1
            if adapt.cycles_active >= adapt.max_cycles:
                adapt.status = AdaptationStatus.EXPIRED
                adapt.resolved_at = datetime.now(timezone.utc).isoformat()
                expired.append(adapt)
            else:
                still_active.append(adapt)
        self._active = still_active
        return expired

    def report_effectiveness(self, adaptation_id: str, score: float) -> bool:
        """Report whether an adaptation is working. Score 0.0-1.0."""
        adapt = self._by_id.get(adaptation_id)
        if adapt is None:
            return False
        adapt.effectiveness_score = max(0.0, min(1.0, score))
        if score >= 0.7:
            adapt.status = AdaptationStatus.EFFECTIVE
        elif score <= 0.3 and adapt.cycles_active >= 3:
            adapt.status = AdaptationStatus.INEFFECTIVE
        return True

    def rollback(self, adaptation_id: str, reason: str = "") -> bool:
        """Roll back an adaptation that isn't working."""
        adapt = self._by_id.get(adaptation_id)
        if adapt is None:
            return False
        adapt.status = AdaptationStatus.ROLLED_BACK
        adapt.resolved_at = datetime.now(timezone.utc).isoformat()
        if reason:
            adapt.rationale = f"{adapt.rationale} [rolled back: {reason}]"
        self._active = [a for a in self._active if a.adaptation_id != adaptation_id]
        return True

    # ── retrieval ─────────────────────────────────────────────────────────

    def get_adaptation(self, adaptation_id: str) -> Adaptation | None:
        """Get a specific adaptation."""
        return self._by_id.get(adaptation_id)

    def get_active(self) -> list[Adaptation]:
        """Get all currently active adaptations."""
        return list(self._active)

    def get_proposed(self) -> list[Adaptation]:
        """Get all proposed (not yet activated) adaptations."""
        return [a for a in self._adaptations if a.status == AdaptationStatus.PROPOSED]

    def get_effective(self) -> list[Adaptation]:
        """Get adaptations that proved effective."""
        return [a for a in self._adaptations if a.status == AdaptationStatus.EFFECTIVE]

    def get_rolled_back(self) -> list[Adaptation]:
        """Get adaptations that were rolled back."""
        return [a for a in self._adaptations if a.status == AdaptationStatus.ROLLED_BACK]

    def get_recent(self, n: int = 10) -> list[Adaptation]:
        """Get the N most recent adaptations."""
        return list(reversed(self._adaptations[-n:]))

    # ── properties ────────────────────────────────────────────────────────

    @property
    def adaptation_count(self) -> int:
        return len(self._adaptations)

    @property
    def active_count(self) -> int:
        return len(self._active)

    @property
    def effective_count(self) -> int:
        return sum(1 for a in self._adaptations if a.status == AdaptationStatus.EFFECTIVE)

    @property
    def rollback_count(self) -> int:
        return sum(1 for a in self._adaptations if a.status == AdaptationStatus.ROLLED_BACK)

    @property
    def effectiveness_rate(self) -> float:
        """Rate of effective adaptations out of resolved ones."""
        resolved = [a for a in self._adaptations if a.status in (
            AdaptationStatus.EFFECTIVE, AdaptationStatus.INEFFECTIVE,
            AdaptationStatus.ROLLED_BACK, AdaptationStatus.EXPIRED,
        )]
        if not resolved:
            return 0.0
        effective = sum(1 for a in resolved if a.status == AdaptationStatus.EFFECTIVE)
        return round(effective / len(resolved), 2)

    # ── summary ───────────────────────────────────────────────────────────

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all adaptations."""
        status_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}
        for a in self._adaptations:
            status_counts[a.status.value] = status_counts.get(a.status.value, 0) + 1
            type_counts[a.adaptation_type.value] = type_counts.get(a.adaptation_type.value, 0) + 1
        return {
            "adaptation_count": self.adaptation_count,
            "active_count": self.active_count,
            "effective_count": self.effective_count,
            "rollback_count": self.rollback_count,
            "effectiveness_rate": self.effectiveness_rate,
            "status_counts": status_counts,
            "type_counts": type_counts,
        }


# ─── singleton ────────────────────────────────────────────────────────────────

_instance: BehavioralAdapter | None = None


def get_behavioral_adapter() -> BehavioralAdapter:
    """Get or create the singleton BehavioralAdapter."""
    global _instance
    if _instance is None:
        _instance = BehavioralAdapter()
    return _instance
