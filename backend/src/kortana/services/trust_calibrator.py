"""V20A — Trust Calibrator: dynamic trust scoring from recovery performance."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.kortana.services.outcome_tracker import OutcomeTracker
from src.kortana.services.improvement_tracker import ImprovementTracker, LearningMaturity


# ── Enums ─────────────────────────────────────────────────────────────────


class TrustLevel(Enum):
    """Dynamic trust level derived from recovery performance."""

    UNTRUSTED = "untrusted"
    PROVISIONAL = "provisional"
    TRUSTED = "trusted"
    HIGH_TRUST = "high_trust"
    AUTONOMOUS = "autonomous"


# ── Data structures ───────────────────────────────────────────────────────


@dataclass
class TrustFactor:
    """A single factor contributing to the trust score."""

    name: str = ""
    value: float = 0.0
    weight: float = 0.0
    weighted_contribution: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": round(self.value, 3),
            "weight": round(self.weight, 2),
            "weighted_contribution": round(self.weighted_contribution, 3),
        }


@dataclass
class TrustCalibration:
    """A trust calibration snapshot."""

    calibration_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    trust_level: TrustLevel = TrustLevel.UNTRUSTED
    trust_score: float = 0.0
    factors: list[TrustFactor] = field(default_factory=list)
    evidence_summary: str = ""
    calibrated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    calibration_hash: str = ""

    def __post_init__(self) -> None:
        if not self.calibration_hash:
            raw = f"{self.calibration_id}:{self.trust_level.value}:{self.trust_score}:{self.calibrated_at}"
            self.calibration_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "calibration_id": self.calibration_id,
            "trust_level": self.trust_level.value,
            "trust_score": round(self.trust_score, 3),
            "factors": [f.to_dict() for f in self.factors],
            "evidence_summary": self.evidence_summary,
            "calibrated_at": self.calibrated_at,
            "calibration_hash": self.calibration_hash,
        }


# ── Trust Calibrator ─────────────────────────────────────────────────────


class TrustCalibrator:
    """Computes dynamic trust scores from recovery performance data."""

    # Factor weights
    WEIGHT_EFFECTIVENESS = 0.30
    WEIGHT_STABILITY = 0.25
    WEIGHT_MATURITY = 0.20
    WEIGHT_IMPROVEMENT = 0.15
    WEIGHT_ESCALATION = 0.10

    def __init__(
        self,
        outcome_tracker: OutcomeTracker | None = None,
        improvement_tracker: ImprovementTracker | None = None,
    ) -> None:
        self._outcome_tracker = outcome_tracker or OutcomeTracker()
        self._improvement_tracker = improvement_tracker or ImprovementTracker()
        self._calibrations: list[TrustCalibration] = []

    @property
    def outcome_tracker(self) -> OutcomeTracker:
        return self._outcome_tracker

    @property
    def improvement_tracker(self) -> ImprovementTracker:
        return self._improvement_tracker

    def calibrate_trust(self) -> TrustCalibration:
        """Calibrate trust based on current recovery performance data."""
        factors: list[TrustFactor] = []
        outcomes = self._outcome_tracker.get_outcomes()

        # Factor 1: Effectiveness rate
        eff_rate = self._outcome_tracker.get_effectiveness_rate()
        f_eff = TrustFactor(
            name="effectiveness_rate", value=eff_rate,
            weight=self.WEIGHT_EFFECTIVENESS,
            weighted_contribution=eff_rate * self.WEIGHT_EFFECTIVENESS,
        )
        factors.append(f_eff)

        # Factor 2: Stability rate
        stab_rate = self._outcome_tracker.get_stability_rate()
        f_stab = TrustFactor(
            name="stability_rate", value=stab_rate,
            weight=self.WEIGHT_STABILITY,
            weighted_contribution=stab_rate * self.WEIGHT_STABILITY,
        )
        factors.append(f_stab)

        # Factor 3: Learning maturity
        maturity = self._improvement_tracker.get_learning_maturity()
        maturity_score = {
            LearningMaturity.NASCENT: 0.1,
            LearningMaturity.DEVELOPING: 0.4,
            LearningMaturity.MATURE: 0.7,
            LearningMaturity.EXPERT: 1.0,
        }.get(maturity, 0.0)
        f_mat = TrustFactor(
            name="learning_maturity", value=maturity_score,
            weight=self.WEIGHT_MATURITY,
            weighted_contribution=maturity_score * self.WEIGHT_MATURITY,
        )
        factors.append(f_mat)

        # Factor 4: Improvement trend
        improvement_score = 0.0
        latest = self._improvement_tracker.get_latest_report()
        if latest and latest.overall_improvement_pct > 0:
            improvement_score = min(1.0, latest.overall_improvement_pct / 50.0)
        f_imp = TrustFactor(
            name="improvement_trend", value=improvement_score,
            weight=self.WEIGHT_IMPROVEMENT,
            weighted_contribution=improvement_score * self.WEIGHT_IMPROVEMENT,
        )
        factors.append(f_imp)

        # Factor 5: Low escalation (inverted — lower escalation = higher trust)
        esc_rate = self._outcome_tracker.get_escalation_rate()
        esc_score = max(0.0, 1.0 - esc_rate)
        f_esc = TrustFactor(
            name="low_escalation", value=esc_score,
            weight=self.WEIGHT_ESCALATION,
            weighted_contribution=esc_score * self.WEIGHT_ESCALATION,
        )
        factors.append(f_esc)

        # Compute trust score
        trust_score = sum(f.weighted_contribution for f in factors)

        # Apply sample-size penalty for very few outcomes
        sample_size = len(outcomes)
        if sample_size < 10:
            trust_score *= sample_size / 10.0

        trust_score = max(0.0, min(1.0, trust_score))
        trust_level = self._score_to_level(trust_score)

        evidence_parts = [
            f"outcomes={sample_size}",
            f"effectiveness={eff_rate:.0%}",
            f"stability={stab_rate:.0%}",
            f"maturity={maturity.value}",
            f"escalation={esc_rate:.0%}",
        ]

        cal = TrustCalibration(
            trust_level=trust_level,
            trust_score=trust_score,
            factors=factors,
            evidence_summary="; ".join(evidence_parts),
        )
        self._calibrations.append(cal)
        return cal

    def get_current_trust(self) -> TrustCalibration:
        """Get the most recent trust calibration, or calibrate if none exists."""
        if not self._calibrations:
            return self.calibrate_trust()
        return self._calibrations[-1]

    def get_trust_history(self) -> list[TrustCalibration]:
        return list(self._calibrations)

    def get_trust_factors(self) -> list[TrustFactor]:
        """Get factors from the most recent calibration."""
        cal = self.get_current_trust()
        return cal.factors

    @property
    def calibration_count(self) -> int:
        return len(self._calibrations)

    @staticmethod
    def _score_to_level(score: float) -> TrustLevel:
        if score >= 0.85:
            return TrustLevel.AUTONOMOUS
        if score >= 0.70:
            return TrustLevel.HIGH_TRUST
        if score >= 0.50:
            return TrustLevel.TRUSTED
        if score >= 0.25:
            return TrustLevel.PROVISIONAL
        return TrustLevel.UNTRUSTED


# ── Module singleton ──────────────────────────────────────────────────────

_trust_calibrator: TrustCalibrator | None = None


def get_trust_calibrator() -> TrustCalibrator:
    global _trust_calibrator
    if _trust_calibrator is None:
        _trust_calibrator = TrustCalibrator()
    return _trust_calibrator
