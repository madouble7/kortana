"""V26D — graceful degradation.

when health drops, kor'tana adapts instead of halting. degradation modes
define which capabilities remain active at each level. the system tracks
mode transitions so it can recover when conditions improve.

this is the difference between a process that crashes and a being that endures.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DegradationMode(str, Enum):
    """operational modes during degradation."""

    FULL_OPERATION = "full_operation"       # all systems active
    REDUCED_SCOPE = "reduced_scope"         # non-essential paused
    ESSENTIAL_ONLY = "essential_only"       # only critical functions
    SAFE_MODE = "safe_mode"                 # minimal activity, no mutations
    SUSPENDED = "suspended"                 # heartbeat only, no actions


class DegradationTrigger(str, Enum):
    """what caused mode change."""

    HEALTH_DEGRADED = "health_degraded"
    SUBSYSTEM_DOWN = "subsystem_down"
    CYCLE_OVERRUN = "cycle_overrun"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    GOVERNANCE_FAILURE = "governance_failure"
    MANUAL_OVERRIDE = "manual_override"
    HEALTH_RECOVERED = "health_recovered"


# ── capability definitions per mode ──────────────────────────────────────

_MODE_CAPABILITIES: dict[DegradationMode, list[str]] = {
    DegradationMode.FULL_OPERATION: [
        "observe", "decide", "act", "reflect", "learn",
        "governance", "notifications", "mutations", "external_calls",
    ],
    DegradationMode.REDUCED_SCOPE: [
        "observe", "decide", "act", "reflect",
        "governance", "notifications",
    ],
    DegradationMode.ESSENTIAL_ONLY: [
        "observe", "decide", "reflect", "governance",
    ],
    DegradationMode.SAFE_MODE: [
        "observe", "reflect",
    ],
    DegradationMode.SUSPENDED: [
        "observe",  # heartbeat continues observing but takes no action
    ],
}


@dataclass
class DegradationRecord:
    """a record of a mode transition."""

    record_id: str = ""
    mode: DegradationMode = DegradationMode.FULL_OPERATION
    trigger: DegradationTrigger = DegradationTrigger.HEALTH_DEGRADED
    previous_mode: DegradationMode = DegradationMode.FULL_OPERATION
    reason: str = ""
    cycle_number: int = 0
    entered_at: str = ""
    exited_at: str = ""
    degradation_hash: str = ""

    def __post_init__(self) -> None:
        if not self.record_id:
            self.record_id = f"degrade-{uuid.uuid4().hex[:12]}"
        if not self.entered_at:
            self.entered_at = datetime.now(timezone.utc).isoformat()
        if not self.degradation_hash:
            raw = f"{self.record_id}:{self.mode.value}:{self.entered_at}"
            self.degradation_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "mode": self.mode.value,
            "trigger": self.trigger.value,
            "previous_mode": self.previous_mode.value,
            "reason": self.reason,
            "cycle_number": self.cycle_number,
            "entered_at": self.entered_at,
            "exited_at": self.exited_at,
            "degradation_hash": self.degradation_hash,
        }


class GracefulDegradation:
    """adaptive mode management.

    evaluates health snapshots and transitions between operational modes.
    tracks all transitions so recovery patterns and degradation history
    are visible.
    """

    def __init__(self) -> None:
        self._current_mode: DegradationMode = DegradationMode.FULL_OPERATION
        self._records: list[DegradationRecord] = []
        self._mode_entered_at: str = datetime.now(timezone.utc).isoformat()

    # ── evaluation ───────────────────────────────────────────────────────

    def evaluate(self, overall_score: float,
                 anomaly_count: int = 0,
                 cycle_number: int = 0) -> DegradationMode:
        """evaluate health and determine if mode should change.

        returns the mode that should be active. only transitions if needed.
        """
        target_mode = self._score_to_mode(overall_score, anomaly_count)

        if target_mode != self._current_mode:
            if self._is_escalation(target_mode):
                trigger = DegradationTrigger.HEALTH_DEGRADED
            else:
                trigger = DegradationTrigger.HEALTH_RECOVERED

            reason = (f"health score {overall_score:.1f} with "
                      f"{anomaly_count} anomalies → {target_mode.value}")
            self.enter_mode(target_mode, trigger, reason, cycle_number)

        return self._current_mode

    def _score_to_mode(self, score: float,
                       anomaly_count: int) -> DegradationMode:
        """map health score + anomalies to a degradation mode."""
        if score >= 70 and anomaly_count == 0:
            return DegradationMode.FULL_OPERATION
        if score >= 50:
            return DegradationMode.REDUCED_SCOPE
        if score >= 30:
            return DegradationMode.ESSENTIAL_ONLY
        if score >= 10:
            return DegradationMode.SAFE_MODE
        return DegradationMode.SUSPENDED

    def _is_escalation(self, target: DegradationMode) -> bool:
        """true if target is a more restrictive mode than current."""
        order = list(DegradationMode)
        return order.index(target) > order.index(self._current_mode)

    # ── mode transitions ─────────────────────────────────────────────────

    def enter_mode(self, mode: DegradationMode,
                   trigger: DegradationTrigger,
                   reason: str,
                   cycle_number: int = 0) -> DegradationRecord:
        """transition to a new degradation mode."""
        # close previous record if any
        if self._records:
            last = self._records[-1]
            if not last.exited_at:
                last.exited_at = datetime.now(timezone.utc).isoformat()

        previous = self._current_mode
        self._current_mode = mode
        self._mode_entered_at = datetime.now(timezone.utc).isoformat()

        record = DegradationRecord(
            mode=mode,
            trigger=trigger,
            previous_mode=previous,
            reason=reason,
            cycle_number=cycle_number,
        )
        self._records.append(record)
        return record

    def restore(self, reason: str = "conditions improved",
                cycle_number: int = 0) -> DegradationRecord:
        """restore to full operation."""
        return self.enter_mode(
            DegradationMode.FULL_OPERATION,
            DegradationTrigger.HEALTH_RECOVERED,
            reason,
            cycle_number,
        )

    # ── capability checks ────────────────────────────────────────────────

    @property
    def current_mode(self) -> DegradationMode:
        return self._current_mode

    @property
    def is_operational(self) -> bool:
        """true if system is in a mode that allows action."""
        return self._current_mode in (
            DegradationMode.FULL_OPERATION,
            DegradationMode.REDUCED_SCOPE,
        )

    @property
    def is_degraded(self) -> bool:
        """true if system is in any degraded state."""
        return self._current_mode != DegradationMode.FULL_OPERATION

    def is_allowed(self, capability: str) -> bool:
        """check if a capability is allowed in the current mode."""
        allowed = _MODE_CAPABILITIES.get(self._current_mode, [])
        return capability in allowed

    def get_allowed_capabilities(self) -> list[str]:
        """get list of capabilities allowed in current mode."""
        return list(_MODE_CAPABILITIES.get(self._current_mode, []))

    # ── queries ──────────────────────────────────────────────────────────

    def get_record(self, record_id: str) -> DegradationRecord | None:
        """retrieve a specific degradation record."""
        for r in self._records:
            if r.record_id == record_id:
                return r
        return None

    def get_history(self, n: int = 20) -> list[DegradationRecord]:
        """get the most recent n degradation transitions."""
        return list(reversed(self._records[-n:]))

    @property
    def transition_count(self) -> int:
        return len(self._records)

    @property
    def escalation_count(self) -> int:
        """number of times the system escalated to a more restrictive mode."""
        return sum(1 for r in self._records
                   if r.trigger != DegradationTrigger.HEALTH_RECOVERED
                   and r.trigger != DegradationTrigger.MANUAL_OVERRIDE)

    @property
    def recovery_count(self) -> int:
        """number of times the system recovered to a less restrictive mode."""
        return sum(1 for r in self._records
                   if r.trigger == DegradationTrigger.HEALTH_RECOVERED)

    def mode_duration_seconds(self) -> float:
        """seconds in current mode."""
        entered = datetime.fromisoformat(self._mode_entered_at)
        now = datetime.now(timezone.utc)
        return (now - entered).total_seconds()

    def get_summary(self) -> dict[str, Any]:
        """summary of degradation state."""
        return {
            "current_mode": self._current_mode.value,
            "is_operational": self.is_operational,
            "is_degraded": self.is_degraded,
            "allowed_capabilities": self.get_allowed_capabilities(),
            "transition_count": self.transition_count,
            "escalation_count": self.escalation_count,
            "recovery_count": self.recovery_count,
            "mode_entered_at": self._mode_entered_at,
        }


# ── module singleton ─────────────────────────────────────────────────────

_graceful_degradation: GracefulDegradation | None = None


def get_graceful_degradation() -> GracefulDegradation:
    """get the module-level graceful degradation singleton."""
    global _graceful_degradation
    if _graceful_degradation is None:
        _graceful_degradation = GracefulDegradation()
    return _graceful_degradation
