"""V24C — recusal manager: conflict-of-interest detection and enforcement."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ConflictType(Enum):
    """Types of conflicts of interest."""

    PROPOSER = "proposer"
    AREA_INTEREST = "area_interest"
    PRIOR_INVOLVEMENT = "prior_involvement"
    PERSONAL = "personal"


@dataclass
class InterestDeclaration:
    """A declared interest in specific policy areas."""

    declaration_id: str
    actor: str
    policy_areas: list[str]
    reason: str = ""
    declared_at: str = ""

    def __post_init__(self) -> None:
        if not self.declared_at:
            self.declared_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "declaration_id": self.declaration_id,
            "actor": self.actor,
            "policy_areas": self.policy_areas,
            "reason": self.reason,
            "declared_at": self.declared_at,
        }


@dataclass
class RecusalRecord:
    """Record of an actor recusing from a proceeding."""

    recusal_id: str
    actor: str
    reference_id: str
    conflict_type: ConflictType
    reason: str
    mandatory: bool = False
    recused_at: str = ""
    recusal_hash: str = ""

    def __post_init__(self) -> None:
        if not self.recused_at:
            self.recused_at = datetime.now(timezone.utc).isoformat()
        if not self.recusal_hash:
            blob = f"{self.recusal_id}:{self.actor}:{self.reference_id}:{self.conflict_type.value}"
            self.recusal_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "recusal_id": self.recusal_id,
            "actor": self.actor,
            "reference_id": self.reference_id,
            "conflict_type": self.conflict_type.value,
            "reason": self.reason,
            "mandatory": self.mandatory,
            "recused_at": self.recused_at,
            "recusal_hash": self.recusal_hash,
        }


class RecusalManager:
    """Manages conflict-of-interest declarations and recusals."""

    def __init__(self) -> None:
        self._interests: list[InterestDeclaration] = []
        self._recusals: list[RecusalRecord] = []

    def declare_interest(
        self,
        actor: str,
        policy_areas: list[str],
        reason: str = "",
    ) -> InterestDeclaration:
        """Declare an interest in specific policy areas."""
        decl = InterestDeclaration(
            declaration_id=f"int-{uuid.uuid4().hex[:12]}",
            actor=actor,
            policy_areas=policy_areas,
            reason=reason,
        )
        self._interests.append(decl)
        return decl

    def check_conflicts(
        self,
        actor: str,
        reference_id: str,
        policy_area: str,
        proposer_id: str | None = None,
    ) -> list[ConflictType]:
        """Check what conflicts an actor has for a given proceeding."""
        conflicts: list[ConflictType] = []

        # Check if actor is the proposer
        if proposer_id is not None and actor == proposer_id:
            conflicts.append(ConflictType.PROPOSER)

        # Check declared interests
        for decl in self._interests:
            if decl.actor == actor and policy_area in decl.policy_areas:
                conflicts.append(ConflictType.AREA_INTEREST)
                break

        # Check prior involvement (recused from related proceedings)
        for rec in self._recusals:
            if rec.actor == actor and rec.reference_id != reference_id:
                # If recused from another proceeding, flag prior involvement
                conflicts.append(ConflictType.PRIOR_INVOLVEMENT)
                break

        return conflicts

    def recuse(
        self,
        actor: str,
        reference_id: str,
        conflict_type: ConflictType,
        reason: str,
        mandatory: bool = False,
    ) -> RecusalRecord:
        """Record a recusal from a proceeding."""
        record = RecusalRecord(
            recusal_id=f"rec-{uuid.uuid4().hex[:12]}",
            actor=actor,
            reference_id=reference_id,
            conflict_type=conflict_type,
            reason=reason,
            mandatory=mandatory,
        )
        self._recusals.append(record)
        return record

    def is_recused(self, actor: str, reference_id: str) -> bool:
        """Check if an actor is recused from a specific proceeding."""
        return any(
            r.actor == actor and r.reference_id == reference_id
            for r in self._recusals
        )

    def get_recusals(
        self,
        actor: str | None = None,
        reference_id: str | None = None,
    ) -> list[RecusalRecord]:
        result = list(self._recusals)
        if actor is not None:
            result = [r for r in result if r.actor == actor]
        if reference_id is not None:
            result = [r for r in result if r.reference_id == reference_id]
        return result

    def get_interests(self, actor: str | None = None) -> list[InterestDeclaration]:
        if actor is not None:
            return [d for d in self._interests if d.actor == actor]
        return list(self._interests)

    @property
    def interest_count(self) -> int:
        return len(self._interests)

    @property
    def recusal_count(self) -> int:
        return len(self._recusals)

    def get_summary(self) -> dict[str, Any]:
        by_conflict: dict[str, int] = {}
        for r in self._recusals:
            by_conflict[r.conflict_type.value] = by_conflict.get(r.conflict_type.value, 0) + 1
        mandatory = sum(1 for r in self._recusals if r.mandatory)
        return {
            "total_interests": len(self._interests),
            "total_recusals": len(self._recusals),
            "mandatory_recusals": mandatory,
            "voluntary_recusals": len(self._recusals) - mandatory,
            "by_conflict_type": by_conflict,
        }


_manager: RecusalManager | None = None


def get_recusal_manager() -> RecusalManager:
    """Module singleton."""
    global _manager
    if _manager is None:
        _manager = RecusalManager()
    return _manager
