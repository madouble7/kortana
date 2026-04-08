#!/usr/bin/env python3
"""Test the backend/.env GITHUB_TOKEN"""

from pathlib import Path

import requests

OK = "[OK]"
ERR = "[ERR]"

# Read backend/.env
env_file = Path(__file__).parent / "backend" / ".env"
github_token = None

if env_file.exists():
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            if line.startswith("GITHUB_TOKEN="):
                github_token = line.split("=", 1)[1].strip()
                break

if github_token:
    print(
        f"Backend .env token detected: prefix={github_token[:4]} length={len(github_token)}"
    )

    headers = {"Authorization": f"token {github_token}"}
    response = requests.get("https://api.github.com/user", headers=headers, timeout=5)

    if response.status_code == 200:
        user = response.json()
        print(f"{OK} Token is valid - authenticated as: {user['login']}")
    elif response.status_code == 401:
        print(f"{ERR} Token is invalid or expired (401 Unauthorized)")
        print(f"   Response: {response.text[:200]}")
    else:
        print(f"{ERR} API error (status {response.status_code}): {response.text[:200]}")
else:
    print("No GITHUB_TOKEN found in backend/.env")
