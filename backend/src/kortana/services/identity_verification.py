"""V11B — Durable Identity Verification.

Provides identity verification workflows that bridge external auth providers
to the V10 operator identity system.  Handles:

- Token-to-identity resolution via the AuthProviderRegistry
- Identity binding (linking external credentials to operator records)
- Verification challenges for elevated actions
- Session management with expiry and refresh
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

logger = logging.getLogger("kortana.identity_verification")


# ---------------------------------------------------------------------------
# Verification status
# ---------------------------------------------------------------------------


class VerificationLevel(str, Enum):
    """Trust level of a verified identity."""

    NONE = "none"              # Not verified
    BASIC = "basic"            # Token verified, identity resolved
    ELEVATED = "elevated"      # Challenge completed (e.g. re-auth for sensitive ops)
    FULL = "full"              # Multi-factor or provider-confirmed


class SessionStatus(str, Enum):
    """Lifecycle state of an identity session."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


# ---------------------------------------------------------------------------
# Identity session
# ---------------------------------------------------------------------------


@dataclass
class IdentitySession:
    """A verified identity session with expiry and level tracking."""

    session_id: str
    operator_id: str
    display_name: str
    role: str
    provider_type: str
    credential_id: str
    verification_level: VerificationLevel = VerificationLevel.BASIC
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=8)
    )
    last_activity: datetime = field(default_factory=datetime.utcnow)
    session_hash: str = ""

    def __post_init__(self) -> None:
        if not self.session_hash:
            self.session_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "session_id": self.session_id,
                "operator_id": self.operator_id,
                "provider_type": self.provider_type,
                "created_at": self.created_at.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @property
    def is_active(self) -> bool:
        return self.status == SessionStatus.ACTIVE and not self.is_expired

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def elevate(self, level: VerificationLevel) -> None:
        """Upgrade the verification level."""
        self.verification_level = level

    def revoke(self) -> None:
        """Revoke this session."""
        self.status = SessionStatus.REVOKED

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "operator_id": self.operator_id,
            "display_name": self.display_name,
            "role": self.role,
            "provider_type": self.provider_type,
            "credential_id": self.credential_id,
            "verification_level": self.verification_level.value,
            "status": self.status.value if self.is_active else "expired",
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "session_hash": self.session_hash,
        }


# ---------------------------------------------------------------------------
# Identity binding
# ---------------------------------------------------------------------------


@dataclass
class IdentityBinding:
    """Links an external credential to an operator identity.

    Once bound, any token verified by the linked provider is
    automatically resolved to the bound operator.
    """

    binding_id: str
    operator_id: str
    provider_type: str
    external_id: str          # External identifier from the provider
    display_name: str
    bound_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True
    binding_hash: str = ""

    def __post_init__(self) -> None:
        if not self.binding_hash:
            payload = json.dumps(
                {
                    "binding_id": self.binding_id,
                    "operator_id": self.operator_id,
                    "provider_type": self.provider_type,
                    "external_id": self.external_id,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            self.binding_hash = hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "operator_id": self.operator_id,
            "provider_type": self.provider_type,
            "external_id": self.external_id,
            "display_name": self.display_name,
            "bound_at": self.bound_at.isoformat(),
            "active": self.active,
            "binding_hash": self.binding_hash,
        }


# ---------------------------------------------------------------------------
# Verification manager
# ---------------------------------------------------------------------------


class IdentityVerificationManager:
    """Manages identity verification, sessions, and bindings.

    Bridges auth providers (V11A) to operator identity (V10A)
    with durable session state and binding records.
    """

    def __init__(self, session_ttl_hours: int = 8) -> None:
        self._sessions: dict[str, IdentitySession] = {}
        self._bindings: dict[str, IdentityBinding] = {}  # binding_id → binding
        self._operator_bindings: dict[str, list[str]] = {}  # operator_id → [binding_ids]
        self._session_ttl = timedelta(hours=session_ttl_hours)

    def verify_and_create_session(
        self,
        token: str,
        provider_type: str | None = None,
    ) -> tuple[IdentitySession | None, str | None]:
        """Verify a token and create a session if valid.

        Returns (session, None) on success or (None, error) on failure.
        """
        from src.kortana.services.auth_provider import (
            ProviderType,
            get_auth_provider_registry,
        )

        registry = get_auth_provider_registry()
        pt = ProviderType(provider_type) if provider_type else None
        credential = registry.verify(token, pt)

        if credential is None:
            return None, "Token verification failed"

        if credential.is_expired:
            return None, "Credential has expired"

        session = IdentitySession(
            session_id=f"sess_{secrets.token_hex(16)}",
            operator_id=credential.operator_id,
            display_name=credential.display_name,
            role=credential.role_hint,
            provider_type=credential.provider_type.value,
            credential_id=credential.credential_id,
            expires_at=datetime.utcnow() + self._session_ttl,
        )

        self._sessions[session.session_id] = session
        logger.info(
            "Session created: %s for %s via %s",
            session.session_id, session.operator_id, session.provider_type,
        )
        return session, None

    def get_session(self, session_id: str) -> IdentitySession | None:
        session = self._sessions.get(session_id)
        if session and session.is_active:
            session.touch()
            return session
        return None

    def revoke_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session:
            session.revoke()
            logger.info("Session revoked: %s", session_id)
            return True
        return False

    def elevate_session(
        self,
        session_id: str,
        level: VerificationLevel,
    ) -> bool:
        """Elevate a session's verification level."""
        session = self._sessions.get(session_id)
        if session and session.is_active:
            session.elevate(level)
            logger.info(
                "Session elevated: %s → %s", session_id, level.value
            )
            return True
        return False

    def bind_identity(
        self,
        operator_id: str,
        provider_type: str,
        external_id: str,
        display_name: str,
    ) -> IdentityBinding:
        """Create a binding between an external credential and an operator."""
        binding_id = f"bind_{secrets.token_hex(8)}"
        binding = IdentityBinding(
            binding_id=binding_id,
            operator_id=operator_id,
            provider_type=provider_type,
            external_id=external_id,
            display_name=display_name,
        )
        self._bindings[binding_id] = binding
        if operator_id not in self._operator_bindings:
            self._operator_bindings[operator_id] = []
        self._operator_bindings[operator_id].append(binding_id)
        logger.info(
            "Identity bound: %s → %s via %s",
            operator_id, external_id, provider_type,
        )
        return binding

    def get_bindings(self, operator_id: str) -> list[IdentityBinding]:
        """Get all bindings for an operator."""
        ids = self._operator_bindings.get(operator_id, [])
        return [self._bindings[bid] for bid in ids if bid in self._bindings]

    def revoke_binding(self, binding_id: str) -> bool:
        binding = self._bindings.get(binding_id)
        if binding:
            binding.active = False
            logger.info("Binding revoked: %s", binding_id)
            return True
        return False

    @property
    def active_sessions(self) -> list[IdentitySession]:
        return [s for s in self._sessions.values() if s.is_active]

    @property
    def session_count(self) -> int:
        return len(self._sessions)

    @property
    def active_session_count(self) -> int:
        return len(self.active_sessions)

    @property
    def binding_count(self) -> int:
        return len(self._bindings)

    def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count removed."""
        expired = [
            sid for sid, s in self._sessions.items()
            if not s.is_active
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)


# Module-level singleton
_manager = IdentityVerificationManager()


def get_identity_verification_manager() -> IdentityVerificationManager:
    """Return the module-level identity verification manager."""
    return _manager
