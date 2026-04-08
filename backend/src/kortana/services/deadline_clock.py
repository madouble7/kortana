"""V24B — deadline clock: procedural time limits for constitutional actions."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any


class DeadlineType(Enum):
    """Types of procedural deadlines."""

    APPEAL_FILING = "appeal_filing"
    APPEAL_REVIEW = "appeal_review"
    APPEAL_DECISION = "appeal_decision"
    WAIVER_REVIEW = "waiver_review"
    EMERGENCY_REVIEW = "emergency_review"
    QUORUM_VOTING = "quorum_voting"
    WAIVER_EXPIRATION = "waiver_expiration"
    REASONING_PUBLICATION = "reasoning_publication"


class DeadlineStatus(Enum):
    """Status of a deadline."""

    PENDING = "pending"
    MET = "met"
    MISSED = "missed"
    EXTENDED = "extended"
    CANCELLED = "cancelled"


# Default hours for each deadline type
DEFAULT_HOURS: dict[str, int] = {
    "appeal_filing": 48,
    "appeal_review": 72,
    "appeal_decision": 96,
    "waiver_review": 24,
    "emergency_review": 48,
    "quorum_voting": 72,
    "waiver_expiration": 72,
    "reasoning_publication": 24,
}

MAX_EXTENSIONS = 2
MAX_EXTENSION_HOURS = 48


@dataclass
class Deadline:
    """A procedural deadline with expiration tracking."""

    deadline_id: str
    reference_id: str
    deadline_type: DeadlineType
    created_at: str = ""
    due_at: str = ""
    met_at: str = ""
    status: DeadlineStatus = DeadlineStatus.PENDING
    extensions: int = 0
    original_due_at: str = ""
    deadline_hash: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.due_at:
            hours = DEFAULT_HOURS.get(self.deadline_type.value, 48)
            due = datetime.fromisoformat(self.created_at) + timedelta(hours=hours)
            self.due_at = due.isoformat()
        if not self.original_due_at:
            self.original_due_at = self.due_at
        if not self.deadline_hash:
            blob = f"{self.deadline_id}:{self.reference_id}:{self.deadline_type.value}"
            self.deadline_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    @property
    def is_overdue(self) -> bool:
        if self.status != DeadlineStatus.PENDING:
            return False
        return datetime.now(timezone.utc) > datetime.fromisoformat(self.due_at)

    @property
    def remaining_hours(self) -> float:
        if self.status != DeadlineStatus.PENDING:
            return 0.0
        remaining = datetime.fromisoformat(self.due_at) - datetime.now(timezone.utc)
        return max(0.0, round(remaining.total_seconds() / 3600, 2))

    def to_dict(self) -> dict[str, Any]:
        return {
            "deadline_id": self.deadline_id,
            "reference_id": self.reference_id,
            "deadline_type": self.deadline_type.value,
            "created_at": self.created_at,
            "due_at": self.due_at,
            "original_due_at": self.original_due_at,
            "met_at": self.met_at,
            "status": self.status.value,
            "extensions": self.extensions,
            "is_overdue": self.is_overdue,
            "remaining_hours": self.remaining_hours,
            "deadline_hash": self.deadline_hash,
        }


class DeadlineClock:
    """Manages procedural deadlines for constitutional actions."""

    def __init__(self) -> None:
        self._deadlines: list[Deadline] = []

    def create_deadline(
        self,
        reference_id: str,
        deadline_type: DeadlineType,
        hours: int | None = None,
    ) -> Deadline:
        """Create a new procedural deadline."""
        now = datetime.now(timezone.utc)
        h = hours if hours is not None else DEFAULT_HOURS.get(deadline_type.value, 48)
        due = now + timedelta(hours=h)
        deadline = Deadline(
            deadline_id=f"dl-{uuid.uuid4().hex[:12]}",
            reference_id=reference_id,
            deadline_type=deadline_type,
            created_at=now.isoformat(),
            due_at=due.isoformat(),
            original_due_at=due.isoformat(),
        )
        self._deadlines.append(deadline)
        return deadline

    def meet_deadline(self, deadline_id: str) -> bool:
        """Mark a deadline as met."""
        for d in self._deadlines:
            if d.deadline_id == deadline_id and d.status == DeadlineStatus.PENDING:
                d.status = DeadlineStatus.MET
                d.met_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def extend_deadline(self, deadline_id: str, extra_hours: int = 24) -> bool:
        """Extend a pending deadline. Max 2 extensions, max 48h per extension."""
        for d in self._deadlines:
            if d.deadline_id == deadline_id and d.status == DeadlineStatus.PENDING:
                if d.extensions >= MAX_EXTENSIONS:
                    return False
                extra = min(extra_hours, MAX_EXTENSION_HOURS)
                new_due = datetime.fromisoformat(d.due_at) + timedelta(hours=extra)
                d.due_at = new_due.isoformat()
                d.extensions += 1
                d.status = DeadlineStatus.EXTENDED if d.extensions > 0 else DeadlineStatus.PENDING
                d.status = DeadlineStatus.PENDING  # back to pending after extension
                return True
        return False

    def cancel_deadline(self, deadline_id: str) -> bool:
        """Cancel a deadline."""
        for d in self._deadlines:
            if d.deadline_id == deadline_id and d.status == DeadlineStatus.PENDING:
                d.status = DeadlineStatus.CANCELLED
                return True
        return False

    def expire_deadlines(self) -> int:
        """Mark all overdue deadlines as missed. Returns count."""
        now = datetime.now(timezone.utc)
        count = 0
        for d in self._deadlines:
            if d.status == DeadlineStatus.PENDING:
                if now > datetime.fromisoformat(d.due_at):
                    d.status = DeadlineStatus.MISSED
                    count += 1
        return count

    def get_deadline(self, deadline_id: str) -> Deadline | None:
        for d in self._deadlines:
            if d.deadline_id == deadline_id:
                return d
        return None

    def get_deadlines(
        self,
        reference_id: str | None = None,
        deadline_type: DeadlineType | None = None,
        status: DeadlineStatus | None = None,
        pending_only: bool = False,
    ) -> list[Deadline]:
        result = list(self._deadlines)
        if reference_id is not None:
            result = [d for d in result if d.reference_id == reference_id]
        if deadline_type is not None:
            result = [d for d in result if d.deadline_type == deadline_type]
        if status is not None:
            result = [d for d in result if d.status == status]
        if pending_only:
            result = [d for d in result if d.status == DeadlineStatus.PENDING]
        return result

    @property
    def deadline_count(self) -> int:
        return len(self._deadlines)

    @property
    def pending_count(self) -> int:
        return sum(1 for d in self._deadlines if d.status == DeadlineStatus.PENDING)

    @property
    def missed_count(self) -> int:
        return sum(1 for d in self._deadlines if d.status == DeadlineStatus.MISSED)

    def get_summary(self) -> dict[str, Any]:
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for d in self._deadlines:
            by_status[d.status.value] = by_status.get(d.status.value, 0) + 1
            by_type[d.deadline_type.value] = by_type.get(d.deadline_type.value, 0) + 1
        return {
            "total_deadlines": len(self._deadlines),
            "pending": self.pending_count,
            "missed": self.missed_count,
            "by_status": by_status,
            "by_type": by_type,
            "max_extensions": MAX_EXTENSIONS,
            "max_extension_hours": MAX_EXTENSION_HOURS,
        }


_clock: DeadlineClock | None = None


def get_deadline_clock() -> DeadlineClock:
    """Module singleton."""
    global _clock
    if _clock is None:
        _clock = DeadlineClock()
    return _clock
