"""Integration harness for Kor'tana experience seeding and nudging."""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Final

try:  # Optional dependency for full configuration support
    from config import load_config
except Exception:  # pragma: no cover - falls back when config deps missing
    load_config = None  # type: ignore[assignment]

from seed import seed_xp
from scripts.init_db import init_kortana_db

_DB_DEFAULT: Final[str] = "kortana.db"


def _get_connection(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def get_totals(db_path: str | Path) -> dict[str, int]:
    with _get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT focus, bond, relief FROM xp_totals WHERE id = 1"
        ).fetchone()
    if row is None:
        return {"focus": 0, "bond": 0, "relief": 0}
    return {key: int(row[key]) for key in ("focus", "bond", "relief")}


def get_next_nudge(db_path: str | Path) -> dict[str, Any]:
    totals = get_totals(db_path)
    dominant_metric = max(totals, key=totals.get)

    motivations = {
        "focus": "Channel the clarity you've been cultivating. Take a dedicated 5-minute scan of today's goals.",
        "bond": "Reach out with a message of appreciation. Small acts grow the bond you value most.",
        "relief": "Give yourself permission to breathe. A brief pause will amplify the calm you've earned.",
    }

    message = motivations.get(
        dominant_metric,
        "Notice how each stat is growing. Choose the one that resonates and give it attention today.",
    )

    return {
        "totals": totals,
        "dominant": dominant_metric,
        "message": message,
    }


def push_notification(nudge: dict[str, Any]) -> None:
    print("\n[NOTIFICATION]")
    print(f"Dominant focus: {nudge['dominant']}")
    print(nudge["message"])


def _iter_logs(connection: sqlite3.Connection, limit: int) -> Iterable[sqlite3.Row]:
    cursor = connection.execute(
        """
        SELECT id, event_type, focus, bond, relief, payload, created_at
        FROM xp_logs
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    # Display oldest first within the limited window for readability
    return reversed(rows)


def print_logs(db_path: str | Path, limit: int) -> None:
    print("\n[XP LOGS]")
    with _get_connection(db_path) as connection:
        rows = list(_iter_logs(connection, limit))
        if not rows:
            print("No XP log entries recorded yet.")
            return
        for row in rows:
            payload = json.loads(row["payload"]) if row["payload"] else {}
            increments = payload.get("increments", {})
            print(
                f"#{row['id']:03d} {row['created_at']} "
                f"event={row['event_type']} totals(focus={row['focus']}, bond={row['bond']}, relief={row['relief']}) "
                f"delta={increments}"
            )


def _resolve_log_limit(config_obj: Any) -> int:
    if config_obj is None:
        return 50

    for attribute in ("log_limit",):
        if hasattr(config_obj, attribute):
            value = getattr(config_obj, attribute)
            if isinstance(value, int) and value > 0:
                return value

    if hasattr(config_obj, "logging") and hasattr(config_obj.logging, "log_limit"):
        value = getattr(config_obj.logging, "log_limit")
        if isinstance(value, int) and value > 0:
            return value

    return 50


def run_flow(db_path: str | Path, seed_overrides: dict[str, int] | None = None) -> None:
    config_obj = load_config() if callable(load_config) else None
    log_limit = _resolve_log_limit(config_obj)

    print("[STEP] init_db()")
    init_kortana_db(str(db_path))

    print("[STEP] seed.py")
    result = seed_xp(db_path=db_path, amounts=seed_overrides)

    print("[STEP] get_next_nudge()")
    nudge = get_next_nudge(db_path)

    print("[STEP] push_notification()")
    push_notification(nudge)

    print_logs(db_path, log_limit)

    print(
        "focus={focus}, bond={bond}, relief={relief}".format(
            focus=result.focus,
            bond=result.bond,
            relief=result.relief,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Kor'tana XP flow test")
    parser.add_argument(
        "--db",
        default=_DB_DEFAULT,
        help="Path to the Kor'tana SQLite database (default: %(default)s)",
    )
    parser.add_argument(
        "pairs",
        nargs="*",
        metavar=("field", "amount"),
        help="Optional XP overrides passed to seed.py (e.g. focus 5 bond 3)",
    )

    args = parser.parse_args()

    seed_overrides = None
    if args.pairs:
        from seed import _coerce_amounts  # Lazy import to keep CLI parsing aligned

        try:
            seed_overrides = _coerce_amounts(args.pairs)
        except ValueError as exc:
            parser.error(str(exc))
            return

    run_flow(Path(args.db), seed_overrides)


if __name__ == "__main__":
    main()
