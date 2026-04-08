"""V25A — public docket: registry of all constitutional proceedings."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class CaseType(Enum):
    """Types of constitutional proceedings."""

    APPEAL = "appeal"
    WAIVER = "waiver"
    EMERGENCY = "emergency"
    QUORUM_VOTE = "quorum_vote"
    BOUNDARY_CHECK = "boundary_check"
    RECUSAL = "recusal"
    PRECEDENT_REVIEW = "precedent_review"


class CaseStatus(Enum):
    """Status of a docketed case."""

    OPENED = "opened"
    IN_PROGRESS = "in_progress"
    AWAITING_DECISION = "awaiting_decision"
    DECIDED = "decided"
    CLOSED = "closed"
    DISMISSED = "dismissed"


@dataclass
class DocketEntry:
    """A single entry on the public docket."""

    case_number: str
    case_type: CaseType
    title: str
    parties: list[str]
    policy_area: str = ""
    status: CaseStatus = CaseStatus.OPENED
    reference_id: str = ""
    opened_at: str = ""
    updated_at: str = ""
    closed_at: str = ""
    outcome: str = ""
    docket_hash: str = ""

    def __post_init__(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        if not self.opened_at:
            self.opened_at = now
        if not self.updated_at:
            self.updated_at = now
        if not self.docket_hash:
            blob = f"{self.case_number}:{self.case_type.value}:{self.title}"
            self.docket_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_number": self.case_number,
            "case_type": self.case_type.value,
            "title": self.title,
            "parties": self.parties,
            "policy_area": self.policy_area,
            "status": self.status.value,
            "reference_id": self.reference_id,
            "opened_at": self.opened_at,
            "updated_at": self.updated_at,
            "closed_at": self.closed_at,
            "outcome": self.outcome,
            "docket_hash": self.docket_hash,
        }


class PublicDocket:
    """Manages the public docket of constitutional proceedings."""

    def __init__(self) -> None:
        self._entries: list[DocketEntry] = []
        self._counter: int = 0

    def _next_case_number(self, case_type: CaseType) -> str:
        self._counter += 1
        prefix = case_type.value[:3].upper()
        return f"{prefix}-2026-{self._counter:04d}"

    def open_case(
        self,
        case_type: CaseType,
        title: str,
        parties: list[str],
        policy_area: str = "",
        reference_id: str = "",
    ) -> DocketEntry:
        """Open a new case on the public docket."""
        entry = DocketEntry(
            case_number=self._next_case_number(case_type),
            case_type=case_type,
            title=title,
            parties=parties,
            policy_area=policy_area,
            reference_id=reference_id,
        )
        self._entries.append(entry)
        return entry

    def update_status(self, case_number: str, status: CaseStatus) -> bool:
        """Update the status of a docketed case."""
        for e in self._entries:
            if e.case_number == case_number:
                e.status = status
                e.updated_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def close_case(self, case_number: str, outcome: str) -> bool:
        """Close a case with an outcome."""
        for e in self._entries:
            if e.case_number == case_number:
                e.status = CaseStatus.CLOSED
                e.outcome = outcome
                now = datetime.now(timezone.utc).isoformat()
                e.updated_at = now
                e.closed_at = now
                return True
        return False

    def dismiss_case(self, case_number: str, reason: str) -> bool:
        """Dismiss a case."""
        for e in self._entries:
            if e.case_number == case_number:
                e.status = CaseStatus.DISMISSED
                e.outcome = f"Dismissed: {reason}"
                now = datetime.now(timezone.utc).isoformat()
                e.updated_at = now
                e.closed_at = now
                return True
        return False

    def get_case(self, case_number: str) -> DocketEntry | None:
        for e in self._entries:
            if e.case_number == case_number:
                return e
        return None

    def search(
        self,
        case_type: CaseType | None = None,
        status: CaseStatus | None = None,
        party: str | None = None,
        policy_area: str | None = None,
        reference_id: str | None = None,
        query: str | None = None,
    ) -> list[DocketEntry]:
        """Search docket entries with optional filters."""
        result = list(self._entries)
        if case_type is not None:
            result = [e for e in result if e.case_type == case_type]
        if status is not None:
            result = [e for e in result if e.status == status]
        if party is not None:
            result = [e for e in result if party in e.parties]
        if policy_area is not None:
            result = [e for e in result if e.policy_area == policy_area]
        if reference_id is not None:
            result = [e for e in result if e.reference_id == reference_id]
        if query is not None:
            q = query.lower()
            result = [
                e for e in result
                if q in e.title.lower()
                or q in e.outcome.lower()
                or q in e.policy_area.lower()
            ]
        return result

    @property
    def case_count(self) -> int:
        return len(self._entries)

    @property
    def open_count(self) -> int:
        closed = {CaseStatus.CLOSED, CaseStatus.DISMISSED}
        return sum(1 for e in self._entries if e.status not in closed)

    def get_summary(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for e in self._entries:
            by_type[e.case_type.value] = by_type.get(e.case_type.value, 0) + 1
            by_status[e.status.value] = by_status.get(e.status.value, 0) + 1
        return {
            "total_cases": len(self._entries),
            "open_cases": self.open_count,
            "by_type": by_type,
            "by_status": by_status,
        }


_docket: PublicDocket | None = None


def get_public_docket() -> PublicDocket:
    """Module singleton."""
    global _docket
    if _docket is None:
        _docket = PublicDocket()
    return _docket
