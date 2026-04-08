"""V23A — exception handler: constitutional waivers for edge cases."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any

from src.kortana.services.constitution import (
    Constitution,
    PolicyClassification,
    get_constitution,
)
from src.kortana.services.policy_feedback_loop import PolicyArea


class WaiverStatus(Enum):
    """Lifecycle of a constitutional waiver."""

    REQUESTED = "requested"
    GRANTED = "granted"
    DENIED = "denied"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class WaiverScope(Enum):
    """How broad a waiver's effect is."""

    SINGLE_PROPOSAL = "single_proposal"
    POLICY_AREA = "policy_area"
    TIME_BOUNDED = "time_bounded"


MAX_WAIVER_HOURS = 72  # Hard cap — no waiver lasts longer


@dataclass
class WaiverCondition:
    """A condition that must hold while a waiver is active."""

    condition_id: str
    description: str
    verification_method: str
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "description": self.description,
            "verification_method": self.verification_method,
            "required": self.required,
        }


@dataclass
class ConstitutionalWaiver:
    """A temporary exception to a constitutional article."""

    waiver_id: str
    article_id: str
    proposal_id: str
    policy_area: PolicyArea
    classification_overridden: PolicyClassification
    reason: str
    granted_by: str
    scope: WaiverScope
    conditions: list[WaiverCondition] = field(default_factory=list)
    duration_hours: int = 4
    status: WaiverStatus = WaiverStatus.REQUESTED
    requested_at: str = ""
    granted_at: str = ""
    expires_at: str = ""
    revoked_at: str = ""
    waiver_hash: str = ""

    def __post_init__(self) -> None:
        if not self.requested_at:
            self.requested_at = datetime.now(timezone.utc).isoformat()
        if not self.waiver_hash:
            blob = f"{self.waiver_id}:{self.article_id}:{self.proposal_id}:{self.reason}"
            self.waiver_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]
        # Enforce hard cap
        if self.duration_hours > MAX_WAIVER_HOURS:
            self.duration_hours = MAX_WAIVER_HOURS

    @property
    def is_active(self) -> bool:
        if self.status not in (WaiverStatus.GRANTED, WaiverStatus.ACTIVE):
            return False
        if self.expires_at:
            expires = datetime.fromisoformat(self.expires_at)
            if datetime.now(timezone.utc) > expires:
                return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "waiver_id": self.waiver_id,
            "article_id": self.article_id,
            "proposal_id": self.proposal_id,
            "policy_area": self.policy_area.value,
            "classification_overridden": self.classification_overridden.value,
            "reason": self.reason,
            "granted_by": self.granted_by,
            "scope": self.scope.value,
            "conditions": [c.to_dict() for c in self.conditions],
            "duration_hours": self.duration_hours,
            "status": self.status.value,
            "requested_at": self.requested_at,
            "granted_at": self.granted_at,
            "expires_at": self.expires_at,
            "revoked_at": self.revoked_at,
            "waiver_hash": self.waiver_hash,
            "is_active": self.is_active,
        }


class ExceptionHandler:
    """Manages constitutional waivers — temporary exceptions to articles."""

    def __init__(self, constitution: Constitution | None = None) -> None:
        self._constitution = constitution or get_constitution()
        self._waivers: list[ConstitutionalWaiver] = []

    def request_waiver(
        self,
        article_id: str,
        proposal_id: str,
        reason: str,
        requested_by: str,
        scope: WaiverScope = WaiverScope.SINGLE_PROPOSAL,
        duration_hours: int = 4,
        conditions: list[WaiverCondition] | None = None,
    ) -> ConstitutionalWaiver:
        """Request a temporary waiver for a constitutional article."""
        article = self._constitution.get_article(article_id)
        policy_area = article.policy_area if article else PolicyArea.GOVERNANCE
        classification = article.classification if article else PolicyClassification.IMMUTABLE

        waiver = ConstitutionalWaiver(
            waiver_id=f"waiver-{uuid.uuid4().hex[:12]}",
            article_id=article_id,
            proposal_id=proposal_id,
            policy_area=policy_area,
            classification_overridden=classification,
            reason=reason,
            granted_by=requested_by,
            scope=scope,
            conditions=conditions or [],
            duration_hours=min(duration_hours, MAX_WAIVER_HOURS),
        )
        self._waivers.append(waiver)
        return waiver

    def grant_waiver(self, waiver_id: str) -> bool:
        """Grant a requested waiver — sets expiration clock."""
        for w in self._waivers:
            if w.waiver_id == waiver_id and w.status == WaiverStatus.REQUESTED:
                now = datetime.now(timezone.utc)
                w.status = WaiverStatus.ACTIVE
                w.granted_at = now.isoformat()
                w.expires_at = (now + timedelta(hours=w.duration_hours)).isoformat()
                return True
        return False

    def deny_waiver(self, waiver_id: str, reason: str = "") -> bool:
        """Deny a waiver request."""
        for w in self._waivers:
            if w.waiver_id == waiver_id and w.status == WaiverStatus.REQUESTED:
                w.status = WaiverStatus.DENIED
                if reason:
                    w.reason = f"{w.reason} [DENIED: {reason}]"
                return True
        return False

    def revoke_waiver(self, waiver_id: str) -> bool:
        """Revoke an active waiver immediately."""
        for w in self._waivers:
            if w.waiver_id == waiver_id and w.status in (WaiverStatus.GRANTED, WaiverStatus.ACTIVE):
                w.status = WaiverStatus.REVOKED
                w.revoked_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def check_waiver(self, article_id: str, proposal_id: str) -> ConstitutionalWaiver | None:
        """Check if an active waiver exists for a given article and proposal."""
        for w in self._waivers:
            if not w.is_active:
                continue
            if w.article_id == article_id:
                if w.scope == WaiverScope.SINGLE_PROPOSAL and w.proposal_id == proposal_id:
                    return w
                if w.scope in (WaiverScope.POLICY_AREA, WaiverScope.TIME_BOUNDED):
                    return w
        return None

    def expire_waivers(self) -> int:
        """Expire all waivers past their expiration time. Returns count expired."""
        now = datetime.now(timezone.utc)
        count = 0
        for w in self._waivers:
            if w.status in (WaiverStatus.GRANTED, WaiverStatus.ACTIVE) and w.expires_at:
                if now > datetime.fromisoformat(w.expires_at):
                    w.status = WaiverStatus.EXPIRED
                    count += 1
        return count

    def get_waivers(
        self,
        article_id: str | None = None,
        status: WaiverStatus | None = None,
        active_only: bool = False,
    ) -> list[ConstitutionalWaiver]:
        result = list(self._waivers)
        if article_id is not None:
            result = [w for w in result if w.article_id == article_id]
        if status is not None:
            result = [w for w in result if w.status == status]
        if active_only:
            result = [w for w in result if w.is_active]
        return result

    def get_waiver(self, waiver_id: str) -> ConstitutionalWaiver | None:
        for w in self._waivers:
            if w.waiver_id == waiver_id:
                return w
        return None

    @property
    def waiver_count(self) -> int:
        return len(self._waivers)

    @property
    def active_waiver_count(self) -> int:
        return sum(1 for w in self._waivers if w.is_active)

    def get_summary(self) -> dict[str, Any]:
        by_status: dict[str, int] = {}
        for w in self._waivers:
            key = w.status.value
            by_status[key] = by_status.get(key, 0) + 1
        return {
            "total_waivers": len(self._waivers),
            "active_waivers": self.active_waiver_count,
            "by_status": by_status,
            "max_duration_hours": MAX_WAIVER_HOURS,
        }


_handler: ExceptionHandler | None = None


def get_exception_handler() -> ExceptionHandler:
    """Module singleton."""
    global _handler
    if _handler is None:
        _handler = ExceptionHandler()
    return _handler
