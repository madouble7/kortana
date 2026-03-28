#!/usr/bin/env python3
"""Get detailed info on the #11000 e2e test task"""

import os
from urllib.parse import urlparse

import psycopg2

db_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:supersecretpassword@localhost:5432/kortana",
)
db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

parsed = urlparse(db_url)
conn = psycopg2.connect(
    user=parsed.username,
    password=parsed.password,
    host=parsed.hostname,
    port=parsed.port,
    database=parsed.path[1:] if parsed.path else "kortana",
)

cursor = conn.cursor()

# Find the #11000 task by branch name pattern
cursor.execute(
    "SELECT id, status, branch_name, error_message, error_count, executed_at, code_changes, commit_sha FROM github_tasks WHERE branch_name LIKE '%11000%' LIMIT 1"
)
row = cursor.fetchone()

if row:
    print("=" * 70)
    print("Issue #11000 E2E Test Task Details")
    print("=" * 70)
    print(f"Task ID (UUID): {row[0]}")
    print(f"Status: {row[1]}")
    print(f"Branch name: {row[2]}")
    print(f"Error message: {row[3]}")
    print(f"Error count: {row[4]}")
    print(f"Executed at: {row[5]}")
    print(f"Code changes: {'YES' if row[6] else 'NO'}")
    print(f"Commit SHA: {row[7] if row[7] else 'NOT SET'}")
    print("=" * 70)
    print("^^ Issue has failed 2x with 'Failed to create GitHub branch'")
    print("^^ Safe code IS on main (3fa8bf1), but branch creation is failing")
    print("^^ Likely: GitHub token auth issue or API rate limiting")
else:
    print("Task not found")

conn.close()
