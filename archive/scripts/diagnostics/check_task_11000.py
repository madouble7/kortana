#!/usr/bin/env python3
"""Debug GitHub task 11000 using PostgreSQL"""

import os
import sys
from pathlib import Path

# Set up path
os.chdir(Path(__file__).parent / "backend")
sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))

# Now import after path is set
from kortana.database import SessionLocal  # noqa: E402
from kortana.models import GitHubTask  # noqa: E402

session = SessionLocal()
try:
    task = session.query(GitHubTask).filter_by(id="11000").first()
    if task:
        print("=" * 60)
        print("Issue #11000 Debug Info")
        print("=" * 60)
        print(f"ID: {task.id}")
        print(f"Status: {task.status}")
        print(f"Branch name: {task.branch_name}")
        print(f"Error message: {task.error_message}")
        print("Plan:")
        if task.plan:
            print(f"  {task.plan[:200]}")
        else:
            print("  NULL")
        print(f"Code changes: {task.code_changes[:100] if task.code_changes else 'NULL'}")
        print(f"Executed at: {task.executed_at}")
        print(f"Updated at: {task.updated_at}")
    else:
        print("Task #11000 not found in database")
finally:
    session.close()
