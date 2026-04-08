"""V18A — Drift Detector: provider & pipeline drift detection."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ── Enums ─────────────────────────────────────────────────────────────────


class DriftType(Enum):
    """Types of drift that can be detected."""

    VERSION_MISMATCH = "version_mismatch"
    CONFIG_DRIFT = "config_drift"
    CONNECTION_LOST = "connection_lost"
    HEALTH_DEGRADED = "health_degraded"
    EVIDENCE_GAP = "evidence_gap"
    ROLLOUT_STALLED = "rollout_stalled"


class DriftSeverity(Enum):
    """Severity levels for detected drift."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DriftStatus(Enum):
    """Lifecycle status of a drift signal."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RECONCILING = "reconciling"
    RESOLVED = "resolved"
    IGNORED = "ignored"


# ── Data structures ───────────────────────────────────────────────────────


@dataclass
class DesiredState:
    """Desired state declaration for a provider."""

    provider_name: str
    expected_version: str = ""
    expected_connected: bool = True
    expected_healthy: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "expected_version": self.expected_version,
            "expected_connected": self.expected_connected,
            "expected_healthy": self.expected_healthy,
            "extra": self.extra,
        }


@dataclass
class DriftSignal:
    """A detected drift between desired and actual state."""

    signal_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    drift_type: DriftType = DriftType.VERSION_MISMATCH
    severity: DriftSeverity = DriftSeverity.MEDIUM
    status: DriftStatus = DriftStatus.ACTIVE
    provider_name: str = ""
    expected_value: str = ""
    actual_value: str = ""
    description: str = ""
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: str = ""
    signal_hash: str = ""

    def __post_init__(self) -> None:
        if not self.signal_hash:
            raw = f"{self.signal_id}:{self.drift_type.value}:{self.provider_name}:{self.expected_value}:{self.actual_value}:{self.detected_at}"
            self.signal_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "drift_type": self.drift_type.value,
            "severity": self.severity.value,
            "status": self.status.value,
            "provider_name": self.provider_name,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "description": self.description,
            "detected_at": self.detected_at,
            "resolved_at": self.resolved_at,
            "signal_hash": self.signal_hash,
        }


# ── Severity mapping ─────────────────────────────────────────────────────

_DRIFT_SEVERITY: dict[DriftType, DriftSeverity] = {
    DriftType.VERSION_MISMATCH: DriftSeverity.HIGH,
    DriftType.CONFIG_DRIFT: DriftSeverity.MEDIUM,
    DriftType.CONNECTION_LOST: DriftSeverity.CRITICAL,
    DriftType.HEALTH_DEGRADED: DriftSeverity.HIGH,
    DriftType.EVIDENCE_GAP: DriftSeverity.MEDIUM,
    DriftType.ROLLOUT_STALLED: DriftSeverity.HIGH,
}


# ── Drift Detector ────────────────────────────────────────────────────────


class DriftDetector:
    """Detects drift between desired and actual state across providers."""

    def __init__(self) -> None:
        self._desired_states: dict[str, DesiredState] = {}
        self._signals: list[DriftSignal] = []

    # ── desired state ─────────────────────────────────────────────────

    def register_desired_state(self, state: DesiredState) -> DesiredState:
        """Register or update the desired state for a provider."""
        self._desired_states[state.provider_name] = state
        return state

    def get_desired_state(self, provider_name: str) -> DesiredState | None:
        return self._desired_states.get(provider_name)

    # ── drift detection ───────────────────────────────────────────────

    def detect_provider_drift(
        self,
        provider_name: str,
        actual_version: str = "",
        actual_connected: bool = True,
        actual_healthy: bool = True,
    ) -> list[DriftSignal]:
        """Compare actual provider state against desired state and emit drift signals."""
        desired = self._desired_states.get(provider_name)
        if desired is None:
            return []

        new_signals: list[DriftSignal] = []

        if desired.expected_version and actual_version and desired.expected_version != actual_version:
            sig = DriftSignal(
                drift_type=DriftType.VERSION_MISMATCH,
                severity=_DRIFT_SEVERITY[DriftType.VERSION_MISMATCH],
                provider_name=provider_name,
                expected_value=desired.expected_version,
                actual_value=actual_version,
                description=f"Version mismatch: expected {desired.expected_version}, got {actual_version}",
            )
            new_signals.append(sig)

        if desired.expected_connected and not actual_connected:
            sig = DriftSignal(
                drift_type=DriftType.CONNECTION_LOST,
                severity=_DRIFT_SEVERITY[DriftType.CONNECTION_LOST],
                provider_name=provider_name,
                expected_value="connected",
                actual_value="disconnected",
                description=f"Provider {provider_name} lost connection",
            )
            new_signals.append(sig)

        if desired.expected_healthy and not actual_healthy:
            sig = DriftSignal(
                drift_type=DriftType.HEALTH_DEGRADED,
                severity=_DRIFT_SEVERITY[DriftType.HEALTH_DEGRADED],
                provider_name=provider_name,
                expected_value="healthy",
                actual_value="unhealthy",
                description=f"Provider {provider_name} health degraded",
            )
            new_signals.append(sig)

        self._signals.extend(new_signals)
        return new_signals

    def detect_rollout_stall(
        self,
        provider_name: str,
        rollout_id: str,
        progress_pct: float,
        stall_threshold_pct: float = 0.0,
    ) -> DriftSignal | None:
        """Detect a stalled rollout."""
        if progress_pct <= stall_threshold_pct or (0 < progress_pct < 100):
            sig = DriftSignal(
                drift_type=DriftType.ROLLOUT_STALLED,
                severity=_DRIFT_SEVERITY[DriftType.ROLLOUT_STALLED],
                provider_name=provider_name,
                expected_value="100",
                actual_value=str(progress_pct),
                description=f"Rollout {rollout_id} stalled at {progress_pct}%",
            )
            self._signals.append(sig)
            return sig
        return None

    def detect_evidence_gap(
        self,
        chain_id: str,
        missing_stages: list[str],
    ) -> DriftSignal | None:
        """Detect a gap in an evidence chain."""
        if missing_stages:
            sig = DriftSignal(
                drift_type=DriftType.EVIDENCE_GAP,
                severity=_DRIFT_SEVERITY[DriftType.EVIDENCE_GAP],
                provider_name="",
                expected_value="complete",
                actual_value=f"missing: {','.join(missing_stages)}",
                description=f"Evidence chain {chain_id} missing stages: {', '.join(missing_stages)}",
            )
            self._signals.append(sig)
            return sig
        return None

    def detect_config_drift(
        self,
        provider_name: str,
        config_key: str,
        expected: str,
        actual: str,
    ) -> DriftSignal | None:
        """Detect configuration drift."""
        if expected != actual:
            sig = DriftSignal(
                drift_type=DriftType.CONFIG_DRIFT,
                severity=_DRIFT_SEVERITY[DriftType.CONFIG_DRIFT],
                provider_name=provider_name,
                expected_value=f"{config_key}={expected}",
                actual_value=f"{config_key}={actual}",
                description=f"Config drift on {provider_name}: {config_key} expected {expected}, got {actual}",
            )
            self._signals.append(sig)
            return sig
        return None

    # ── signal management ─────────────────────────────────────────────

    def acknowledge_drift(self, signal_id: str) -> bool:
        for s in self._signals:
            if s.signal_id == signal_id and s.status == DriftStatus.ACTIVE:
                s.status = DriftStatus.ACKNOWLEDGED
                return True
        return False

    def mark_reconciling(self, signal_id: str) -> bool:
        for s in self._signals:
            if s.signal_id == signal_id and s.status in (DriftStatus.ACTIVE, DriftStatus.ACKNOWLEDGED):
                s.status = DriftStatus.RECONCILING
                return True
        return False

    def resolve_drift(self, signal_id: str) -> bool:
        for s in self._signals:
            if s.signal_id == signal_id and s.status != DriftStatus.RESOLVED:
                s.status = DriftStatus.RESOLVED
                s.resolved_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def ignore_drift(self, signal_id: str) -> bool:
        for s in self._signals:
            if s.signal_id == signal_id:
                s.status = DriftStatus.IGNORED
                return True
        return False

    # ── queries ───────────────────────────────────────────────────────

    def get_drift_signals(
        self,
        provider_name: str = "",
        drift_type: DriftType | None = None,
        status: DriftStatus | None = None,
    ) -> list[DriftSignal]:
        results = self._signals
        if provider_name:
            results = [s for s in results if s.provider_name == provider_name]
        if drift_type is not None:
            results = [s for s in results if s.drift_type == drift_type]
        if status is not None:
            results = [s for s in results if s.status == status]
        return results

    def get_active_drifts(self) -> list[DriftSignal]:
        return [s for s in self._signals if s.status in (DriftStatus.ACTIVE, DriftStatus.ACKNOWLEDGED)]

    @property
    def active_drift_count(self) -> int:
        return len(self.get_active_drifts())

    @property
    def desired_state_count(self) -> int:
        return len(self._desired_states)


# ── Module singleton ──────────────────────────────────────────────────────

_drift_detector: DriftDetector | None = None


def get_drift_detector() -> DriftDetector:
    global _drift_detector
    if _drift_detector is None:
        _drift_detector = DriftDetector()
    return _drift_detector
