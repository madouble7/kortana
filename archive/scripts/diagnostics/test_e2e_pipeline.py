#!/usr/bin/env python3
"""
End-to-end test: Create a fresh issue and let the daemon execute full pipeline.
This tests: code generation -> commit (isolated to branch) -> push -> PR creation.
"""
import json
import os

from sqlalchemy import create_engine, text

# Get database URL
db_url = os.getenv(
    "DATABASE_URL", "postgresql://postgres:supersecretpassword@localhost:5432/kortana"
)
db_url = db_url.replace("+asyncpg", "")

# Create issue that will trigger full pipeline
issue_number = 11000
plan = {
    "action": "create-e2e-test-files",
    "description": "E2E test: Create sample files to verify isolated branch commit/push/PR pipeline",
    "FILE_CHANGES": [
        {
            "path": "e2e_test_file_1.py",
            "action": "create",
            "content": "#!/usr/bin/env python3\n# E2E Test File 1\nprint('E2E pipeline test - File 1')\n",
        },
        {
            "path": "e2e_test_file_2.py",
            "action": "create",
            "content": "#!/usr/bin/env python3\n# E2E Test File 2\nprint('E2E pipeline test - File 2')\n",
        },
    ],
}

# Insert directly into database
engine = create_engine(db_url)
with engine.connect() as conn:
    # Check if issue already exists
    check_sql = text("SELECT COUNT(*) FROM github_tasks WHERE github_issue_number = :issue_number")
    count = conn.execute(check_sql, {"issue_number": issue_number}).scalar()

    if count == 0:
        # Insert new issue using ORM for proper escaping
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        # Create GitHubTask object
        import uuid

        from backend.src.kortana.models import GitHubTask

        task = GitHubTask(
            id=str(uuid.uuid4()),
            github_issue_number=issue_number,
            github_repo="KOR-TANA/kortana",
            title="E2E Test: Code generation and isolated branch pipeline",
            description="Test full pipeline: generate code files, commit to task branch, push to remote, create PR",
            status="planning_complete",
            branch_name=f"autonomy/e2e-test-{issue_number}",
            plan=json.dumps(plan),
            classification="auto",
            priority="high",
        )

        session.add(task)
        session.commit()
        session.close()
        print(f"✓ Created test issue #{issue_number} with code generation plan")
        print(f"  Branch: autonomy/e2e-test-{issue_number}")
        print("  Status: planning_complete (daemon will execute next cycle)")
        print()
        print("Daemon will:")
        print("  1. Generate code_changes from FILE_CHANGES")
        print("  2. _commit_branch_changes() - checkout branch, add files, commit")
        print("  3. _push_branch() - verify on correct branch, push to remote")
        print("  4. _create_pull_request_for_branch() - create PR")
        print()
        print("Expected in database after daemon runs:")
        print(f"  - Issue #{issue_number}: status='pr_created'")
        print("  - code_changes: populated with FILE_CHANGES")
        print("  - commit_sha: SHA of the commit")
        print("  - github_pr_number: Number of created PR")
        print()
        print(
            f"Check status: SELECT status, code_changes, commit_sha, github_pr_number FROM github_tasks WHERE github_issue_number = {issue_number};"
        )
    else:
        print(f"Issue #{issue_number} already exists in database")
