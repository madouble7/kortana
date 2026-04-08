"""V20B — Autonomy Adjuster: dynamic autonomy threshold adjustment."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.kortana.services.trust_calibrator import TrustCalibrator, TrustLevel


# ── Data structures ───────────────────────────────────────────────────────


@dataclass
class AutonomyThreshold:
    """Autonomy thresholds for a task category."""

    threshold_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    category: str = ""
    auto_threshold: float = 0.0
    ho_threshold: float = 0.0
    approval_threshold: float = 0.0
    trust_level_required: TrustLevel = TrustLevel.PROVISIONAL
    reason: str = ""
    adjusted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    threshold_hash: str = ""

    def __post_init__(self) -> None:
        if not self.threshold_hash:
            raw = f"{self.threshold_id}:{self.category}:{self.auto_threshold}:{self.adjusted_at}"
            self.threshold_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "threshold_id": self.threshold_id,
            "category": self.category,
            "auto_threshold": round(self.auto_threshold, 3),
            "ho_threshold": round(self.ho_threshold, 3),
            "approval_threshold": round(self.approval_threshold, 3),
            "trust_level_required": self.trust_level_required.value,
            "reason": self.reason,
            "adjusted_at": self.adjusted_at,
            "threshold_hash": self.threshold_hash,
        }


# ── Default thresholds ───────────────────────────────────────────────────

_DEFAULT_CATEGORIES: dict[str, dict[str, float]] = {
    "reconciliation": {"auto": 0.50, "ho": 0.30, "approval": 0.10},
    "deployment": {"auto": 0.70, "ho": 0.50, "approval": 0.30},
    "rollback": {"auto": 0.60, "ho": 0.40, "approval": 0.20},
    "config_change": {"auto": 0.55, "ho": 0.35, "approval": 0.15},
    "security_action": {"auto": 0.80, "ho": 0.60, "approval": 0.40},
}

# Trust-level multipliers (higher trust = wider autonomy window)
_TRUST_MULTIPLIERS: dict[TrustLevel, float] = {
    TrustLevel.UNTRUSTED: 0.5,
    TrustLevel.PROVISIONAL: 0.7,
    TrustLevel.TRUSTED: 1.0,
    TrustLevel.HIGH_TRUST: 1.2,
    TrustLevel.AUTONOMOUS: 1.5,
}


# ── Autonomy Adjuster ────────────────────────────────────────────────────


class AutonomyAdjuster:
    """Adjusts autonomy thresholds based on trust calibration."""

    def __init__(self, calibrator: TrustCalibrator | None = None) -> None:
        self._calibrator = calibrator or TrustCalibrator()
        self._thresholds: dict[str, AutonomyThreshold] = {}
        self._history: list[dict[str, Any]] = []

    @property
    def calibrator(self) -> TrustCalibrator:
        return self._calibrator

    def adjust_thresholds(self) -> dict[str, AutonomyThreshold]:
        """Recalculate all thresholds based on current trust level."""
        cal = self._calibrator.get_current_trust()
        multiplier = _TRUST_MULTIPLIERS.get(cal.trust_level, 1.0)

        adjusted: dict[str, AutonomyThreshold] = {}
        for category, defaults in _DEFAULT_CATEGORIES.items():
            # Lower thresholds = easier to auto-execute
            auto_t = max(0.0, min(1.0, defaults["auto"] / multiplier))
            ho_t = max(0.0, min(1.0, defaults["ho"] / multiplier))
            appr_t = max(0.0, min(1.0, defaults["approval"] / multiplier))

            threshold = AutonomyThreshold(
                category=category,
                auto_threshold=auto_t,
                ho_threshold=ho_t,
                approval_threshold=appr_t,
                trust_level_required=cal.trust_level,
                reason=f"Calibrated from trust={cal.trust_score:.3f} ({cal.trust_level.value}), multiplier={multiplier}",
            )
            adjusted[category] = threshold

        self._thresholds = adjusted
        self._history.append({
            "trust_level": cal.trust_level.value,
            "trust_score": round(cal.trust_score, 3),
            "categories_adjusted": len(adjusted),
            "adjusted_at": datetime.now(timezone.utc).isoformat(),
        })
        return adjusted

    def get_current_thresholds(self) -> dict[str, AutonomyThreshold]:
        if not self._thresholds:
            self.adjust_thresholds()
        return self._thresholds

    def get_threshold_for_category(self, category: str) -> AutonomyThreshold | None:
        thresholds = self.get_current_thresholds()
        return thresholds.get(category)

    def should_auto_execute(self, category: str, confidence: float) -> bool:
        """Determine if an action should auto-execute given its confidence score."""
        threshold = self.get_threshold_for_category(category)
        if threshold is None:
            return False
        return confidence >= threshold.auto_threshold

    def get_execution_mode(self, category: str, confidence: float) -> str:
        """Get execution mode: 'auto', 'ho', or 'approval'."""
        threshold = self.get_threshold_for_category(category)
        if threshold is None:
            return "approval"
        if confidence >= threshold.auto_threshold:
            return "auto"
        if confidence >= threshold.ho_threshold:
            return "ho"
        return "approval"

    def get_adjustment_history(self) -> list[dict[str, Any]]:
        return list(self._history)

    @property
    def threshold_count(self) -> int:
        return len(self._thresholds)


# ── Module singleton ──────────────────────────────────────────────────────

_autonomy_adjuster: AutonomyAdjuster | None = None


def get_autonomy_adjuster() -> AutonomyAdjuster:
    global _autonomy_adjuster
    if _autonomy_adjuster is None:
        _autonomy_adjuster = AutonomyAdjuster()
    return _autonomy_adjuster
