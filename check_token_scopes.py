#!/usr/bin/env python
"""Check GitHub token scopes and permissions."""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def check_token() -> None:
    from src.kortana.http_client import get_http_client
    
    token = os.getenv("GITHUB_TOKEN")
    owner = os.getenv("GITHUB_OWNER", "madouble7")
    repo = os.getenv("GITHUB_REPO", "kortana")
    
    if not token:
        print("✗ GITHUB_TOKEN not found in environment")
        return
    
    print(f"Testing token against: {owner}/{repo}")
    token_display = f"{token[:20]}...{token[-10:]}" if len(token) > 30 else token[:10] + "..."
    print(f"Token format: {token_display}")
    print()
    
    client = get_http_client()
    
    # Check current user
    try:
        response = await client.get(
            "https://api.github.com/user",
            api_name="github",
            headers={"Authorization": f"token {token}"},
            timeout=10,
        )
        user_data = response.json()
        print(f"✓ Authenticated as: {user_data.get('login')}")
        print(f"  Type: {user_data.get('type')}")
        print()
    except Exception as e:
        print(f"✗ Failed to authenticate: {e}")
        return
    
    # Check if token has repo access (read)
    try:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            api_name="github",
            headers={"Authorization": f"token {token}"},
            timeout=10,
        )
        repo_data = response.json()
        print(f"✓ Can read repository: {repo_data.get('full_name')}")
        print(f"  Permission level: {repo_data.get('permissions')}")
        print()
    except Exception as e:
        print(f"✗ Cannot read repository: {e}")
        return
    
    # Check if token has push access (write)
    try:
        # Try to list branches (read-only, just to confirm read access)
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/branches",
            api_name="github",
            headers={"Authorization": f"token {token}"},
            timeout=10,
        )
        branches = response.json()
        print(f"✓ Can list branches: {len(branches)} found")
        main_branch = next((b for b in branches if b['name'] == 'main'), None)
        if main_branch:
            print(f"  Main branch SHA: {main_branch['commit']['sha'][:8]}...")
        print()
    except Exception as e:
        print(f"✗ Cannot list branches: {e}")
        return
    
    # Check write permissions by trying to access collaborators
    try:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/collaborators",
            api_name="github",
            headers={"Authorization": f"token {token}"},
            timeout=10,
        )
        _ = response.json()
        print("✓ Can list collaborators (write permission indicator)")
        print()
    except Exception as e:
        print(f"⚠ Limited to read-only access: {str(e)[:100]}")
        return
    
    print("=" * 60)
    print("✅ TOKEN APPEARS TO HAVE PROPER PERMISSIONS")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "backend")
    asyncio.run(check_token())
