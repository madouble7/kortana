"""V12B — Key Rotation Infrastructure.

Provides durable key rotation lifecycle management with rotation schedules,
grace periods for zero-downtime rollover, automatic expiration of old
credentials, and a full rotation audit trail.

Integrates with V11A auth providers (APIKeyProvider, ServiceAccountProvider)
to issue new keys and revoke old ones during rotation events.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger("kortana.key_rotation")


# ---------------------------------------------------------------------------
# Rotation state machine
# ---------------------------------------------------------------------------


class RotationState(str, Enum):
    """Lifecycle state of a key rotation schedule."""

    ACTIVE = "active"            # Key is current and valid
    GRACE_PERIOD = "grace"       # Old key still works, new key issued
    EXPIRED = "expired"          # Grace period elapsed, old key revoked
    ROTATED = "rotated"          # Rotation completed successfully
    DISABLED = "disabled"        # Rotation schedule disabled


class RotationEventType(str, Enum):
    """Type of rotation event."""

    SCHEDULED = "scheduled"      # Automatic rotation trigger
    MANUAL = "manual"            # Operator-initiated rotation
    EMERGENCY = "emergency"      # Emergency rotation (compromised key)
    GRACE_EXPIRED = "grace_expired"  # Grace period ended


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class RotationSchedule:
    """Tracks rotation lifecycle for a single key."""

    key_id: str
    provider_type: str                # "api_key" or "service_account"
    operator_id: str
    rotation_interval_hours: int = 720   # 30 days default
    grace_period_hours: int = 24         # 24 hour overlap
    created_at: datetime = field(default_factory=datetime.utcnow)
    next_rotation_at: datetime | None = None
    last_rotated_at: datetime | None = None
    grace_expires_at: datetime | None = None
    state: RotationState = RotationState.ACTIVE
    old_credential_id: str = ""
    new_credential_id: str = ""
    schedule_hash: str = ""

    def __post_init__(self) -> None:
        if self.next_rotation_at is None:
            self.next_rotation_at = self.created_at + timedelta(
                hours=self.rotation_interval_hours
            )
        if not self.schedule_hash:
            self.schedule_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "key_id": self.key_id,
                "provider_type": self.provider_type,
                "operator_id": self.operator_id,
                "created_at": self.created_at.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def is_due(self) -> bool:
        """Whether this key is due for rotation."""
        if self.state != RotationState.ACTIVE:
            return False
        if self.next_rotation_at is None:
            return False
        return datetime.utcnow() >= self.next_rotation_at

    @property
    def is_in_grace_period(self) -> bool:
        """Whether the old key is in a grace period."""
        if self.state != RotationState.GRACE_PERIOD:
            return False
        if self.grace_expires_at is None:
            return False
        return datetime.utcnow() < self.grace_expires_at

    @property
    def is_grace_expired(self) -> bool:
        """Whether the grace period has expired."""
        if self.state != RotationState.GRACE_PERIOD:
            return False
        if self.grace_expires_at is None:
            return False
        return datetime.utcnow() >= self.grace_expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "key_id": self.key_id,
            "provider_type": self.provider_type,
            "operator_id": self.operator_id,
            "rotation_interval_hours": self.rotation_interval_hours,
            "grace_period_hours": self.grace_period_hours,
            "state": self.state.value,
            "next_rotation_at": self.next_rotation_at.isoformat() if self.next_rotation_at else None,
            "last_rotated_at": self.last_rotated_at.isoformat() if self.last_rotated_at else None,
            "grace_expires_at": self.grace_expires_at.isoformat() if self.grace_expires_at else None,
            "old_credential_id": self.old_credential_id,
            "new_credential_id": self.new_credential_id,
            "is_due": self.is_due,
            "is_in_grace_period": self.is_in_grace_period,
            "schedule_hash": self.schedule_hash,
        }


@dataclass
class RotationEvent:
    """Records a single rotation action for audit purposes."""

    event_id: str = field(default_factory=lambda: f"rot_{secrets.token_hex(8)}")
    key_id: str = ""
    event_type: RotationEventType = RotationEventType.SCHEDULED
    old_credential_id: str = ""
    new_credential_id: str = ""
    initiated_by: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: str = ""
    event_hash: str = ""

    def __post_init__(self) -> None:
        if not self.event_hash:
            self.event_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "event_id": self.event_id,
                "key_id": self.key_id,
                "event_type": self.event_type.value,
                "timestamp": self.timestamp.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "key_id": self.key_id,
            "event_type": self.event_type.value,
            "old_credential_id": self.old_credential_id,
            "new_credential_id": self.new_credential_id,
            "initiated_by": self.initiated_by,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "event_hash": self.event_hash,
        }


# ---------------------------------------------------------------------------
# Key rotation manager
# ---------------------------------------------------------------------------


class KeyRotationManager:
    """Manages key rotation schedules and executes rotations.

    Integrates with V11A auth providers to issue new keys and
    revoke old ones during rotation events.  Supports:

    - Scheduled rotation at configurable intervals
    - Grace periods where both old and new keys are valid
    - Manual and emergency rotation triggers
    - Full audit trail of all rotation events
    """

    def __init__(self) -> None:
        self._schedules: dict[str, RotationSchedule] = {}  # key_id → schedule
        self._events: list[RotationEvent] = []

    def schedule_rotation(
        self,
        key_id: str,
        provider_type: str,
        operator_id: str,
        rotation_interval_hours: int = 720,
        grace_period_hours: int = 24,
    ) -> RotationSchedule:
        """Create a rotation schedule for an existing key."""
        schedule = RotationSchedule(
            key_id=key_id,
            provider_type=provider_type,
            operator_id=operator_id,
            rotation_interval_hours=rotation_interval_hours,
            grace_period_hours=grace_period_hours,
        )
        self._schedules[key_id] = schedule
        logger.info(
            "Rotation scheduled: key=%s interval=%dh grace=%dh",
            key_id,
            rotation_interval_hours,
            grace_period_hours,
        )
        return schedule

    def check_due_rotations(self) -> list[RotationSchedule]:
        """Return all schedules that are due for rotation."""
        return [s for s in self._schedules.values() if s.is_due]

    def execute_rotation(
        self,
        key_id: str,
        initiated_by: str,
        event_type: RotationEventType = RotationEventType.SCHEDULED,
    ) -> tuple[RotationEvent | None, str | None]:
        """Execute a key rotation.

        Issues a new key via the auth provider and puts the old key
        into a grace period.  Returns (event, error).
        """
        schedule = self._schedules.get(key_id)
        if schedule is None:
            return None, f"No rotation schedule for key {key_id!r}"

        if schedule.state not in (RotationState.ACTIVE, RotationState.GRACE_PERIOD):
            return None, f"Key {key_id!r} in state {schedule.state.value}, cannot rotate"

        # Issue new key via the appropriate provider
        new_bearer, new_credential_id, error = self._issue_new_key(schedule)
        if error:
            return None, error

        now = datetime.utcnow()
        old_credential_id = schedule.new_credential_id or key_id

        # Update schedule state
        schedule.old_credential_id = old_credential_id
        schedule.new_credential_id = new_credential_id
        schedule.state = RotationState.GRACE_PERIOD
        schedule.grace_expires_at = now + timedelta(hours=schedule.grace_period_hours)
        schedule.last_rotated_at = now
        schedule.next_rotation_at = now + timedelta(hours=schedule.rotation_interval_hours)

        # Record event
        event = RotationEvent(
            key_id=key_id,
            event_type=event_type,
            old_credential_id=old_credential_id,
            new_credential_id=new_credential_id,
            initiated_by=initiated_by,
            details=f"Rotated {schedule.provider_type} key for {schedule.operator_id}. "
                    f"Grace period: {schedule.grace_period_hours}h",
        )
        self._events.append(event)

        logger.info(
            "Key rotated: key=%s old=%s new=%s grace=%dh",
            key_id,
            old_credential_id,
            new_credential_id,
            schedule.grace_period_hours,
        )
        return event, None

    def _issue_new_key(
        self,
        schedule: RotationSchedule,
    ) -> tuple[str, str, str | None]:
        """Issue a new key via the appropriate auth provider.

        Returns (bearer_token, credential_id, error).
        """
        from src.kortana.services.auth_provider import (
            ProviderType,
            get_auth_provider_registry,
        )

        registry = get_auth_provider_registry()

        if schedule.provider_type == ProviderType.API_KEY.value:
            provider = registry.get_provider(ProviderType.API_KEY)
            if provider is None:
                return "", "", "API key provider not available"
            bearer, credential = provider.issue_key(
                operator_id=schedule.operator_id,
                display_name=f"Rotated key for {schedule.key_id}",
                role_hint="operator",
            )
            return bearer, credential.credential_id, None

        if schedule.provider_type == ProviderType.SERVICE_ACCOUNT.value:
            provider = registry.get_provider(ProviderType.SERVICE_ACCOUNT)
            if provider is None:
                return "", "", "Service account provider not available"
            secret, credential = provider.register(
                account_id=f"{schedule.operator_id}_rotated_{secrets.token_hex(4)}",
                display_name=f"Rotated service account for {schedule.key_id}",
            )
            return secret, credential.credential_id, None

        return "", "", f"Unsupported provider type for rotation: {schedule.provider_type}"

    def check_grace_periods(self) -> list[RotationSchedule]:
        """Return schedules whose grace period has expired."""
        return [s for s in self._schedules.values() if s.is_grace_expired]

    def expire_grace_period(self, key_id: str) -> tuple[bool, str | None]:
        """Expire a grace period, revoking the old key.

        Returns (success, error).
        """
        schedule = self._schedules.get(key_id)
        if schedule is None:
            return False, f"No rotation schedule for key {key_id!r}"

        if schedule.state != RotationState.GRACE_PERIOD:
            return False, f"Key {key_id!r} not in grace period"

        # Revoke the old key
        if schedule.old_credential_id:
            self._revoke_old_key(schedule)

        schedule.state = RotationState.ACTIVE

        event = RotationEvent(
            key_id=key_id,
            event_type=RotationEventType.GRACE_EXPIRED,
            old_credential_id=schedule.old_credential_id,
            new_credential_id=schedule.new_credential_id,
            initiated_by="system",
            details="Grace period expired; old key revoked",
        )
        self._events.append(event)

        logger.info("Grace period expired: key=%s old=%s revoked", key_id, schedule.old_credential_id)
        return True, None

    def _revoke_old_key(self, schedule: RotationSchedule) -> None:
        """Revoke the old key via the auth provider."""
        try:
            from src.kortana.services.auth_provider import (
                ProviderType,
                get_auth_provider_registry,
            )

            registry = get_auth_provider_registry()
            pt = ProviderType(schedule.provider_type)
            registry.revoke(pt, schedule.old_credential_id)
        except Exception as e:
            logger.warning("Failed to revoke old key %s: %s", schedule.old_credential_id, e)

    def disable_schedule(self, key_id: str) -> bool:
        """Disable a rotation schedule."""
        schedule = self._schedules.get(key_id)
        if schedule is None:
            return False
        schedule.state = RotationState.DISABLED
        return True

    def get_schedule(self, key_id: str) -> RotationSchedule | None:
        return self._schedules.get(key_id)

    def get_schedules(self) -> list[RotationSchedule]:
        return list(self._schedules.values())

    def get_rotation_history(self, key_id: str) -> list[RotationEvent]:
        return [e for e in self._events if e.key_id == key_id]

    @property
    def active_schedule_count(self) -> int:
        return sum(
            1 for s in self._schedules.values()
            if s.state in (RotationState.ACTIVE, RotationState.GRACE_PERIOD)
        )

    @property
    def due_count(self) -> int:
        return len(self.check_due_rotations())

    @property
    def event_count(self) -> int:
        return len(self._events)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_manager: KeyRotationManager | None = None


def get_key_rotation_manager() -> KeyRotationManager:
    """Return the module-level key rotation manager."""
    global _manager
    if _manager is None:
        _manager = KeyRotationManager()
    return _manager
