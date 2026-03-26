#!/usr/bin/env python
"""
Test that daemon configuration correctly points to personal fork
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv


def main():
    # Load .env
    load_dotenv()

    # Check environment
    owner = os.getenv("GITHUB_OWNER")
    repo = os.getenv("GITHUB_REPO")
    token = os.getenv("GITHUB_TOKEN")

    print("=" * 60)
    print("PERSONAL FORK CONFIGURATION CHECK")
    print("=" * 60)
    print(f"✓ GITHUB_OWNER: {owner}")
    print(f"✓ GITHUB_REPO: {repo}")
    print(f"✓ GITHUB_TOKEN present: {bool(token)}")
    print()

    # Verify it's the personal fork
    target_owner = "madouble7"
    target_repo = "kortana"

    if owner == target_owner:
        print(f"✅ Correct owner: {owner}")
    else:
        print(f"❌ Wrong owner: {owner} (expected {target_owner})")
        return False

    if repo == target_repo:
        print(f"✅ Correct repo: {repo}")
    else:
        print(f"❌ Wrong repo: {repo} (expected {target_repo})")
        return False

    if not token:
        print("⚠️  GITHUB_TOKEN not set (will cause runtime errors)")
        return False

    print("✅ GitHub token is set")
    print()
    print("=" * 60)
    print(f"Daemon will target: {owner}/{repo}")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
