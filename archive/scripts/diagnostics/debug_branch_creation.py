#!/usr/bin/env python3
"""Debug script to check branch creation issue for #11000"""

import sqlite3
from pathlib import Path

db_path = Path("backend/github_tasks.db")
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute(
    """SELECT id, branch_name, plan, status, error_message
       FROM github_tasks WHERE id = '11000' LIMIT 1"""
)
row = cursor.fetchone()

if row:
    r = dict(row)
    print("Issue #11000 Details:")
    print(f"  ID: {r['id']}")
    print(f"  Status: {r['status']}")
    print(f"  Branch name: {r['branch_name']}")
    print(f"  Plan (first 300 chars): {r['plan'][:300] if r['plan'] else 'NULL'}")
    print(f"  Error: {r['error_message']}")
else:
    print("Issue #11000 not found")

conn.close()
