"""Simple persistent memory for Kortana hub.

This is a conservative, local-only SQLite store for notes and events.
It is intentionally minimal and requires the user to opt-in for any external
data sources. No network access or external APIs are used by this module.
"""
import sqlite3
import datetime
from typing import Iterable


class MemoryStore:
    def __init__(self, path: str = "kortana_memory.db"):
        self.path = path
        self._conn = sqlite3.connect(self.path)
        self._init_db()

    def _init_db(self):
        c = self._conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created TIMESTAMP,
                source TEXT,
                text TEXT
            )
            """
        )
        self._conn.commit()

    def add_note(self, text: str, source: str = "local") -> int:
        c = self._conn.cursor()
        now = datetime.datetime.utcnow()
        c.execute("INSERT INTO notes (created, source, text) VALUES (?, ?, ?)", (now, source, text))
        self._conn.commit()
        return c.lastrowid

    def list_notes(self, limit: int = 50) -> Iterable[dict]:
        c = self._conn.cursor()
        c.execute("SELECT id, created, source, text FROM notes ORDER BY created DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        for r in rows:
            yield {"id": r[0], "created": r[1], "source": r[2], "text": r[3]}

    def search(self, q: str, limit: int = 50) -> Iterable[dict]:
        c = self._conn.cursor()
        pattern = f"%{q}%"
        c.execute("SELECT id, created, source, text FROM notes WHERE text LIKE ? ORDER BY created DESC LIMIT ?", (pattern, limit))
        rows = c.fetchall()
        for r in rows:
            yield {"id": r[0], "created": r[1], "source": r[2], "text": r[3]}

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass
