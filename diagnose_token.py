#!/usr/bin/env python
"""Diagnose GitHub token permissions for branch creation."""
import asyncio
import json
import sys
import time

import httpx

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
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=10,
            )
            main_sha = response.json()["object"]["sha"]
            print(f"OK Got main SHA: {main_sha[:8]}...")

            # Step 2: Try to create a short-lived probe branch
            create_url = "https://api.github.com/repos/KOR-TANA/kortana/git/refs"
            branch_name = f"token-permission-probe-{int(time.time())}"
            branch_data = {"ref": f"refs/heads/{branch_name}", "sha": main_sha}
            print(f"Probe ref: refs/heads/{branch_name}")

            try:
                create_response = await service.http_client.post(
                    create_url,
                    api_name="github_api",
                    headers={
                        "Authorization": f"token {service.github_token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                    json=branch_data,
                    timeout=10,
                )
                print(f"Create branch status: {create_response.status_code}")
                accepted_permissions = create_response.headers.get("X-Accepted-GitHub-Permissions")
                if accepted_permissions:
                    print(f"Accepted permissions: {accepted_permissions}")

                try:
                    error_detail = create_response.json()
                    print("Error message:", error_detail.get("message", ""))
                    print("Full response:")
                    print(json.dumps(error_detail, indent=2))
                except Exception:
                    print("Response:", create_response.text[:300])

                if create_response.status_code == 201:
                    delete_response = await service.http_client.delete(
                        f"{create_url}/heads/{branch_name}",
                        api_name="github_api",
                        headers={
                            "Authorization": f"token {service.github_token}",
                            "Accept": "application/vnd.github+json",
                            "X-GitHub-Api-Version": "2022-11-28",
                        },
                        timeout=10,
                    )
                    print(f"Cleanup delete status: {delete_response.status_code}")
            except httpx.HTTPStatusError as exc:
                response = exc.response
                print(f"Create branch status: {response.status_code}")
                accepted_permissions = response.headers.get("X-Accepted-GitHub-Permissions")
                if accepted_permissions:
                    print(f"Accepted permissions: {accepted_permissions}")
                try:
                    error_detail = response.json()
                    print("Error message:", error_detail.get("message", ""))
                    print("Full response:")
                    print(json.dumps(error_detail, indent=2))
                except Exception:
                    print("Response:", response.text[:300])
        break


asyncio.run(diagnose())
