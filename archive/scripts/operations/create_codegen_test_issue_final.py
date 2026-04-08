#!/usr/bin/env python3
"""Create and inject a test issue that will generate code"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.src.kortana.models import GitHubTask

db_url = os.getenv(
    "DATABASE_URL", "postgresql://postgres:supersecretpassword@localhost:5432/kortana"
)
db_url = db_url.replace("+asyncpg", "")

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

try:
    # Create a task with a valid code generation plan
    task = GitHubTask(
        github_issue_number=10000,
        title="Test: Code generation and commit pipeline",
        description="This issue tests the full pipeline",
        status="planning_complete",
        branch_name="autonomy/test-10000",
        github_repo="KOR-TANA/kortana",
        priority="high",
        classification="auto",
        # Valid plan that will trigger code generation
        plan='{"action": "create-files", "description": "Create test files", "FILE_CHANGES": [{"path": "test_pipeline_execution.py", "content": "# Auto-generated\\nprint(\'success\')", "action": "create"}]}',
    )

    db.add(task)
    db.commit()

    print("Created test issue #10000 with code generation plan")
    print("Daemon should pick this up next cycle and:")
    print("  1. Generate the code file")
    print("  2. Call _commit_branch_changes() to commit it")
    print("  3. Call _push_branch() to push it")
    print("  4. Call _create_pull_request_for_branch() to create PR")

finally:
    db.close()
