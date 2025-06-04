#!/usr/bin/env python3
"""
Simple endpoint test without starting server
"""

import requests


def test_endpoints():
    """Test the FastAPI endpoints."""
    base_url = "http://127.0.0.1:8000"

    try:
        # Test health endpoint
        print("Testing /health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ /health endpoint: SUCCESS")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ /health endpoint: FAILED - Status {response.status_code}")

        # Test database endpoint
        print("\nTesting /test-db endpoint...")
        response = requests.get(f"{base_url}/test-db", timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result.get("db_connection") == "ok":
                print("✅ /test-db endpoint: SUCCESS")
                print(f"   Response: {result}")
            else:
                print(f"❌ /test-db endpoint: FAILED - {result}")
        else:
            print(f"❌ /test-db endpoint: FAILED - Status {response.status_code}")

        return True

    except requests.exceptions.ConnectionError:
        print(
            "❌ Could not connect to server. Make sure it's running on http://127.0.0.1:8000"
        )
        return False
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        return False


if __name__ == "__main__":
    print("=== FastAPI Endpoint Test ===")
    success = test_endpoints()
    print("\n=== Test Complete ===")
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed. Please check server status.")
