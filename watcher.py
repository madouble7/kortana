"""Simple directory watcher for ingesting text files.

This script watches the ``incoming`` directory for new ``.txt`` files. When a
new file appears, it reads the contents, records a log entry in the SQLite
database, and prints a preview of the contents.
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict

DB_PATH = Path("kortana.db")
WATCH_DIR = Path("incoming")
POLL_INTERVAL_SECONDS = 1.0


def ensure_database(conn: sqlite3.Connection) -> None:
    """Create the activity_log table if it does not exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def get_processed_state(directory: Path) -> Dict[Path, float]:
    """Return a mapping of file paths to their modification times."""
    processed: Dict[Path, float] = {}
    for path in directory.glob("*.txt"):
        processed[path] = path.stat().st_mtime
    return processed


def log_file_ingest(conn: sqlite3.Connection, file_path: Path) -> None:
    """Insert a file_ingest log entry for the provided file."""
    conn.execute(
        """
        INSERT INTO activity_log (event_type, notes)
        VALUES (?, ?)
        """,
        ("file_ingest", file_path.name),
    )
    conn.commit()


def print_file_preview(file_path: Path) -> None:
    """Print the first 80 characters of the file."""
    contents = file_path.read_text(encoding="utf-8", errors="replace")
    preview = contents[:80]
    print(f"📄 {file_path.name}: {preview}")


def watch_directory() -> None:
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_database(conn)
        processed_files = get_processed_state(WATCH_DIR)
        print(f"👀 Watching directory: {WATCH_DIR.resolve()}")
        print("Press Ctrl+C to exit.")

        while True:
            try:
                for file_path in WATCH_DIR.glob("*.txt"):
                    mtime = file_path.stat().st_mtime
                    if file_path not in processed_files or processed_files[file_path] != mtime:
                        # Only treat the file as new if we have not seen it before.
                        if file_path not in processed_files:
                            log_file_ingest(conn, file_path)
                            print_file_preview(file_path)
                        processed_files[file_path] = mtime
                time.sleep(POLL_INTERVAL_SECONDS)
            except KeyboardInterrupt:
                raise
            except Exception as exc:  # pragma: no cover - runtime safety
                print(f"⚠️ Error while watching directory: {exc}", file=sys.stderr)
                time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n👋 Watcher stopped by user.")
    finally:
        conn.close()


if __name__ == "__main__":
    watch_directory()
