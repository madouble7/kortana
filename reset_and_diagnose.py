#!/usr/bin/env python3
"""Reset issue #11000 to planning_complete with diagnostic logging enabled"""

import os
import time
from urllib.parse import urlparse

import psycopg2
import requests

# Reset the task in database
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
cursor.execute(
    """
    UPDATE github_tasks
    SET status = 'planning_complete',
        error_message = NULL,
        error_count = 0
    WHERE branch_name LIKE '%11000%'
    RETURNING id
    """
)
result = cursor.fetchone()
conn.commit()
conn.close()

if result:
    print(f"✓ Reset issue #11000 (task {result[0][:8]}...)")
else:
    print("No task found")
    exit(1)

# Restart daemon
print("\nRestarting daemon with enhanced logging...")
response = requests.post("http://127.0.0.1:9001/api/daemon/stop", timeout=5)
if response.status_code != 200:
    print(f"Warning: Problem stopping daemon: {response.status_code}")

time.sleep(1)

response = requests.post("http://127.0.0.1:9001/api/daemon/start", timeout=5)
if response.status_code == 200:
    print("✓ Daemon restarted")
else:
    print(f"Warning: Problem starting daemon: {response.status_code}")

print("\n" + "=" * 70)
print("NEXT: Check logs to see what GitHub API actually returns")
print("=" * 70)
print("On daemon restart, it will:")
print("  1. Pick up #11000 (planning_complete)")
print("  2. Try to create branch autonomy/e2e-test-11000")
print("  3. Log the ACTUAL GitHub API response")
print("     - Status code")
print("     - API error message")
print("     - Full response body")
print("\nRun this to see captured error:")
print("  python check_11000_uuid.py")
