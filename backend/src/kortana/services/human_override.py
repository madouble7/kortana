"""V8D — Human Override Protocol: signed manual overrides with expiry.

Allows authorised humans to override daemon mode with a scoped reason,
expiry window, and cryptographic audit hash. Active overrides take
precedence over automated actuation decisions.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("kortana.human_override")


# ---------------------------------------------------------------------------
# Override record
# ---------------------------------------------------------------------------


def compute_override_hash(
    mode: str,
    reason: str,
    expires_at: str,
    created_by: str,
    created_at: str,
) -> str:
    """SHA-256 hash over the override fields for tamper evidence."""
    payload = json.dumps(
        {
            "mode": mode,
            "reason": reason,
            "expires_at": expires_at,
            "created_by": created_by,
            "created_at": created_at,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class OverrideRecord:
    """A signed human override of daemon mode."""

    mode: str
    reason: str
    expires_at: datetime
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    audit_hash: str = ""
    revoked: bool = False
    revoked_at: datetime | None = None
    revoked_by: str | None = None
    override_id: int | None = None

    def __post_init__(self) -> None:
        if not self.audit_hash:
            self.audit_hash = compute_override_hash(
                self.mode,
                self.reason,
                self.expires_at.isoformat(),
                self.created_by,
                self.created_at.isoformat(),
            )

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @property
    def is_active(self) -> bool:
        return not self.revoked and not self.is_expired

    def to_dict(self) -> dict[str, Any]:
        return {
            "override_id": self.override_id,
            "mode": self.mode,
            "reason": self.reason,
            "expires_at": self.expires_at.isoformat(),
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "audit_hash": self.audit_hash,
            "revoked": self.revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revoked_by": self.revoked_by,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
        }


# ---------------------------------------------------------------------------
# Override precedence
# ---------------------------------------------------------------------------


def check_active_override(
    overrides: list[OverrideRecord],
    now: datetime | None = None,
) -> OverrideRecord | None:
    """Return the active override with the latest creation time, or None.

    An override is active if it is not revoked and not expired.
    """
    now = now or datetime.utcnow()
    active = [
        o for o in overrides
        if not o.revoked and o.expires_at > now
    ]
    if not active:
        return None
    # Latest one wins
    return max(active, key=lambda o: o.created_at)


def should_override_actuation(
    override: OverrideRecord | None,
    proposed_mode: str,
) -> tuple[bool, str]:
    """Check if a human override should block an actuation.

    Returns (should_block, reason).
    """
    if override is None:
        return False, ""

    if not override.is_active:
        return False, "Override is expired or revoked"

    if override.mode == proposed_mode:
        return False, "Override mode matches proposed mode"

    return True, (
        f"Human override active: mode locked to {override.mode!r} "
        f"by {override.created_by} until {override.expires_at.isoformat()} "
        f"— reason: {override.reason}"
    )


# ---------------------------------------------------------------------------
# In-memory override manager
# ---------------------------------------------------------------------------


class OverrideManager:
    """Manages human overrides within a daemon process."""

    def __init__(self) -> None:
        self._overrides: list[OverrideRecord] = []
        self._next_id: int = 1

    def create(
        self,
        mode: str,
        reason: str,
        expires_in_minutes: int = 60,
        created_by: str = "matt",
    ) -> OverrideRecord:
        """Create a new override and make it active."""
        now = datetime.utcnow()
        override = OverrideRecord(
            mode=mode,
            reason=reason,
            expires_at=now + timedelta(minutes=expires_in_minutes),
            created_by=created_by,
            created_at=now,
            override_id=self._next_id,
        )
        self._overrides.append(override)
        self._next_id += 1

        logger.info(
            "Override #%d created: mode=%s by=%s expires=%s reason=%s",
            override.override_id,
            override.mode,
            override.created_by,
            override.expires_at.isoformat(),
            override.reason,
        )
        return override

    def revoke(self, override_id: int, revoked_by: str = "matt") -> bool:
        """Revoke an override by ID. Returns True if found and revoked."""
        for o in self._overrides:
            if o.override_id == override_id and not o.revoked:
                o.revoked = True
                o.revoked_at = datetime.utcnow()
                o.revoked_by = revoked_by
                logger.info("Override #%d revoked by %s", override_id, revoked_by)
                return True
        return False

    def active(self, now: datetime | None = None) -> OverrideRecord | None:
        """Return the currently active override, or None."""
        return check_active_override(self._overrides, now)

    def all_active(self, now: datetime | None = None) -> list[OverrideRecord]:
        """Return all active (non-revoked, non-expired) overrides."""
        now = now or datetime.utcnow()
        return [o for o in self._overrides if not o.revoked and o.expires_at > now]

    def history(self) -> list[dict[str, Any]]:
        """Return all overrides as dicts, newest first."""
        return [o.to_dict() for o in reversed(self._overrides)]

    @property
    def count(self) -> int:
        return len(self._overrides)


# Module-level singleton
_manager = OverrideManager()


def get_override_manager() -> OverrideManager:
    """Return the module-level override manager singleton."""
    return _manager
