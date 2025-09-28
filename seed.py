"""Utility script for seeding experience points into the Kor'tana database."""
from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

DEFAULT_AMOUNTS: dict[str, int] = {"focus": 1, "bond": 1, "relief": 1}
SUPPORTED_FIELDS = set(DEFAULT_AMOUNTS)


@dataclass(slots=True, frozen=True)
class SeedResult:
    """Structured return type for seed operations."""

    focus: int
    bond: int
    relief: int
    log_id: int

    def as_dict(self) -> dict[str, int]:
        return {"focus": self.focus, "bond": self.bond, "relief": self.relief}


def _ensure_tables(connection: sqlite3.Connection) -> None:
    """Create tables used for XP tracking if they do not already exist."""

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS xp_totals (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            focus INTEGER NOT NULL DEFAULT 0,
            bond INTEGER NOT NULL DEFAULT 0,
            relief INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    connection.execute("INSERT OR IGNORE INTO xp_totals (id) VALUES (1)")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS xp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            focus INTEGER NOT NULL,
            bond INTEGER NOT NULL,
            relief INTEGER NOT NULL,
            payload TEXT,
            created_at TEXT NOT NULL
        )
        """
    )


def _coerce_amounts(pairs: Iterable[str]) -> dict[str, int]:
    """Parse CLI pairs like ("focus", "5") into a dictionary."""

    amounts: dict[str, int] = {}
    iterator = iter(pairs)
    for key in iterator:
        try:
            value = next(iterator)
        except StopIteration as exc:  # pragma: no cover - defensive guard
            raise ValueError("XP arguments must be provided in <name> <amount> pairs") from exc

        field = key.lower()
        if field not in SUPPORTED_FIELDS:
            raise ValueError(
                f"Unsupported XP field '{key}'. Supported fields: {', '.join(sorted(SUPPORTED_FIELDS))}."
            )

        try:
            amounts[field] = int(value)
        except ValueError as exc:  # pragma: no cover - validated by argparse
            raise ValueError(f"Amount for '{key}' must be an integer, got: {value!r}") from exc

    return amounts


def seed_xp(db_path: str | Path = "kortana.db", amounts: dict[str, int] | None = None) -> SeedResult:
    """Seed experience points into the database.

    Args:
        db_path: Path to the SQLite database.
        amounts: Optional mapping of XP increments.

    Returns:
        SeedResult describing the totals after seeding and log identifier.
    """

    increments = {**DEFAULT_AMOUNTS}
    if amounts:
        increments.update(amounts)

    db_location = Path(db_path)
    db_location.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_location) as connection:
        connection.row_factory = sqlite3.Row
        _ensure_tables(connection)

        connection.execute(
            """
            UPDATE xp_totals
            SET focus = focus + ?,
                bond = bond + ?,
                relief = relief + ?
            WHERE id = 1
            """,
            (
                increments["focus"],
                increments["bond"],
                increments["relief"],
            ),
        )

        row = connection.execute(
            "SELECT focus, bond, relief FROM xp_totals WHERE id = 1"
        ).fetchone()
        assert row is not None, "xp_totals should always contain row with id=1"

        payload = json.dumps({"increments": increments})
        timestamp = datetime.now(UTC).isoformat()
        cursor = connection.execute(
            """
            INSERT INTO xp_logs (event_type, focus, bond, relief, payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "seed",
                row["focus"],
                row["bond"],
                row["relief"],
                payload,
                timestamp,
            ),
        )

    result = SeedResult(
        focus=int(row["focus"]),
        bond=int(row["bond"]),
        relief=int(row["relief"]),
        log_id=cursor.lastrowid,
    )

    print(
        "[XP] Seed complete -> focus={focus}, bond={bond}, relief={relief}".format(
            **result.as_dict()
        )
    )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed XP totals for Kor'tana")
    parser.add_argument(
        "pairs",
        nargs="*",
        metavar=("field", "amount"),
        help="Pairs of XP field names and integer amounts (e.g. focus 5 bond 2)",
    )
    parser.add_argument(
        "--db",
        default="kortana.db",
        help="Path to the Kor'tana SQLite database (default: %(default)s)",
    )

    args = parser.parse_args()

    try:
        user_amounts = _coerce_amounts(args.pairs) if args.pairs else None
    except ValueError as exc:
        parser.error(str(exc))
        return

    seed_xp(db_path=args.db, amounts=user_amounts)


if __name__ == "__main__":
    main()
