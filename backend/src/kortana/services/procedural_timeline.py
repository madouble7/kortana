"""V25B — procedural timeline: ordered event log for constitutional proceedings."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(Enum):
    """Types of procedural events."""

    CASE_OPENED = "case_opened"
    STANDING_CHECKED = "standing_checked"
    DEADLINE_CREATED = "deadline_created"
    DEADLINE_MET = "deadline_met"
    DEADLINE_MISSED = "deadline_missed"
    DEADLINE_EXTENDED = "deadline_extended"
    RECUSAL_DECLARED = "recusal_declared"
    CONFLICT_DETECTED = "conflict_detected"
    VOTE_CAST = "vote_cast"
    DECISION_RENDERED = "decision_rendered"
    REASONING_PUBLISHED = "reasoning_published"
    NOTICE_SENT = "notice_sent"
    NOTICE_ACKNOWLEDGED = "notice_acknowledged"
    CASE_CLOSED = "case_closed"
    CASE_DISMISSED = "case_dismissed"
    STATUS_CHANGED = "status_changed"
    EVIDENCE_SUBMITTED = "evidence_submitted"
    REVIEW_STARTED = "review_started"


@dataclass
class TimelineEvent:
    """A single event in a proceeding's timeline."""

    event_id: str
    case_number: str
    event_type: EventType
    actor: str
    description: str
    timestamp: str = ""
    extra_data: dict[str, Any] = field(default_factory=dict)
    event_hash: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.event_hash:
            blob = f"{self.event_id}:{self.case_number}:{self.event_type.value}:{self.actor}"
            self.event_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "case_number": self.case_number,
            "event_type": self.event_type.value,
            "actor": self.actor,
            "description": self.description,
            "timestamp": self.timestamp,
            "extra_data": self.extra_data,
            "event_hash": self.event_hash,
        }


class ProceduralTimeline:
    """Manages ordered event logs for constitutional proceedings."""

    def __init__(self) -> None:
        self._events: list[TimelineEvent] = []

    def record_event(
        self,
        case_number: str,
        event_type: EventType,
        actor: str,
        description: str,
        extra_data: dict[str, Any] | None = None,
    ) -> TimelineEvent:
        """Record a new event in a proceeding's timeline."""
        event = TimelineEvent(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            case_number=case_number,
            event_type=event_type,
            actor=actor,
            description=description,
            extra_data=extra_data or {},
        )
        self._events.append(event)
        return event

    def get_timeline(
        self,
        case_number: str,
        event_type: EventType | None = None,
        actor: str | None = None,
    ) -> list[TimelineEvent]:
        """Get the timeline for a case, in chronological order."""
        result = [e for e in self._events if e.case_number == case_number]
        if event_type is not None:
            result = [e for e in result if e.event_type == event_type]
        if actor is not None:
            result = [e for e in result if e.actor == actor]
        return sorted(result, key=lambda e: e.timestamp)

    def get_events(
        self,
        event_type: EventType | None = None,
        actor: str | None = None,
        limit: int | None = None,
    ) -> list[TimelineEvent]:
        """Get events across all cases with optional filters."""
        result = list(self._events)
        if event_type is not None:
            result = [e for e in result if e.event_type == event_type]
        if actor is not None:
            result = [e for e in result if e.actor == actor]
        result = sorted(result, key=lambda e: e.timestamp, reverse=True)
        if limit is not None:
            result = result[:limit]
        return result

    def get_event(self, event_id: str) -> TimelineEvent | None:
        for e in self._events:
            if e.event_id == event_id:
                return e
        return None

    @property
    def event_count(self) -> int:
        return len(self._events)

    def case_event_count(self, case_number: str) -> int:
        return sum(1 for e in self._events if e.case_number == case_number)

    def get_summary(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        by_case: dict[str, int] = {}
        for e in self._events:
            by_type[e.event_type.value] = by_type.get(e.event_type.value, 0) + 1
            by_case[e.case_number] = by_case.get(e.case_number, 0) + 1
        return {
            "total_events": len(self._events),
            "distinct_cases": len(by_case),
            "by_event_type": by_type,
            "events_per_case": by_case,
        }


_timeline: ProceduralTimeline | None = None


def get_procedural_timeline() -> ProceduralTimeline:
    """Module singleton."""
    global _timeline
    if _timeline is None:
        _timeline = ProceduralTimeline()
    return _timeline
