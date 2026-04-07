#!/usr/bin/env python3
"""Monitor issue #11000 for daemon execution with safe code."""
import os

from sqlalchemy import create_engine, text

db_url = os.getenv(
    "DATABASE_URL", "postgresql://postgres:supersecretpassword@localhost:5432/kortana"
)
db_url = db_url.replace("+asyncpg", "")

engine = create_engine(db_url)
with engine.connect() as conn:
    sql = text(
        """
        SELECT
            status,
            code_changes,
            commit_sha,
            github_pr_number,
            error_message,
            updated_at,
            executed_at
        FROM github_tasks
        WHERE github_issue_number = 11000
    """
    )
    result = conn.execute(sql).fetchone()

    if result:
        (
            status,
            code_changes,
            commit_sha,
            pr_number,
            error,
            updated_at,
            executed_at,
        ) = result

        print("=" * 70)
        print("ISSUE #11000 DAEMON EXECUTION STATUS")
        print("=" * 70)
        print()
        print("Status:", status)
        print("Code changes populated:", "YES" if code_changes else "NO")
        print("Commit SHA:", commit_sha if commit_sha else "NOT SET")
        print("PR Number:", pr_number if pr_number else "NOT SET")
        print("Error:", error if error else "None")
        print()
        print("Execution Timeline:")
        print("  Updated at:", updated_at)
        print("  Executed at:", executed_at)
        print()

        if status == "planning_complete":
            print("⏳ WAITING FOR DAEMON")
            print("   Issue is ready for execution")
            print("   Daemon will process on next cycle (~600 seconds)")
        elif status == "executing":
            print("⚙️  DAEMON IS EXECUTING")
            print("   Safe pipeline running on main (3fa8bf1)")
        elif status == "pr_created":
            print("✅ PIPELINE COMPLETE")
            if code_changes and commit_sha and pr_number:
                print("   Full end-to-end verified!")
                print("   - Code generated and committed")
                print("   - Branch push successful")
                print("   - PR created successfully")
            else:
                print("   PR created but missing data fields")
        elif status == "failed":
            print("❌ EXECUTION FAILED")
            print("   Error:", error)
        else:
            print(f"⚠️  STATUS: {status}")

        print()
        print("=" * 70)
    else:
        print("Issue #11000 not found in database")
