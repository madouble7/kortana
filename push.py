"""Utilities for handling push notifications and persisting them."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

DB_PATH = Path(__file__).resolve().with_name("kortana.db")
_Priority = Literal["low", "med", "high"]


def _ensure_logs_table(conn: sqlite3.Connection) -> None:
    """Ensure the logs table exists with the fields required for push notes."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            priority TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


def _normalise_priority(priority: str | None) -> _Priority:
    """Normalise and validate the priority string."""
    if priority is None:
        priority = "med"
    normalised = priority.strip().lower()
    if normalised not in {"low", "med", "high"}:
        raise ValueError("priority must be one of: low, med, high")
    return normalised  # type: ignore[return-value]


def push_notification(
    title: str,
    message: str,
    priority: str | None = None,
    *,
    db_path: Path | None = None,
) -> None:
    """Send a push notification, log it to stdout, and persist it."""
    resolved_priority = _normalise_priority(priority)
    print(
        f"***PUSH NOTE*** title: {title} | message: {message} | priority: {resolved_priority}"
    )

    path = Path(db_path) if db_path is not None else DB_PATH
    conn = sqlite3.connect(path)
    try:
        _ensure_logs_table(conn)
        conn.execute(
            """
            INSERT INTO logs (event_type, title, message, priority, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "push",
                title,
                message,
                resolved_priority,
                datetime.now(UTC).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


@dataclass(frozen=True)
class _SamplePush:
    title: str
    message: str
    priority: _Priority


def _sample_pushes() -> Iterable[_SamplePush]:
    """Provide the sample pushes used in simulate_pushes."""
    return (
        _SamplePush("Welcome", "Kor'tana systems initialised.", "low"),
        _SamplePush("Reminder", "Review the latest mission logs.", "med"),
        _SamplePush("Alert", "Autonomous engine requires attention.", "high"),
    )


def simulate_pushes(*, db_path: Path | None = None) -> None:
    """Trigger a few sample push notifications to validate integration."""
    for push in _sample_pushes():
        push_notification(push.title, push.message, push.priority, db_path=db_path)


if __name__ == "__main__":
    simulate_pushes()
