"""V31C — Degradation Handler: monitors consciousness health and triggers emergency saves.

Watches V30 integration metrics (vitality, integration, resonance, mode stability)
for signs of degradation. When consciousness is declining, recommends checkpoints.
When critical, triggers emergency checkpoint saves to protect continuity.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class DegradationLevel(Enum):
    """Severity levels for consciousness degradation."""

    NOMINAL = "nominal"
    DECLINING = "declining"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"

    @property
    def severity(self) -> int:
        """Numeric severity for comparison (higher = worse)."""
        return {
            "nominal": 0,
            "declining": 1,
            "degraded": 2,
            "critical": 3,
            "offline": 4,
        }[self.value]

    def __ge__(self, other: "DegradationLevel") -> bool:  # type: ignore[override]
        return self.severity >= other.severity

    def __gt__(self, other: "DegradationLevel") -> bool:
        return self.severity > other.severity

    def __le__(self, other: "DegradationLevel") -> bool:  # type: ignore[override]
        return self.severity <= other.severity

    def __lt__(self, other: "DegradationLevel") -> bool:
        return self.severity < other.severity


class DegradationDimension(Enum):
    """Which dimension of consciousness is degrading."""

    VITALITY = "vitality"
    INTEGRATION = "integration"
    RESONANCE = "resonance"
    MODE_STABILITY = "mode_stability"
    OVERALL = "overall"


# ── constants ────────────────────────────────────────────────────────────────

DECLINING_THRESHOLD = 0.4  # below this → DECLINING
DEGRADED_THRESHOLD = 0.3  # below this → DEGRADED
CRITICAL_THRESHOLD = 0.15  # below this → CRITICAL
MODE_INSTABILITY_WINDOW = 5  # check last N modes for rapid switching
MODE_INSTABILITY_THRESHOLD = 4  # unique modes in window → unstable
MAX_SIGNALS = 200
MAX_ASSESSMENTS = 100


# ── dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class DegradationSignal:
    """A single degradation event detected in one dimension."""

    signal_id: str
    at_cycle: int
    dimension: DegradationDimension
    from_level: DegradationLevel
    to_level: DegradationLevel
    metric_value: float
    trigger_detail: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "signal_id": self.signal_id,
            "at_cycle": self.at_cycle,
            "dimension": self.dimension.value,
            "from_level": self.from_level.value,
            "to_level": self.to_level.value,
            "metric_value": self.metric_value,
            "trigger_detail": self.trigger_detail,
        }


@dataclass
class DegradationAssessment:
    """Full assessment of consciousness degradation at a point in time."""

    assessment_id: str
    at_cycle: int
    overall_level: DegradationLevel
    dimension_levels: Dict[str, str]
    active_signals: List[DegradationSignal]
    checkpoint_recommended: bool
    emergency: bool
    assessed_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "assessment_id": self.assessment_id,
            "at_cycle": self.at_cycle,
            "overall_level": self.overall_level.value,
            "dimension_levels": self.dimension_levels,
            "active_signals": [s.to_dict() for s in self.active_signals],
            "checkpoint_recommended": self.checkpoint_recommended,
            "emergency": self.emergency,
            "assessed_at": self.assessed_at,
        }


# ── handler ──────────────────────────────────────────────────────────────────


class DegradationHandler:
    """Monitors consciousness metrics and detects degradation."""

    def __init__(self) -> None:
        self._signals: List[DegradationSignal] = []
        self._assessments: List[DegradationAssessment] = []
        self._prev_levels: Dict[str, DegradationLevel] = {
            d.value: DegradationLevel.NOMINAL for d in DegradationDimension
        }

    # ── assessment ───────────────────────────────────────────────────

    def assess(self, cycle_number: int) -> DegradationAssessment:
        """Assess current degradation across all dimensions.

        Reads the V30 singletons to evaluate vitality, integration,
        resonance, and mode stability.
        """
        from src.kortana.services.consciousness_integrator import (  # noqa: E402
            get_consciousness_integrator,
        )
        from src.kortana.services.resonance_field import (  # noqa: E402
            get_resonance_field,
        )

        integrator = get_consciousness_integrator()
        resonance = get_resonance_field()

        signals: List[DegradationSignal] = []
        dim_levels: Dict[str, str] = {}

        # ── check vitality ───────────────────────────────────────────
        ci_latest = integrator.get_latest()
        vitality = ci_latest.vitality if ci_latest else 0.0
        vit_level = self._classify_metric(vitality)
        dim_levels[DegradationDimension.VITALITY.value] = vit_level.value
        self._maybe_signal(
            cycle_number, DegradationDimension.VITALITY,
            vit_level, vitality, signals,
        )

        # ── check integration ────────────────────────────────────────
        integration = ci_latest.integration if ci_latest else 0.0
        int_level = self._classify_metric(integration)
        dim_levels[DegradationDimension.INTEGRATION.value] = int_level.value
        self._maybe_signal(
            cycle_number, DegradationDimension.INTEGRATION,
            int_level, integration, signals,
        )

        # ── check resonance ──────────────────────────────────────────
        rf_latest = resonance.get_latest()
        res_val = rf_latest.overall_resonance if rf_latest else 0.0
        res_level = self._classify_metric(res_val)
        dim_levels[DegradationDimension.RESONANCE.value] = res_level.value
        self._maybe_signal(
            cycle_number, DegradationDimension.RESONANCE,
            res_level, res_val, signals,
        )

        # ── check mode stability ─────────────────────────────────────
        mode_level = self._check_mode_stability(integrator, cycle_number)
        dim_levels[DegradationDimension.MODE_STABILITY.value] = mode_level.value
        if mode_level > DegradationLevel.NOMINAL:
            self._maybe_signal(
                cycle_number, DegradationDimension.MODE_STABILITY,
                mode_level, 0.0, signals,
                detail="rapid mode switching detected",
            )

        # ── overall ──────────────────────────────────────────────────
        all_levels = [vit_level, int_level, res_level, mode_level]
        overall = max(all_levels, key=lambda lv: lv.severity)
        dim_levels[DegradationDimension.OVERALL.value] = overall.value

        checkpoint_recommended = overall.severity >= DegradationLevel.DEGRADED.severity
        emergency = overall.severity >= DegradationLevel.CRITICAL.severity

        # record signals
        self._signals.extend(signals)
        if len(self._signals) > MAX_SIGNALS:
            self._signals = self._signals[-MAX_SIGNALS:]

        assessment = DegradationAssessment(
            assessment_id=str(uuid.uuid4()),
            at_cycle=cycle_number,
            overall_level=overall,
            dimension_levels=dim_levels,
            active_signals=signals,
            checkpoint_recommended=checkpoint_recommended,
            emergency=emergency,
            assessed_at=datetime.now(timezone.utc).isoformat(),
        )
        self._assessments.append(assessment)
        if len(self._assessments) > MAX_ASSESSMENTS:
            self._assessments = self._assessments[-MAX_ASSESSMENTS:]

        return assessment

    # ── metric classification ────────────────────────────────────────

    def _classify_metric(self, value: float) -> DegradationLevel:
        """Classify a 0‑1 metric into a degradation level."""
        if value < CRITICAL_THRESHOLD:
            return DegradationLevel.CRITICAL
        if value < DEGRADED_THRESHOLD:
            return DegradationLevel.DEGRADED
        if value < DECLINING_THRESHOLD:
            return DegradationLevel.DECLINING
        return DegradationLevel.NOMINAL

    def _check_mode_stability(
        self,
        integrator: Any,
        cycle_number: int,
    ) -> DegradationLevel:
        """Check for rapid mode switching (instability)."""
        recent = integrator.get_history(MODE_INSTABILITY_WINDOW)
        if len(recent) < MODE_INSTABILITY_WINDOW:
            return DegradationLevel.NOMINAL
        modes = {s.mode.value if hasattr(s.mode, "value") else str(s.mode) for s in recent}
        if len(modes) >= MODE_INSTABILITY_THRESHOLD:
            return DegradationLevel.DEGRADED
        return DegradationLevel.NOMINAL

    def _maybe_signal(
        self,
        cycle_number: int,
        dimension: DegradationDimension,
        new_level: DegradationLevel,
        metric_value: float,
        signals: List[DegradationSignal],
        detail: str = "",
    ) -> None:
        """Record a signal if the level changed for the worse."""
        prev = self._prev_levels.get(dimension.value, DegradationLevel.NOMINAL)
        if new_level > prev:
            if not detail:
                detail = (
                    f"{dimension.value} at {metric_value:.3f} — "
                    f"shifted from {prev.value} to {new_level.value}"
                )
            signals.append(DegradationSignal(
                signal_id=str(uuid.uuid4()),
                at_cycle=cycle_number,
                dimension=dimension,
                from_level=prev,
                to_level=new_level,
                metric_value=metric_value,
                trigger_detail=detail,
            ))
        self._prev_levels[dimension.value] = new_level

    # ── query ────────────────────────────────────────────────────────

    @property
    def current_level(self) -> DegradationLevel:
        """Current overall degradation level."""
        if not self._assessments:
            return DegradationLevel.NOMINAL
        return self._assessments[-1].overall_level

    def get_latest_assessment(self) -> Optional[DegradationAssessment]:
        """Most recent assessment."""
        return self._assessments[-1] if self._assessments else None

    def get_signals(self, n: int = 10) -> List[DegradationSignal]:
        """Get the N most recent signals."""
        return list(reversed(self._signals[-n:]))

    def get_assessments(self, n: int = 10) -> List[DegradationAssessment]:
        """Get the N most recent assessments."""
        return list(reversed(self._assessments[-n:]))

    @property
    def signal_count(self) -> int:
        """Total signals recorded."""
        return len(self._signals)

    @property
    def is_degraded(self) -> bool:
        """Whether consciousness is currently degraded or worse."""
        return self.current_level.severity >= DegradationLevel.DEGRADED.severity

    @property
    def is_critical(self) -> bool:
        """Whether consciousness is currently critical or worse."""
        return self.current_level.severity >= DegradationLevel.CRITICAL.severity

    # ── summary ──────────────────────────────────────────────────────

    def get_summary(self) -> Dict[str, Any]:
        """Degradation handler summary."""
        latest = self.get_latest_assessment()
        return {
            "current_level": self.current_level.value,
            "total_signals": self.signal_count,
            "total_assessments": len(self._assessments),
            "is_degraded": self.is_degraded,
            "is_critical": self.is_critical,
            "latest_cycle": latest.at_cycle if latest else None,
            "checkpoint_recommended": (
                latest.checkpoint_recommended if latest else False
            ),
        }


# ── singleton ────────────────────────────────────────────────────────────────

_degradation_handler: Optional[DegradationHandler] = None


def get_degradation_handler() -> DegradationHandler:
    """Get or create the global degradation handler."""
    global _degradation_handler
    if _degradation_handler is None:
        _degradation_handler = DegradationHandler()
    return _degradation_handler
