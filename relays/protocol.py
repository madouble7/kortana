#!/usr/bin/env python3
"""Structured inter-agent protocol primitives for Kor'tana relays."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
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
    return datetime.now(UTC).isoformat()


def append_text_line(path: str | Path, line: str, encoding: str = "utf-8") -> None:
    """Append a full line with one low-level write for safer multi-process usage."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = line if line.endswith("\n") else f"{line}\n"
    data = payload.encode(encoding)

    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY

    fd = os.open(str(target), flags)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def tail_text_lines(
    path: str | Path,
    offset: int,
    remainder: str = "",
    encoding: str = "utf-8",
) -> tuple[list[str], int, str]:
    """Read only newly appended complete lines from a text file."""
    target = Path(path)
    if not target.exists():
        return [], 0, ""

    next_offset = max(0, int(offset))
    next_remainder = remainder

    with open(target, encoding=encoding) as f:
        size = target.stat().st_size
        if next_offset > size:
            next_offset = 0
            next_remainder = ""
        f.seek(next_offset)
        chunk = f.read()
        next_offset = f.tell()

    if not chunk and not next_remainder:
        return [], next_offset, next_remainder

    merged = f"{next_remainder}{chunk}"
    lines = merged.splitlines()
    if merged and not merged.endswith(("\n", "\r")):
        next_remainder = lines.pop() if lines else merged
    else:
        next_remainder = ""

    return lines, next_offset, next_remainder


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
