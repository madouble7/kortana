#!/usr/bin/env python
"""Reset issue #11000 to queued state for re-processing with fixed code."""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))


async def reset_task():
    from sqlalchemy import select

    from src.kortana.database import get_db_manager
    from src.kortana.models import GitHubTask

    manager = get_db_manager()

    # Use async context manager generator
    async for db in manager.get_session():
        # Fetch the task
        stmt = select(GitHubTask).where(GitHubTask.github_issue_number == 11000)
        result = await db.execute(stmt)
        task = result.scalar()

        if task:
            print(f"Found Issue #{task.github_issue_number}: {task.title}")
            print(f"  Current Status: {task.status}")
            print(f"  Current Error: {task.error_message}")
            print(f"  Error Count: {task.error_count}")

            # Reset for re-processing
            task.status = "queued"
            task.error_message = None
            task.error_count = 0
            task.code_changes = None
            task.commit_sha = None
            task.github_pr_number = None

            print(f"\n  Reset to Status: {task.status}")
            print("  Task ready for re-processing")
        else:
            print("Issue #11000 not found in database")


if __name__ == "__main__":
    asyncio.run(reset_task())
