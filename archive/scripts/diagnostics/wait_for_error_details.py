#!/usr/bin/env python3
"""Poll issue #11000 until daemon captures the detailed error response"""

import os
import time
from urllib.parse import urlparse

import psycopg2

db_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:supersecretpassword@localhost:5432/kortana",
)
db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

parsed = urlparse(db_url)

print("=" * 75)
print("Waiting for daemon to process #11000 and capture GitHub API error...")
print("=" * 75)
print("Polling every 30 seconds for 15 minutes...\n")

start_time = time.time()
timeout = 900  # 15 minutes

while time.time() - start_time < timeout:
    try:
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
            SELECT status, error_message, error_count, executed_at, updated_at
            FROM github_tasks WHERE branch_name LIKE '%11000%'
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            status, error_msg, error_count, executed_at, updated_at = row
            elapsed = int(time.time() - start_time)

            # Show any change
            print(f"[{elapsed // 60}m {elapsed % 60}s] Status: {status}")
            if status == "executing":
                print("  ⏳ Daemon is processing...")
            elif status == "failed":
                print(f"  ❌ Failed (attempt {error_count})")
                if error_msg:
                    print(f"\n  ERROR MESSAGE:\n  {error_msg}\n")
                if error_msg and "Status" in error_msg:
                    # Found the detailed error we logged
                    print("  ✓ Detailed error captured")
                    print("\n" + "=" * 75)
                    print("ACTUAL GITHUB API ERROR:")
                    print("=" * 75)
                    print(error_msg)
                    break
            elif status == "pr_created":
                print("  ✓ SUCCESS - PR created")
                break

        time.sleep(30)

    except Exception as e:
        print(f"Error checking database: {e}")
        time.sleep(30)

print("\n" + "=" * 75)
print("To see full daemon logs, check the FastAPI stdout on port 9001")
print("=" * 75)
