#!/usr/bin/env python3
"""
Start FastAPI server for testing
"""
import subprocess
import sys
import time
import requests
import os

def start_server_and_test():
    """Start server and test endpoints."""
    print("=== Starting FastAPI Server ===")

    # Change to project directory
    os.chdir("c:\\project-kortana")

    # Start server in background
    process = subprocess.Popen([
        "C:\\project-kortana\\venv311\\Scripts\\python.exe",
        "-m", "uvicorn",
        "src.kortana.main:app",
        "--host", "127.0.0.1",
        "--port", "8002",
        "--log-level", "warning"
    ])

    print("Server starting... waiting 3 seconds")
    time.sleep(3)

    # Test endpoints
    base_url = "http://127.0.0.1:8002"
    success = True

    try:
        # Test health endpoint
        print("\\nTesting /health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ /health endpoint: SUCCESS")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ /health endpoint: FAILED - Status {response.status_code}")
            success = False

        # Test database endpoint
        print("\\nTesting /test-db endpoint...")
        response = requests.get(f"{base_url}/test-db", timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result.get("db_connection") == "ok":
                print("✅ /test-db endpoint: SUCCESS")
                print(f"   Response: {result}")
            else:
                print(f"❌ /test-db endpoint: FAILED - {result}")
                success = False
        else:
            print(f"❌ /test-db endpoint: FAILED - Status {response.status_code}")
            success = False

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
        success = False
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        success = False
    finally:
        # Stop server
        print("\\nStopping server...")
        process.terminate()
        process.wait()

    return success

if __name__ == "__main__":
    success = start_server_and_test()
    print("\\n=== FastAPI Test Complete ===")
    if success:
        print("🎉 All FastAPI endpoints working correctly!")
    else:
        print("❌ Some FastAPI tests failed.")
