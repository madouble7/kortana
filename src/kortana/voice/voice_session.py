"""Voice session lifecycle management."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any


@dataclass
class VoiceSession:
    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    turn_count: int = 0
    interrupted: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class VoiceSessionManager:
    """In-memory voice session manager."""

    def __init__(self):
        self._sessions: dict[str, VoiceSession] = {}
        self._lock = Lock()

    def get_or_create(
        self, session_id: str | None, user_id: str | None
    ) -> VoiceSession:
        with self._lock:
            if session_id and session_id in self._sessions:
                session = self._sessions[session_id]
                session.last_activity_at = datetime.now(UTC)
                return session

            new_session = VoiceSession(
                session_id=session_id or str(uuid.uuid4()),
                user_id=user_id or "default",
            )
            self._sessions[new_session.session_id] = new_session
            return new_session

    def mark_turn(self, session_id: str) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return
            session.turn_count += 1
            session.last_activity_at = datetime.now(UTC)

    def mark_interrupted(self, session_id: str, interrupted: bool = True) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.interrupted = interrupted
