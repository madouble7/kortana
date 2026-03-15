"""Kor'tana nudge processing loop."""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

CONFIG_PATH = Path(__file__).with_name("config.json")
DB_PATH = Path(__file__).with_name("kortana.db")
DEFAULT_INTERVAL_SECONDS = 60


def load_config() -> Dict[str, Any]:
    """Load configuration settings from config.json.

    Falls back to defaults if the file is missing or malformed.
    """
    if not CONFIG_PATH.exists():
        logging.warning("config.json not found. Using default settings.")
        return {"nudge_interval_seconds": DEFAULT_INTERVAL_SECONDS}

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except json.JSONDecodeError as exc:
        logging.error("Failed to parse config.json: %s", exc)
        return {"nudge_interval_seconds": DEFAULT_INTERVAL_SECONDS}

    if "nudge_interval_seconds" not in config:
        logging.warning(
            "nudge_interval_seconds missing in config.json. Using default value." 
        )
        config["nudge_interval_seconds"] = DEFAULT_INTERVAL_SECONDS

    return config


def init_db() -> None:
    """Initialize the SQLite database required for the nudge loop."""
    logging.info("Initializing Kor'tana database (nudges + events tables).")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS nudges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                delivered_at TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                notes TEXT
            )
            """
        )
        connection.commit()


def get_next_nudge() -> Optional[Tuple[int, str]]:
    """Fetch the next undelivered nudge from the database.

    Returns the nudge identifier and message when available. Ensures the
    selected nudge is marked as delivered to prevent duplicates when
    restarting the loop.
    """
    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT id, message
                FROM nudges
                WHERE delivered_at IS NULL
                ORDER BY created_at ASC
                LIMIT 1
                """
            ).fetchone()

            if not row:
                return None

            connection.execute(
                "UPDATE nudges SET delivered_at = CURRENT_TIMESTAMP WHERE id = ?",
                (row["id"],),
            )
            connection.commit()
            return row["id"], row["message"]
    except sqlite3.Error as exc:
        logging.exception("Database error retrieving next nudge: %s", exc)
        init_db()
        return None


def push_notification(title: str, message: str) -> None:
    """Send a push notification (currently logs for visibility)."""
    logging.info("Notification: %s - %s", title, message)


def log_event(event_type: str, notes: str) -> None:
    """Record an event in the events table."""
    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute(
                "INSERT INTO events (event_type, notes) VALUES (?, ?)",
                (event_type, notes),
            )
            connection.commit()
    except sqlite3.Error as exc:
        logging.exception("Database error logging event: %s", exc)
        init_db()


def run_loop() -> None:
    """Main loop polling for nudges and dispatching notifications."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    config = load_config()
    interval = max(1, int(config.get("nudge_interval_seconds", DEFAULT_INTERVAL_SECONDS)))

    init_db()

    last_nudge: Optional[Tuple[int, str]] = None

    logging.info("Starting nudge processing loop with %s second interval.", interval)

    while True:
        try:
            nudge = get_next_nudge()
        except Exception as exc:  # Catch-all to avoid loop crash
            logging.exception("Unexpected error fetching nudge: %s", exc)
            init_db()
            nudge = None

        if nudge and nudge != last_nudge:
            _, message = nudge
            push_notification("kor’tana nudge", message)
            log_event("nudge", message)
            last_nudge = nudge
        elif nudge:
            logging.debug("Duplicate nudge detected. Skipping notification.")

        time.sleep(interval)


if __name__ == "__main__":
    run_loop()
