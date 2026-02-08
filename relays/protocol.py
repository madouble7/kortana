#!/usr/bin/env python3
"""Structured inter-agent protocol primitives for Kor'tana relays."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


EVENT_TYPES = {
    "TASK_ASSIGN",
    "TASK_CLAIM",
    "TASK_UPDATE",
    "BLOCKER",
    "REQUEST_REVIEW",
    "MERGE_READY",
    "DIRECTIVE",
    "HEARTBEAT",
    "ACK",
    "INFO",
}


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


@dataclass
class AgentEvent:
    id: str
    timestamp: str
    source: str
    target: str
    event_type: str
    task_id: str | None = None
    priority: str = "normal"
    payload: dict[str, Any] | None = None
    requires_ack: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "source": self.source,
            "target": self.target,
            "event_type": self.event_type,
            "task_id": self.task_id,
            "priority": self.priority,
            "payload": self.payload or {},
            "requires_ack": self.requires_ack,
        }

    def to_json_line(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def new(
        cls,
        source: str,
        target: str,
        event_type: str,
        task_id: str | None = None,
        priority: str = "normal",
        payload: dict[str, Any] | None = None,
        requires_ack: bool = False,
    ) -> "AgentEvent":
        normalized_type = event_type.upper()
        if normalized_type not in EVENT_TYPES:
            normalized_type = "INFO"

        return cls(
            id=str(uuid.uuid4()),
            timestamp=utc_now_iso(),
            source=source,
            target=target,
            event_type=normalized_type,
            task_id=task_id,
            priority=priority,
            payload=payload or {},
            requires_ack=requires_ack,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentEvent":
        event_type = str(data.get("event_type", "INFO")).upper()
        if event_type not in EVENT_TYPES:
            event_type = "INFO"

        return cls(
            id=str(data.get("id") or str(uuid.uuid4())),
            timestamp=str(data.get("timestamp") or utc_now_iso()),
            source=str(data.get("source") or "unknown"),
            target=str(data.get("target") or "all"),
            event_type=event_type,
            task_id=str(data.get("task_id")) if data.get("task_id") else None,
            priority=str(data.get("priority") or "normal"),
            payload=data.get("payload") if isinstance(data.get("payload"), dict) else {},
            requires_ack=bool(data.get("requires_ack", False)),
        )


def parse_event_line(line: str) -> AgentEvent | None:
    """Parse one queue/log line into structured AgentEvent when possible."""
    text = line.strip()
    if not text:
        return None

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return AgentEvent.from_dict(data)
    except json.JSONDecodeError:
        return None

    return None
