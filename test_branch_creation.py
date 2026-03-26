#!/usr/bin/env python
"""Test actual branch creation with updated token."""
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, "backend")


async def test_branch_creation() -> None:
    import httpx
    
    token = os.getenv("GITHUB_TOKEN")
    owner = os.getenv("GITHUB_OWNER", "madouble7")
    repo = os.getenv("GITHUB_REPO", "kortana")
    
    print(f"Testing branch creation on: {owner}/{repo}")
    print()
    
    # Step 1: Get main branch SHA
    print("Step 1: Getting main branch SHA...")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/main",
            headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
            timeout=10,
        )
        
        if response.status_code != 200:
            print(f"✗ Failed to get main SHA: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return
        
        main_sha = response.json()["object"]["sha"]
        print(f"✓ Got main branch SHA: {main_sha[:8]}...")
        print()
        
        # Step 2: Try to create a test branch
        print("Step 2: Creating test branch...")
        branch_name = f"test-branch-{os.urandom(4).hex()}"
        create_response = await client.post(
            f"https://api.github.com/repos/{owner}/{repo}/git/refs",
            headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
            json={"ref": f"refs/heads/{branch_name}", "sha": main_sha},
            timeout=10,
        )
        
        if create_response.status_code == 201:
            print(f"✅ Successfully created branch: {branch_name}")
            print()
            
            # Step 3: Delete test branch to clean up
            print("Step 3: Cleaning up test branch...")
            delete_response = await client.delete(
                f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch_name}",
                headers={"Authorization": f"token {token}"},
                timeout=10,
            )
            
            if delete_response.status_code == 204:
                print(f"✓ Deleted test branch: {branch_name}")
                print()
                print("=" * 60)
                print("✅ TOKEN HAS FULL WRITE PERMISSIONS")
                print("=" * 60)
            else:
                print(f"⚠ Could not delete branch: {delete_response.status_code}")
        elif create_response.status_code == 422:
            print(f"⚠ Branch already exists (422): {create_response.json().get('message')}")
            print("  This is expected if run multiple times")
        else:
            print(f"✗ Failed to create branch: {create_response.status_code}")
            print(f"  Response: {create_response.text}")


if __name__ == "__main__":
    asyncio.run(test_branch_creation())
