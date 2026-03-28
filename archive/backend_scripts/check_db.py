#!/usr/bin/env python
"""Check existing SQLite database tables."""

import sqlite3

conn = sqlite3.connect("kortana.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Existing tables:")
for (table,) in tables:
    print(f"  - {table}")
conn.close()
