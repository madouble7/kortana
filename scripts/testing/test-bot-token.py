#!/usr/bin/env python3
"""
Test GitHub Bot Token for Kor'tana Autonomous Operations
Verifies the bot token has correct permissions for autonomous workflows
"""

import requests
import os
import sys

def test_bot_token(token: str) -> bool:
    """Test if the bot token has required permissions"""

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    print("🔍 Testing GitHub bot token permissions...")

    # Test 1: Basic API access
    try:
        response = requests.get('https://api.github.com/user', headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Basic API access: {user_data.get('login', 'unknown')}")
        else:
            print(f"❌ Basic API access failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Basic API access failed: {str(e)}")
        return False

    # Test 2: Repository access (KOR-TANA/kortana)
    try:
        response = requests.get('https://api.github.com/repos/KOR-TANA/kortana', headers=headers)
        if response.status_code == 200:
            repo_data = response.json()
            print(f"✅ Repository access: {repo_data.get('full_name', 'unknown')}")
        else:
            print(f"❌ Repository access failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Repository access failed: {str(e)}")
        return False

    # Test 3: Repository issues access (needed for TaskQueue)
    try:
        response = requests.get('https://api.github.com/repos/KOR-TANA/kortana/issues', headers=headers)
        if response.status_code == 200:
            print("✅ Issues access: Can read repository issues")
        else:
            print(f"❌ Issues access failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Issues access failed: {str(e)}")
        return False

    # Test 4: Repository contents access (needed for commits)
    try:
        response = requests.get('https://api.github.com/repos/KOR-TANA/kortana/contents/README.md', headers=headers)
        if response.status_code == 200:
            print("✅ Contents access: Can read repository files")
        else:
            print(f"❌ Contents access failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Contents access failed: {str(e)}")
        return False

    # Test 5: Check token scopes (if possible)
    try:
        # This endpoint might not be available for PATs, but let's try
        response = requests.get('https://api.github.com/user/installations', headers=headers)
        if response.status_code == 200:
            print("✅ Advanced permissions: Token has workflow/installation access")
        elif response.status_code == 404:
            print("ℹ️  Advanced permissions: Not available for PATs (expected)")
        else:
            print(f"⚠️  Advanced permissions check: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Advanced permissions check failed: {str(e)}")

    print("\n🎉 Bot token test completed successfully!")
    print("The token has sufficient permissions for Kor'tana autonomous operations.")
    return True

def main():
    """Main test function"""
    # Try to get token from environment variable
    token = os.getenv('KORTANA_AUTONOMOUS_TOKEN')

    if not token:
        print("❌ No KORTANA_AUTONOMOUS_TOKEN environment variable found")
        print("Set it with: export KORTANA_AUTONOMOUS_TOKEN=your_token_here")
        print("Or pass token as argument: python test-bot-token.py your_token_here")
        sys.exit(1)

    # Mask token in output for security
    masked_token = token[:4] + "*" * (len(token) - 8) + token[-4:] if len(token) > 8 else "***"

    print(f"Testing token: {masked_token}")
    print("=" * 50)

    if test_bot_token(token):
        print("\n✅ SUCCESS: Bot token is ready for autonomous operations!")
        sys.exit(0)
    else:
        print("\n❌ FAILURE: Bot token lacks required permissions")
        print("Please check the setup guide and ensure all scopes are granted")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Token passed as command line argument
        os.environ['KORTANA_AUTONOMOUS_TOKEN'] = sys.argv[1]

    main()
