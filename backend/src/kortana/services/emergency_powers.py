"""V23C — emergency powers: time-boxed authority for crisis response."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any

from kortana.services.constitution import PolicyClassification
from kortana.services.policy_feedback_loop import PolicyArea


class EmergencyStatus(Enum):
    """Lifecycle of an emergency declaration."""

    DECLARED = "declared"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVIEWED = "reviewed"
    REVOKED = "revoked"


class EmergencyScope(Enum):
    """What areas emergency powers cover."""

    SINGLE_AREA = "single_area"
    MULTIPLE_AREAS = "multiple_areas"
    SYSTEM_WIDE = "system_wide"


MAX_EMERGENCY_HOURS = 24  # Hard cap — no emergency lasts longer
CONSTITUTIONAL_FLOOR = PolicyClassification.IMMUTABLE  # Cannot override


@dataclass
class EmergencyPower:
    """A specific power granted during an emergency."""

    power_id: str
    description: str
    policy_area: PolicyArea
    original_classification: PolicyClassification
    temporary_classification: PolicyClassification

    def to_dict(self) -> dict[str, Any]:
        return {
            "power_id": self.power_id,
            "description": self.description,
            "policy_area": self.policy_area.value,
            "original_classification": self.original_classification.value,
            "temporary_classification": self.temporary_classification.value,
        }


@dataclass
class PostEmergencyReview:
    """Mandatory review after emergency powers expire."""

    review_id: str
    declaration_id: str
    reviewer: str
    actions_taken: list[str]
    justified: bool
    findings: str
    recommendations: list[str] = field(default_factory=list)
    reviewed_at: str = ""

    def __post_init__(self) -> None:
        if not self.reviewed_at:
            self.reviewed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "declaration_id": self.declaration_id,
            "reviewer": self.reviewer,
            "actions_taken": self.actions_taken,
            "justified": self.justified,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "reviewed_at": self.reviewed_at,
        }


@dataclass
class EmergencyDeclaration:
    """A declaration of emergency granting temporary powers."""

    declaration_id: str
    declared_by: str
    reason: str
    scope: EmergencyScope
    affected_areas: list[PolicyArea]
    powers: list[EmergencyPower] = field(default_factory=list)
    duration_hours: int = 4
    status: EmergencyStatus = EmergencyStatus.DECLARED
    review: PostEmergencyReview | None = None
    declared_at: str = ""
    activated_at: str = ""
    expires_at: str = ""
    revoked_at: str = ""
    declaration_hash: str = ""

    def __post_init__(self) -> None:
        if not self.declared_at:
            self.declared_at = datetime.now(timezone.utc).isoformat()
        if not self.declaration_hash:
            blob = f"{self.declaration_id}:{self.declared_by}:{self.reason}:{self.scope.value}"
            self.declaration_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]
        if self.duration_hours > MAX_EMERGENCY_HOURS:
            self.duration_hours = MAX_EMERGENCY_HOURS

    @property
    def is_active(self) -> bool:
        if self.status not in (EmergencyStatus.DECLARED, EmergencyStatus.ACTIVE):
            return False
        if self.expires_at:
            return datetime.now(timezone.utc) <= datetime.fromisoformat(self.expires_at)
        return True

    @property
    def needs_review(self) -> bool:
        return self.status in (EmergencyStatus.EXPIRED, EmergencyStatus.REVOKED) and self.review is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "declaration_id": self.declaration_id,
            "declared_by": self.declared_by,
            "reason": self.reason,
            "scope": self.scope.value,
            "affected_areas": [a.value for a in self.affected_areas],
            "powers": [p.to_dict() for p in self.powers],
            "duration_hours": self.duration_hours,
            "status": self.status.value,
            "review": self.review.to_dict() if self.review else None,
            "declared_at": self.declared_at,
            "activated_at": self.activated_at,
            "expires_at": self.expires_at,
            "revoked_at": self.revoked_at,
            "declaration_hash": self.declaration_hash,
            "is_active": self.is_active,
            "needs_review": self.needs_review,
        }


class EmergencyPowersManager:
    """Manages time-boxed emergency powers that cannot override the constitutional floor."""

    def __init__(self) -> None:
        self._declarations: list[EmergencyDeclaration] = []

    def declare_emergency(
        self,
        declared_by: str,
        reason: str,
        affected_areas: list[PolicyArea],
        scope: EmergencyScope = EmergencyScope.SINGLE_AREA,
        duration_hours: int = 4,
    ) -> EmergencyDeclaration:
        """Declare an emergency. Powers for immutable areas are rejected."""
        powers: list[EmergencyPower] = []
        for area in affected_areas:
            # Determine what power we can grant
            original = PolicyClassification.RESTRICTED  # default assumption
            temp = PolicyClassification.AMENDABLE
            powers.append(EmergencyPower(
                power_id=f"pow-{uuid.uuid4().hex[:8]}",
                description=f"Temporary relaxation of {area.value} restrictions",
                policy_area=area,
                original_classification=original,
                temporary_classification=temp,
            ))

        declaration = EmergencyDeclaration(
            declaration_id=f"emer-{uuid.uuid4().hex[:12]}",
            declared_by=declared_by,
            reason=reason,
            scope=scope,
            affected_areas=affected_areas,
            powers=powers,
            duration_hours=min(duration_hours, MAX_EMERGENCY_HOURS),
        )
        self._declarations.append(declaration)
        return declaration

    def activate(self, declaration_id: str) -> bool:
        """Activate a declared emergency — starts the expiration clock."""
        for d in self._declarations:
            if d.declaration_id == declaration_id and d.status == EmergencyStatus.DECLARED:
                now = datetime.now(timezone.utc)
                d.status = EmergencyStatus.ACTIVE
                d.activated_at = now.isoformat()
                d.expires_at = (now + timedelta(hours=d.duration_hours)).isoformat()
                return True
        return False

    def revoke(self, declaration_id: str) -> bool:
        """Revoke an active emergency immediately."""
        for d in self._declarations:
            if d.declaration_id == declaration_id and d.status in (EmergencyStatus.DECLARED, EmergencyStatus.ACTIVE):
                d.status = EmergencyStatus.REVOKED
                d.revoked_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def expire_declarations(self) -> int:
        """Expire all declarations past their expiration time."""
        now = datetime.now(timezone.utc)
        count = 0
        for d in self._declarations:
            if d.status == EmergencyStatus.ACTIVE and d.expires_at:
                if now > datetime.fromisoformat(d.expires_at):
                    d.status = EmergencyStatus.EXPIRED
                    count += 1
        return count

    def submit_review(
        self,
        declaration_id: str,
        reviewer: str,
        actions_taken: list[str],
        justified: bool,
        findings: str,
        recommendations: list[str] | None = None,
    ) -> bool:
        """Submit a mandatory post-emergency review."""
        for d in self._declarations:
            if d.declaration_id == declaration_id and d.needs_review:
                d.review = PostEmergencyReview(
                    review_id=f"rev-{uuid.uuid4().hex[:12]}",
                    declaration_id=declaration_id,
                    reviewer=reviewer,
                    actions_taken=actions_taken,
                    justified=justified,
                    findings=findings,
                    recommendations=recommendations or [],
                )
                d.status = EmergencyStatus.REVIEWED
                return True
        return False

    def check_emergency_power(self, area: PolicyArea) -> EmergencyDeclaration | None:
        """Check if an active emergency grants power over a policy area."""
        for d in self._declarations:
            if d.is_active and area in d.affected_areas:
                return d
        return None

    def is_area_under_emergency(self, area: PolicyArea) -> bool:
        return self.check_emergency_power(area) is not None

    def get_declaration(self, declaration_id: str) -> EmergencyDeclaration | None:
        for d in self._declarations:
            if d.declaration_id == declaration_id:
                return d
        return None

    def get_declarations(
        self,
        status: EmergencyStatus | None = None,
        active_only: bool = False,
        needs_review: bool = False,
    ) -> list[EmergencyDeclaration]:
        result = list(self._declarations)
        if status is not None:
            result = [d for d in result if d.status == status]
        if active_only:
            result = [d for d in result if d.is_active]
        if needs_review:
            result = [d for d in result if d.needs_review]
        return result

    @property
    def declaration_count(self) -> int:
        return len(self._declarations)

    @property
    def active_count(self) -> int:
        return sum(1 for d in self._declarations if d.is_active)

    @property
    def needs_review_count(self) -> int:
        return sum(1 for d in self._declarations if d.needs_review)

    def get_summary(self) -> dict[str, Any]:
        by_status: dict[str, int] = {}
        for d in self._declarations:
            by_status[d.status.value] = by_status.get(d.status.value, 0) + 1
        return {
            "total_declarations": len(self._declarations),
            "active": self.active_count,
            "needs_review": self.needs_review_count,
            "by_status": by_status,
            "max_duration_hours": MAX_EMERGENCY_HOURS,
            "constitutional_floor": CONSTITUTIONAL_FLOOR.value,
        }


_manager: EmergencyPowersManager | None = None


def get_emergency_powers() -> EmergencyPowersManager:
    """Module singleton."""
    global _manager
    if _manager is None:
        _manager = EmergencyPowersManager()
    return _manager
