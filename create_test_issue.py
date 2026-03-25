#!/usr/bin/env python3
"""Create a test [AUTO] GitHub issue for daemon discovery verification."""

import os
from datetime import datetime

import requests


def main() -> bool:
    # Read GitHub token from .env directly
    env_path = ".env"
    github_token = None
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    github_token = line.split("=", 1)[1]
                    break
    
    if not github_token:
        print("ERROR: GITHUB_TOKEN not found in .env")
        return False

    print("✅ GitHub token found. Creating test [AUTO] issue...\n")

    # Create issue via GitHub API
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    issue_data = {
        "title": "[AUTO] Daemon Test Discovery - Autonomous Task Processing Verification",
        "body": "This is a test issue created to verify that the autonomous daemon on 8004 can discover and process GitHub issues in real-time.\n\nTest timestamp: "
        + datetime.now().isoformat(),
        "labels": ["autonomy-test", "test"],
    }

    response = requests.post(
        "https://api.github.com/repos/KOR-TANA/kortana/issues",
        headers=headers,
        json=issue_data,
    )

    if response.status_code == 201:
        issue = response.json()
        print("✅ ISSUE CREATED")
        print(f"   Issue #:    {issue['number']}")
        print(f"   Title:      {issue['title']}")
        print(f"   URL:        {issue['html_url']}")
        print(f"   Created At: {issue['created_at']}")
        print("\n⏳ Daemon on 8004 will discover this in next cycle (~30 seconds)")
        return True
    else:
        print(f"❌ Failed to create issue: {response.status_code}")
        print(response.text)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
