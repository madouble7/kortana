"""V21D — evolution observer: makes policy evolution observable and auditable."""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(Enum):
    """Types of events in the policy evolution lifecycle."""

    PROPOSAL_CREATED = "proposal_created"
    PROPOSAL_SUBMITTED = "proposal_submitted"
    REVIEW_STARTED = "review_started"
    PROPOSAL_APPROVED = "proposal_approved"
    PROPOSAL_REJECTED = "proposal_rejected"
    PROPOSAL_PROMOTED = "proposal_promoted"
    PROPOSAL_WITHDRAWN = "proposal_withdrawn"
    ROLLBACK_CREATED = "rollback_created"
    ROLLBACK_EXECUTED = "rollback_executed"
    APPROVAL_AUTO = "approval_auto"
    APPROVAL_HUMAN = "approval_human"
    POLICY_APPLIED = "policy_applied"


@dataclass
class EvolutionEvent:
    """A single observable event in the evolution timeline."""

    event_id: str
    event_type: EventType
    subject_id: str
    details: dict[str, Any]
    timestamp: str = ""
    event_hash: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.event_hash:
            blob = f"{self.event_id}:{self.event_type.value}:{self.subject_id}"
            self.event_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "subject_id": self.subject_id,
            "details": self.details,
            "timestamp": self.timestamp,
            "event_hash": self.event_hash,
        }


class EvolutionObserver:
    """Observes and records all events in the policy evolution lifecycle."""

    def __init__(self) -> None:
        self._timeline: list[EvolutionEvent] = []
        self._subscribers: dict[str, Callable[[EvolutionEvent], None]] = {}

    def emit(
        self,
        event_type: EventType,
        subject_id: str,
        details: dict[str, Any] | None = None,
    ) -> EvolutionEvent:
        """Emit an evolution event and notify subscribers."""
        event = EvolutionEvent(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            subject_id=subject_id,
            details=details or {},
        )
        self._timeline.append(event)
        self._notify(event)
        return event

    def get_timeline(self, limit: int = 0) -> list[EvolutionEvent]:
        """Get the full timeline or last N events."""
        if limit > 0:
            return list(self._timeline[-limit:])
        return list(self._timeline)

    def get_events_by_type(self, event_type: EventType) -> list[EvolutionEvent]:
        return [e for e in self._timeline if e.event_type == event_type]

    def get_events_for_subject(self, subject_id: str) -> list[EvolutionEvent]:
        return [e for e in self._timeline if e.subject_id == subject_id]

    def get_audit_trail(self) -> dict[str, Any]:
        """Get a summary audit trail of all evolution activity."""
        type_counts: dict[str, int] = {}
        for e in self._timeline:
            key = e.event_type.value
            type_counts[key] = type_counts.get(key, 0) + 1

        subjects: set[str] = {e.subject_id for e in self._timeline}

        return {
            "total_events": len(self._timeline),
            "event_type_counts": type_counts,
            "unique_subjects": len(subjects),
            "first_event": self._timeline[0].timestamp if self._timeline else None,
            "last_event": self._timeline[-1].timestamp if self._timeline else None,
        }

    def subscribe(self, callback: Callable[[EvolutionEvent], None]) -> str:
        """Subscribe to evolution events. Returns subscription ID."""
        sub_id = f"sub-{uuid.uuid4().hex[:8]}"
        self._subscribers[sub_id] = callback
        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        if subscription_id in self._subscribers:
            del self._subscribers[subscription_id]
            return True
        return False

    @property
    def event_count(self) -> int:
        return len(self._timeline)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def _notify(self, event: EvolutionEvent) -> None:
        for callback in self._subscribers.values():
            try:
                callback(event)
            except Exception:
                pass


_observer: EvolutionObserver | None = None


def get_evolution_observer() -> EvolutionObserver:
    """Module singleton."""
    global _observer
    if _observer is None:
        _observer = EvolutionObserver()
    return _observer
