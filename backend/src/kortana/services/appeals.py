"""V23B — appeals: escalated review for blocked proposals."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from kortana.services.boundary_enforcer import BoundaryCheck
from kortana.services.constitution import Sensitivity
from kortana.services.policy_feedback_loop import PolicyArea


class AppealStatus(Enum):
    """Lifecycle of an appeal."""

    FILED = "filed"
    UNDER_REVIEW = "under_review"
    UPHELD = "upheld"
    OVERTURNED = "overturned"
    REMANDED = "remanded"
    WITHDRAWN = "withdrawn"


class AppealGrounds(Enum):
    """Basis for filing an appeal."""

    FACTUAL_ERROR = "factual_error"
    CHANGED_CIRCUMSTANCES = "changed_circumstances"
    DISPROPORTIONATE = "disproportionate"
    MISCLASSIFICATION = "misclassification"
    EMERGENCY_NEED = "emergency_need"
    NEW_EVIDENCE = "new_evidence"


@dataclass
class AppealEvidence:
    """Supporting evidence for an appeal."""

    evidence_id: str
    description: str
    evidence_type: str
    value: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "description": self.description,
            "evidence_type": self.evidence_type,
            "value": self.value,
        }


@dataclass
class AppealDecision:
    """The adjudication decision on an appeal."""

    decided_by: str
    outcome: AppealStatus
    reasoning: str
    conditions: list[str] = field(default_factory=list)
    decided_at: str = ""

    def __post_init__(self) -> None:
        if not self.decided_at:
            self.decided_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "decided_by": self.decided_by,
            "outcome": self.outcome.value,
            "reasoning": self.reasoning,
            "conditions": self.conditions,
            "decided_at": self.decided_at,
        }


@dataclass
class Appeal:
    """An appeal against a boundary enforcement decision."""

    appeal_id: str
    proposal_id: str
    original_check_id: str
    policy_area: PolicyArea
    appellant: str
    grounds: AppealGrounds
    argument: str
    evidence: list[AppealEvidence] = field(default_factory=list)
    status: AppealStatus = AppealStatus.FILED
    decision: AppealDecision | None = None
    escalated_sensitivity: Sensitivity = Sensitivity.HIGH
    filed_at: str = ""
    appeal_hash: str = ""

    def __post_init__(self) -> None:
        if not self.filed_at:
            self.filed_at = datetime.now(timezone.utc).isoformat()
        if not self.appeal_hash:
            blob = f"{self.appeal_id}:{self.proposal_id}:{self.grounds.value}:{self.appellant}"
            self.appeal_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "appeal_id": self.appeal_id,
            "proposal_id": self.proposal_id,
            "original_check_id": self.original_check_id,
            "policy_area": self.policy_area.value,
            "appellant": self.appellant,
            "grounds": self.grounds.value,
            "argument": self.argument,
            "evidence": [e.to_dict() for e in self.evidence],
            "status": self.status.value,
            "decision": self.decision.to_dict() if self.decision else None,
            "escalated_sensitivity": self.escalated_sensitivity.value,
            "filed_at": self.filed_at,
            "appeal_hash": self.appeal_hash,
        }


def _escalate_sensitivity(original: Sensitivity) -> Sensitivity:
    """Appeals always require one tier higher review."""
    escalation = {
        Sensitivity.LOW: Sensitivity.STANDARD,
        Sensitivity.STANDARD: Sensitivity.HIGH,
        Sensitivity.HIGH: Sensitivity.CRITICAL,
        Sensitivity.CRITICAL: Sensitivity.CRITICAL,
    }
    return escalation[original]


class AppealsCourt:
    """Manages the appeals process for blocked proposals."""

    def __init__(self) -> None:
        self._appeals: list[Appeal] = []

    def file_appeal(
        self,
        proposal_id: str,
        original_check: BoundaryCheck,
        appellant: str,
        grounds: AppealGrounds,
        argument: str,
        evidence: list[AppealEvidence] | None = None,
    ) -> Appeal:
        """File an appeal against a boundary check decision."""
        original_sensitivity = Sensitivity(original_check.sensitivity)
        escalated = _escalate_sensitivity(original_sensitivity)

        appeal = Appeal(
            appeal_id=f"appeal-{uuid.uuid4().hex[:12]}",
            proposal_id=proposal_id,
            original_check_id=original_check.check_id,
            policy_area=PolicyArea(original_check.policy_area),
            appellant=appellant,
            grounds=grounds,
            argument=argument,
            evidence=evidence or [],
            escalated_sensitivity=escalated,
        )
        self._appeals.append(appeal)
        return appeal

    def begin_review(self, appeal_id: str) -> bool:
        """Move an appeal into review."""
        for a in self._appeals:
            if a.appeal_id == appeal_id and a.status == AppealStatus.FILED:
                a.status = AppealStatus.UNDER_REVIEW
                return True
        return False

    def decide(
        self,
        appeal_id: str,
        decided_by: str,
        outcome: AppealStatus,
        reasoning: str,
        conditions: list[str] | None = None,
    ) -> bool:
        """Issue a decision on an appeal."""
        if outcome not in (AppealStatus.UPHELD, AppealStatus.OVERTURNED, AppealStatus.REMANDED):
            return False
        for a in self._appeals:
            if a.appeal_id == appeal_id and a.status in (AppealStatus.FILED, AppealStatus.UNDER_REVIEW):
                a.status = outcome
                a.decision = AppealDecision(
                    decided_by=decided_by,
                    outcome=outcome,
                    reasoning=reasoning,
                    conditions=conditions or [],
                )
                return True
        return False

    def withdraw(self, appeal_id: str) -> bool:
        """Withdraw a filed appeal."""
        for a in self._appeals:
            if a.appeal_id == appeal_id and a.status in (AppealStatus.FILED, AppealStatus.UNDER_REVIEW):
                a.status = AppealStatus.WITHDRAWN
                return True
        return False

    def get_appeal(self, appeal_id: str) -> Appeal | None:
        for a in self._appeals:
            if a.appeal_id == appeal_id:
                return a
        return None

    def get_appeals(
        self,
        proposal_id: str | None = None,
        status: AppealStatus | None = None,
        appellant: str | None = None,
    ) -> list[Appeal]:
        result = list(self._appeals)
        if proposal_id is not None:
            result = [a for a in result if a.proposal_id == proposal_id]
        if status is not None:
            result = [a for a in result if a.status == status]
        if appellant is not None:
            result = [a for a in result if a.appellant == appellant]
        return result

    @property
    def appeal_count(self) -> int:
        return len(self._appeals)

    @property
    def pending_count(self) -> int:
        return sum(1 for a in self._appeals if a.status in (AppealStatus.FILED, AppealStatus.UNDER_REVIEW))

    def get_summary(self) -> dict[str, Any]:
        by_status: dict[str, int] = {}
        by_grounds: dict[str, int] = {}
        for a in self._appeals:
            by_status[a.status.value] = by_status.get(a.status.value, 0) + 1
            by_grounds[a.grounds.value] = by_grounds.get(a.grounds.value, 0) + 1
        overturn_rate = 0.0
        decided = [a for a in self._appeals if a.status in (AppealStatus.UPHELD, AppealStatus.OVERTURNED)]
        if decided:
            overturn_rate = sum(1 for a in decided if a.status == AppealStatus.OVERTURNED) / len(decided)
        return {
            "total_appeals": len(self._appeals),
            "pending": self.pending_count,
            "by_status": by_status,
            "by_grounds": by_grounds,
            "overturn_rate": round(overturn_rate, 3),
        }


_court: AppealsCourt | None = None


def get_appeals_court() -> AppealsCourt:
    """Module singleton."""
    global _court
    if _court is None:
        _court = AppealsCourt()
    return _court
