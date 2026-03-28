#!/usr/bin/env python3
"""List all tasks in github_tasks table"""

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

# Get all tasks
cursor.execute(
    "SELECT id, status, branch_name, error_message FROM github_tasks ORDER BY id DESC LIMIT 10"
)
rows = cursor.fetchall()

print("Latest 10 tasks in database:")
print("=" * 70)
for row in rows:
    print(
        f"ID: {row[0]} ({type(row[0]).__name__}), Status: {row[1]}, Branch: {row[2]}, Error: {row[3][:50] if row[3] else 'None'}"
    )

conn.close()
