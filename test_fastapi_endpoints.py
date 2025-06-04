#!/usr/bin/env python3
"""
Test script for FastAPI endpoints
"""
import requests
import time
import subprocess
import sys
import os
from threading import Thread

def start_server():
    """Start the FastAPI server in a subprocess."""
    try:
        # Change to project directory
        os.chdir("c:\\project-kortana")

        # Start the server
        subprocess.run([
            "C:\\project-kortana\\venv311\\Scripts\\python.exe",
            "-m", "uvicorn",
            "src.kortana.main:app",
            "--host", "127.0.0.1",
            "--port", "8000"
        ], timeout=30)
    except subprocess.TimeoutExpired:
        pass  # Server will keep running
    except Exception as e:
        print(f"Error starting server: {e}")

def test_endpoints():
    """Test the FastAPI endpoints."""
    base_url = "http://127.0.0.1:8000"

    # Wait a bit for server to start
    time.sleep(3)

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

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running.")
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")

if __name__ == "__main__":
    print("=== FastAPI Endpoint Test ===")

    # Start server in a separate thread
    server_thread = Thread(target=start_server, daemon=True)
    server_thread.start()

    # Test endpoints
    test_endpoints()

    print("\n=== Test Complete ===")
