#!/usr/bin/env python3
"""
Directly test /goals and /memories API endpoints after Alembic setup.
Ensures a non-zero exit code on failure.
"""

import os
import sys  # Import sys for exit codes

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("KORTANA_API_URL", "http://127.0.0.1:8000")
HEALTH_ENDPOINT = "/health"  # Assuming a standard health check endpoint


def check_server_health():
    """Check if the server is reachable and healthy."""
    try:
        health_url = f"{BASE_URL}{HEALTH_ENDPOINT}"
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print(
                f"✅ Server Health ({health_url}): HEALTHY (Status {response.status_code})"
            )
            return True
        else:
            print(
                f"⚠️ Server Health ({health_url}): UNHEALTHY (Status {response.status_code}) - Response: {response.text[:200]}"
            )
            return False
    except requests.exceptions.ConnectionError:
        print(
            f"❌ Server Health ({BASE_URL}): NOT REACHABLE. Please ensure the server is running."
        )
        return False
    except Exception as e:
        print(f"❌ Server Health ({BASE_URL}): Error during health check: {e}")
        return False


def test_api_endpoints():
    """Test critical API endpoints and return True if all pass, False otherwise."""
    print(f"\n🔍 Testing API endpoints at {BASE_URL}...")

    endpoints_to_test = [
        ("Goals", "/goals/"),
        ("Memories", "/memories/"),
    ]

    all_passed = True

    for name, endpoint in endpoints_to_test:
        url = f"{BASE_URL}{endpoint}"  # Define url here for use in exception printing
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(
                    f"  ✅ {name} endpoint ({url}): PASSED (Status {response.status_code})"
                )
            else:
                print(
                    f"  ❌ {name} endpoint ({url}): FAILED (Status {response.status_code}) - Response: {response.text[:200]}"
                )
                all_passed = False
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {name} endpoint ({url}): FAILED (Error: {e})")
            all_passed = False

    if all_passed:
        print("\n🎉 All tested API endpoints are responding correctly!")
    else:
        print(
            "\n⚠️ Some API endpoints are still failing. Please check server logs and endpoint implementations."
        )
    return all_passed


if __name__ == "__main__":
    if not check_server_health():
        sys.exit(1)  # Exit with error code if server is not healthy

    if not test_api_endpoints():
        sys.exit(1)  # Exit with error code if any API test fails

    sys.exit(0)  # Exit with success code if all tests pass
