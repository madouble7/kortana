"""Experience point (XP) tracking utilities for Kortana.

This module manages a lightweight SQLite database that keeps track of
XP "bars" along with a log of changes for debugging purposes.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

_DB_LOCK = threading.Lock()
_DB_PATH = Path(__file__).resolve().parent / "kortana.db"


def _initialise_database() -> None:
    """Create the SQLite database and required tables if they don't exist."""
    with _DB_LOCK:
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS xp_bars (
                    name TEXT PRIMARY KEY,
                    xp INTEGER NOT NULL DEFAULT 0,
                    last_nudged_at REAL NOT NULL DEFAULT 0,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    change INTEGER NOT NULL,
                    old_xp INTEGER NOT NULL,
                    new_xp INTEGER NOT NULL,
                    logged_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )


# Ensure the database structure exists as soon as the module is imported.
_initialise_database()


@contextmanager
def _get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection with row factory configured."""
    with sqlite3.connect(_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        yield conn


def ensure_bar(bar_name: str) -> None:
    """Ensure a bar exists in the database without altering its XP."""
    if not bar_name:
        raise ValueError("bar_name must be a non-empty string")

    with _DB_LOCK:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO xp_bars (name)
                VALUES (?)
                ON CONFLICT(name) DO NOTHING
                """,
                (bar_name,),
            )


def get_xp(bar_name: str) -> int:
    """Return the current XP value for a specific bar."""
    ensure_bar(bar_name)
    with _DB_LOCK:
        with _get_connection() as conn:
            row = conn.execute(
                "SELECT xp FROM xp_bars WHERE name = ?",
                (bar_name,),
            ).fetchone()
            return int(row["xp"]) if row else 0


def update_xp(bar_name: str, amount: int, *, absolute: bool = False) -> int:
    """Update XP for the provided bar, clamping between 0 and 100.

    Args:
        bar_name: The name of the XP bar to adjust.
        amount: Either the new absolute XP value (when ``absolute`` is True)
            or the delta to apply.
        absolute: When True, ``amount`` is treated as the target XP value.

    Returns:
        The updated XP value after clamping between 0 and 100.
    """
    if not bar_name:
        raise ValueError("bar_name must be a non-empty string")

    ensure_bar(bar_name)

    with _DB_LOCK:
        with _get_connection() as conn:
            row = conn.execute(
                "SELECT xp FROM xp_bars WHERE name = ?",
                (bar_name,),
            ).fetchone()
            current_xp = int(row["xp"]) if row else 0

            target = amount if absolute else current_xp + amount
            clamped = max(0, min(100, target))

            if clamped != current_xp:
                conn.execute(
                    """
                    UPDATE xp_bars
                    SET xp = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                    """,
                    (clamped, bar_name),
                )
                conn.execute(
                    """
                    INSERT INTO logs (name, change, old_xp, new_xp)
                    VALUES (?, ?, ?, ?)
                    """,
                    (bar_name, clamped - current_xp, current_xp, clamped),
                )

            return clamped


def get_next_nudge() -> Optional[Dict[str, Any]]:
    """Return the next XP bar that should receive a nudge.

    The bar with the lowest XP is prioritised. When multiple bars share the
    same XP value, the bar that has gone the longest without being nudged is
    selected (based on ``last_nudged_at``). This ensures deterministic rotation
    across ties.

    Returns:
        A dictionary with ``name`` and ``xp`` keys if a bar exists, otherwise
        ``None``.
    """
    with _DB_LOCK:
        with _get_connection() as conn:
            row = conn.execute(
                """
                SELECT name, xp, last_nudged_at
                FROM xp_bars
                ORDER BY xp ASC, last_nudged_at ASC, name ASC
                LIMIT 1
                """
            ).fetchone()

            if row is None:
                return None

            now = time.time()
            conn.execute(
                """
                UPDATE xp_bars
                SET last_nudged_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
                """,
                (now, row["name"]),
            )

            return {"name": row["name"], "xp": int(row["xp"])}


def get_logs(limit: int = 10) -> list[Dict[str, Any]]:
    """Fetch the most recent XP change logs for debugging."""
    if limit <= 0:
        raise ValueError("limit must be a positive integer")

    with _DB_LOCK:
        with _get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, name, change, old_xp, new_xp, logged_at
                FROM logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]


__all__ = [
    "ensure_bar",
    "get_logs",
    "get_next_nudge",
    "get_xp",
    "update_xp",
]
