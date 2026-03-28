#!/usr/bin/env python3
"""Check task #11000 using environment and psycopg2"""

import os
from urllib.parse import urlparse

import psycopg2

# Parse DATABASE_URL from environment
db_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:supersecretpassword@localhost:5432/kortana",
)
# Convert to sync URL if needed
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
cursor.execute(
    "SELECT id, status, branch_name, error_message, plan FROM github_tasks WHERE id = '11000' LIMIT 1"
)
row = cursor.fetchone()

if row:
    print("=" * 65)
    print("Issue #11000 Debug Info")
    print("=" * 65)
    print(f"ID: {row[0]}")
    print(f"Status: {row[1]}")
    print(f"Branch name: {row[2]}")
    print(f"Error message: {row[3]}")
    if row[4]:
        print(f"Plan (first 300 chars):\n{row[4][:300]}")
    else:
        print("Plan: NULL")
else:
    print("Task #11000 not found")

conn.close()
