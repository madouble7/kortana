"""SQLite-backed experience point tracking utility.

This module provides helpers for tracking three experience bars and logging
activity in a small SQLite database.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

DB_PATH = Path(__file__).with_suffix(".db")
XP_COLUMNS: Tuple[str, ...] = ("focus_xp", "bond_xp", "relief_xp")

SUGGESTIONS: Dict[str, str] = {
    "focus_xp": "Focus is lagging—plan a deep work block to get back on track.",
    "bond_xp": "Bond is the lowest—reach out and nurture an important connection.",
    "relief_xp": "Relief needs attention—take a break to recharge and breathe.",
}


@contextmanager
def get_connection():
    """Context manager yielding a SQLite connection with WAL journaling enabled."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Initialise the SQLite schema and ensure default XP row exists."""

    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS xp_bars (
                focus_xp INTEGER NOT NULL DEFAULT 0,
                bond_xp INTEGER NOT NULL DEFAULT 0,
                relief_xp INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                notes TEXT
            )
            """
        )
        cur = conn.execute("SELECT COUNT(*) FROM xp_bars")
        if cur.fetchone()[0] == 0:
            conn.execute("INSERT INTO xp_bars DEFAULT VALUES")
            conn.execute(
                "INSERT INTO logs (timestamp, event_type, notes) VALUES (?, ?, ?)",
                (
                    datetime.utcnow().isoformat(),
                    "init",
                    "Initial XP row created with default values.",
                ),
            )


def update_xp(bar_name: str, amount: int) -> int:
    """Adjust the specified XP bar by *amount* while preventing negative totals."""

    if bar_name not in XP_COLUMNS:
        raise ValueError(f"Unknown XP bar '{bar_name}'. Expected one of {XP_COLUMNS}.")

    init_db()

    with get_connection() as conn:
        cur = conn.execute("SELECT focus_xp, bond_xp, relief_xp FROM xp_bars LIMIT 1")
        row = cur.fetchone()
        if row is None:
            # Should not happen due to init_db, but handle defensively.
            conn.execute("INSERT INTO xp_bars DEFAULT VALUES")
            row = (0, 0, 0)

        current_value = row[XP_COLUMNS.index(bar_name)]
        new_value = current_value + amount
        if new_value < 0:
            amount = -current_value
            new_value = 0

        conn.execute(f"UPDATE xp_bars SET {bar_name} = ?", (new_value,))
        conn.execute(
            "INSERT INTO logs (timestamp, event_type, notes) VALUES (?, ?, ?)",
            (
                datetime.utcnow().isoformat(),
                "xp_update",
                f"{bar_name} adjusted by {amount}. New value: {new_value}.",
            ),
        )

    return new_value


def get_next_nudge() -> str:
    """Return a suggestion string focused on the lowest XP bar."""

    init_db()

    with get_connection() as conn:
        cur = conn.execute("SELECT focus_xp, bond_xp, relief_xp FROM xp_bars LIMIT 1")
        row = cur.fetchone()

    if not row:
        return "All XP bars are at baseline—pick any area to cultivate today."

    xp_pairs = list(zip(XP_COLUMNS, row))
    min_value = min(value for _, value in xp_pairs)
    lowest_bars = [name for name, value in xp_pairs if value == min_value]

    if len(lowest_bars) == 1:
        bar = lowest_bars[0]
        suggestion = SUGGESTIONS.get(bar)
        if suggestion:
            return suggestion
        return f"{bar.replace('_', ' ').title()} needs attention—invest some energy there."

    readable = ", ".join(name.replace("_", " ") for name in lowest_bars)
    return (
        f"Multiple areas ({readable}) are tied for lowest XP—plan actions that boost each."
    )
