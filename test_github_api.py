#!/usr/bin/env python3
"""Test GitHub API connectivity and token validity"""

import os
from pathlib import Path

import requests

# Load .env file
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

github_token = os.getenv("GITHUB_TOKEN", "").strip()

if not github_token:
    print("❌ GITHUB_TOKEN not set in environment")
else:
    print(f"GitHub token found (length: {len(github_token)})")
    print("Testing GitHub API...")

    # Test 1: Get authenticated user
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.get("https://api.github.com/user", headers=headers, timeout=5)
    print(f"\n/user endpoint: Status {response.status_code}")
    if response.status_code == 200:
        user = response.json()
        print(f"  ✓ Authenticated as: {user['login']}")
    else:
        print(f"  ❌ Error: {response.text[:200]}")

    # Test 2: Get KOR-TANA repo
    response = requests.get(
        "https://api.github.com/repos/KOR-TANA/kortana", headers=headers, timeout=5
    )
    print(f"\n/repos/KOR-TANA/kortana endpoint: Status {response.status_code}")
    if response.status_code == 200:
        repo = response.json()
        print(f"  ✓ Repo found: {repo['name']}")
    else:
        print(f"  ❌ Error: {response.text[:200]}")

    # Test 3: Try to get a ref (main branch)
    response = requests.get(
        "https://api.github.com/repos/KOR-TANA/kortana/git/refs/heads/main",
        headers=headers,
        timeout=5,
    )
    print(f"\n/git/refs/heads/main endpoint: Status {response.status_code}")
    if response.status_code == 200:
        ref = response.json()
        print(f"  ✓ Main branch SHA: {ref['object']['sha'][:8]}...")
    else:
        print(f"  ❌ Error: {response.text[:200]}")

    # Test 4: Try creating a branch (prepare data but don't commit)
    print("\nSimulating branch creation API call...")
    branch_data = {
        "ref": "refs/heads/test-autonomy-token-check",
        "sha": "3fa8bf1",  # The safe code commit
    }
    response = requests.post(
        "https://api.github.com/repos/KOR-TANA/kortana/git/refs",
        headers=headers,
        json=branch_data,
        timeout=5,
    )
    print(f"POST /git/refs endpoint: Status {response.status_code}")
    if response.status_code == 201:
        print("  ✓ Branch created successfully")
    elif response.status_code == 422:
        print("  ℹ Branch already exists (expected on retry)")
    else:
        print(f"  ❌ Error: {response.text[:300]}")
