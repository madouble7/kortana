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
                session.last_activity_at = datetime.now(UTC)

    def get_snapshot(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            return self._serialize(session)

    def end_session(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def cleanup_inactive(
        self,
        max_idle_seconds: int = 1800,
        max_active_sessions: int | None = None,
    ) -> int:
        """Purge stale sessions and enforce optional max session cap."""
        now = datetime.now(UTC)
        removed = 0

        with self._lock:
            if max_idle_seconds > 0:
                stale_ids = [
                    sid
                    for sid, session in self._sessions.items()
                    if (now - session.last_activity_at).total_seconds()
                    > max_idle_seconds
                ]
                for sid in stale_ids:
                    self._sessions.pop(sid, None)
                    removed += 1

            if max_active_sessions and max_active_sessions > 0:
                overflow = len(self._sessions) - max_active_sessions
                if overflow > 0:
                    oldest = sorted(
                        self._sessions.items(),
                        key=lambda item: item[1].last_activity_at,
                    )
                    for sid, _ in oldest[:overflow]:
                        self._sessions.pop(sid, None)
                        removed += 1

        return removed

    def _serialize(self, session: VoiceSession) -> dict[str, Any]:
        now = datetime.now(UTC)
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "turn_count": session.turn_count,
            "interrupted": session.interrupted,
            "created_at": session.created_at.isoformat(),
            "last_activity_at": session.last_activity_at.isoformat(),
            "idle_seconds": round(
                (now - session.last_activity_at).total_seconds(),
                3,
            ),
            "age_seconds": round((now - session.created_at).total_seconds(), 3),
            "metadata": dict(session.metadata),
        }
