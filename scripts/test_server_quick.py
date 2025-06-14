#!/usr/bin/env python
"""
Quick server test script
"""

import subprocess
import time

import requests


def test_server():
    print("🧪 Testing Kor'tana FastAPI Server...")

    # Start server
    print("Starting server...")
    process = subprocess.Popen([
        "python", "-m", "uvicorn", "src.kortana.main:app",
        "--host", "127.0.0.1", "--port", "8000"
    ], capture_output=True, text=True)

    # Wait for startup
    time.sleep(3)

    try:
        # Test endpoints
        print("Testing /health endpoint...")
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint: SUCCESS")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint: FAILED - Status {response.status_code}")

        print("\nTesting /test-db endpoint...")
        response = requests.get("http://127.0.0.1:8000/test-db", timeout=5)
        if response.status_code == 200:
            print("✅ Database endpoint: SUCCESS")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Database endpoint: FAILED - Status {response.status_code}")

    except Exception as e:
        print(f"❌ Error during testing: {e}")

    finally:
        # Stop server
        print("\nStopping server...")
        process.terminate()

    print("\n✅ Server test complete!")
    return True

if __name__ == "__main__":
    test_server()
