#!/usr/bin/env python3
"""Reset issue #11000 for daemon retry with safe code on main."""
import os

from sqlalchemy import create_engine, text

db_url = os.getenv(
    "DATABASE_URL", "postgresql://postgres:supersecretpassword@localhost:5432/kortana"
)
db_url = db_url.replace("+asyncpg", "")

engine = create_engine(db_url)
with engine.connect() as conn:
    # Reset issue #11000 to planning_complete
    reset_sql = text(
        """
        UPDATE github_tasks
        SET status = 'planning_complete',
            error_message = NULL,
            error_count = 0,
            updated_at = NOW()
        WHERE github_issue_number = 11000
    """
    )
    conn.execute(reset_sql)
    conn.commit()

    # Verify reset
    check_sql = text(
        "SELECT status, error_message, error_count FROM github_tasks WHERE github_issue_number = 11000"
    )
    result = conn.execute(check_sql).fetchone()

    if result:
        print("✓ Reset issue #11000")
        print(f"  Status: {result[0]}")
        print(f"  Error message: {result[1] if result[1] else 'Cleared'}")
        print(f"  Error count: {result[2]}")
        print()
        print("Daemon will re-execute on next cycle (600s)")
        print("Expected: Safe branch creation, isolated commit, verified push, PR creation")
    else:
        print("Issue #11000 not found")
