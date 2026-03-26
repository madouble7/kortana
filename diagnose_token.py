#!/usr/bin/env python
"""Diagnose GitHub token permissions."""
import asyncio
import json
import sys

sys.path.insert(0, "backend")


async def diagnose() -> None:
    from sqlalchemy import select
    from src.kortana.database import get_db_manager
    from src.kortana.models import GitHubTask
    from src.kortana.services.github_autonomy_service import GitHubAutonomyService

    manager = get_db_manager()
    async for db in manager.get_session():
        stmt = select(GitHubTask).where(GitHubTask.github_issue_number == 11000)
        result = await db.execute(stmt)
        task = result.scalar()

        if task:
            service = GitHubAutonomyService(db)

            # Step 1: Get main branch SHA
            url = "https://api.github.com/repos/KOR-TANA/kortana/git/ref/heads/main"
            response = await service.http_client.get(
                url,
                api_name="github_api",
                headers={
                    "Authorization": f"token {service.github_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=10,
            )
            main_sha = response.json()["object"]["sha"]
            print(f"✓ Got main SHA: {main_sha[:8]}...")

            # Step 2: Try to create a test branch
            create_url = "https://api.github.com/repos/KOR-TANA/kortana/git/refs"
            branch_data = {"ref": "refs/heads/test-branch-perms", "sha": main_sha}

            create_response = await service.http_client.post(
                create_url,
                api_name="github_api",
                headers={
                    "Authorization": f"token {service.github_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                json=branch_data,
                timeout=10,
            )

            print(f"Create branch status: {create_response.status_code}")

            try:
                error_detail = create_response.json()
                print("Error message:", error_detail.get("message", ""))
                print("Full response:")
                print(json.dumps(error_detail, indent=2))
            except Exception:
                print("Response:", create_response.text[:300])
        break


asyncio.run(diagnose())
