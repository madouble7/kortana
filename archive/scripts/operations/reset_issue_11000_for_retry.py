#!/usr/bin/env python3
"""Reset issue #11000 to planning_complete for retry with fixed HTTP client"""

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

# Find and reset the #11000 task
cursor.execute(
    """
    UPDATE github_tasks
    SET status = 'planning_complete',
        error_message = NULL,
        error_count = 0
    WHERE branch_name LIKE '%11000%'
    RETURNING id, status, error_count
    """
)
result = cursor.fetchone()

if result:
    print(f"✓ Reset task {result[0]}")
    print(f"  Status: {result[1]}")
    print(f"  Error count: {result[2]}")
    conn.commit()
    print("\nDaemon will re-execute on next cycle with FIXED HTTP client")
    print("Expected: 422 response will be treated as idempotent success")
else:
    print("No task found matching #11000")

conn.close()
