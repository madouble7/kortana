#!/usr/bin/env python3
"""Check E2E test issue status after daemon execution."""
import json
import os

from sqlalchemy import create_engine, text

db_url = os.getenv(
    "DATABASE_URL", "postgresql://postgres:supersecretpassword@localhost:5432/kortana"
)
db_url = db_url.replace("+asyncpg", "")

engine = create_engine(db_url)
with engine.connect() as conn:
    sql = text(
        "SELECT status, code_changes, commit_sha, github_pr_number FROM github_tasks WHERE github_issue_number = 11000"
    )
    result = conn.execute(sql).fetchone()

    if result:
        status, code_changes, commit_sha, pr_number = result
        print("Issue #11000 Status:", status)
        print("Code changes generated:", "YES" if code_changes else "NO")
        print("Commit SHA:", commit_sha if commit_sha else "NOT SET")
        print("PR Number:", pr_number if pr_number else "NOT SET")

        if code_changes:
            print()
            print("Code changes contents:")
            if isinstance(code_changes, str):
                cc = json.loads(code_changes)
            else:
                cc = code_changes
            for file_info in cc:
                path = file_info.get("path", "?")
                print(f"  - {path}")
    else:
        print("Issue #11000 not found")
