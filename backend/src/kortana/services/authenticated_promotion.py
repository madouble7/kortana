"""V12D — Authenticated Rule Promotion.

Wraps the V11D RuleLifecycleManager so that every promotion action
(submit, approve, reject, activate, retire) requires a valid V11B
identity session.  This enforces four-eyes review with real credentials
instead of bare operator-ID strings.

Each promotion action creates an AuthenticatedPromotionEvent that
records the session details alongside the rule version change.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("kortana.authenticated_promotion")


# ---------------------------------------------------------------------------
# Promotion event
# ---------------------------------------------------------------------------


@dataclass
class AuthenticatedPromotionEvent:
    """Records a session-backed rule promotion action."""

    event_id: str = field(default_factory=lambda: f"ap_{secrets.token_hex(8)}")
    version_id: str = ""
    rule_id: str = ""
    action: str = ""          # submit / approve / reject / activate / retire
    session_id: str = ""
    operator_id: str = ""
    session_verification_level: str = ""
    session_provider_type: str = ""
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
                "version_id": self.version_id,
                "action": self.action,
                "session_id": self.session_id,
                "operator_id": self.operator_id,
                "timestamp": self.timestamp.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "version_id": self.version_id,
            "rule_id": self.rule_id,
            "action": self.action,
            "session_id": self.session_id,
            "operator_id": self.operator_id,
            "session_verification_level": self.session_verification_level,
            "session_provider_type": self.session_provider_type,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "event_hash": self.event_hash,
        }


# ---------------------------------------------------------------------------
# Authenticated promotion manager
# ---------------------------------------------------------------------------


class AuthenticatedPromotionManager:
    """Wraps RuleLifecycleManager with session-authenticated promotions.

    Every promotion action validates the operator's identity session
    before delegating to the underlying RuleLifecycleManager.
    """

    def __init__(self) -> None:
        self._events: list[AuthenticatedPromotionEvent] = []

    def _validate_session(self, session_id: str) -> tuple[Any, str | None]:
        """Validate an identity session. Returns (session, error)."""
        from src.kortana.services.identity_verification import (
            get_identity_verification_manager,
        )

        manager = get_identity_verification_manager()
        session = manager.get_session(session_id)

        if session is None:
            return None, f"Session {session_id!r} not found or expired"

        if not session.is_active:
            return None, f"Session {session_id!r} is not active"

        return session, None

    def _record_event(
        self,
        version_id: str,
        rule_id: str,
        action: str,
        session: Any,
        details: str = "",
    ) -> AuthenticatedPromotionEvent:
        """Record an authenticated promotion event."""
        event = AuthenticatedPromotionEvent(
            version_id=version_id,
            rule_id=rule_id,
            action=action,
            session_id=session.session_id,
            operator_id=session.operator_id,
            session_verification_level=session.verification_level.value,
            session_provider_type=session.provider_type,
            details=details,
        )
        self._events.append(event)
        logger.info(
            "Authenticated promotion: action=%s version=%s operator=%s level=%s",
            action,
            version_id,
            session.operator_id,
            session.verification_level.value,
        )
        return event

    def submit_for_review(
        self,
        version_id: str,
        session_id: str,
    ) -> tuple[Any | None, str | None]:
        """Submit a draft rule for review, authenticated by session.

        Returns (version, error).
        """
        from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

        session, error = self._validate_session(session_id)
        if error:
            return None, error

        lifecycle = get_rule_lifecycle_manager()
        version, err = lifecycle.submit_for_review(version_id, session.operator_id)
        if err:
            return None, err

        self._record_event(
            version_id=version_id,
            rule_id=version.rule_id,
            action="submit",
            session=session,
            details=f"Submitted for review by {session.operator_id}",
        )
        return version, None

    def approve(
        self,
        version_id: str,
        session_id: str,
    ) -> tuple[Any | None, str | None]:
        """Approve a rule under review, authenticated by session.

        Four-eyes: the session operator must differ from the rule author.
        Returns (version, error).
        """
        from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

        session, error = self._validate_session(session_id)
        if error:
            return None, error

        lifecycle = get_rule_lifecycle_manager()
        version, err = lifecycle.approve(version_id, session.operator_id)
        if err:
            return None, err

        self._record_event(
            version_id=version_id,
            rule_id=version.rule_id,
            action="approve",
            session=session,
            details=f"Approved by {session.operator_id} (reviewer)",
        )
        return version, None

    def reject(
        self,
        version_id: str,
        session_id: str,
        reason: str = "",
    ) -> tuple[Any | None, str | None]:
        """Reject a rule under review, authenticated by session.

        Returns (version, error).
        """
        from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

        session, error = self._validate_session(session_id)
        if error:
            return None, error

        lifecycle = get_rule_lifecycle_manager()
        version, err = lifecycle.reject(version_id, session.operator_id, reason)
        if err:
            return None, err

        self._record_event(
            version_id=version_id,
            rule_id=version.rule_id,
            action="reject",
            session=session,
            details=f"Rejected by {session.operator_id}: {reason}",
        )
        return version, None

    def activate(
        self,
        version_id: str,
        session_id: str,
    ) -> tuple[Any | None, str | None]:
        """Activate a rule, authenticated by session.

        Returns (version, error).
        """
        from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

        session, error = self._validate_session(session_id)
        if error:
            return None, error

        lifecycle = get_rule_lifecycle_manager()
        version, err = lifecycle.activate(version_id, session.operator_id)
        if err:
            return None, err

        self._record_event(
            version_id=version_id,
            rule_id=version.rule_id,
            action="activate",
            session=session,
            details=f"Activated by {session.operator_id}",
        )
        return version, None

    def retire(
        self,
        version_id: str,
        session_id: str,
        reason: str = "",
    ) -> tuple[Any | None, str | None]:
        """Retire an active rule, authenticated by session.

        Returns (version, error).
        """
        from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

        session, error = self._validate_session(session_id)
        if error:
            return None, error

        lifecycle = get_rule_lifecycle_manager()
        version, err = lifecycle.retire(version_id, session.operator_id, reason)
        if err:
            return None, err

        self._record_event(
            version_id=version_id,
            rule_id=version.rule_id,
            action="retire",
            session=session,
            details=f"Retired by {session.operator_id}: {reason}",
        )
        return version, None

    def get_events(self, version_id: str) -> list[AuthenticatedPromotionEvent]:
        """Get all promotion events for a specific rule version."""
        return [e for e in self._events if e.version_id == version_id]

    def get_all_events(self) -> list[AuthenticatedPromotionEvent]:
        """Get all promotion events."""
        return list(self._events)

    @property
    def event_count(self) -> int:
        return len(self._events)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_manager: AuthenticatedPromotionManager | None = None


def get_authenticated_promotion_manager() -> AuthenticatedPromotionManager:
    """Return the module-level authenticated promotion manager."""
    global _manager
    if _manager is None:
        _manager = AuthenticatedPromotionManager()
    return _manager
