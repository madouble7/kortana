#!/usr/bin/env python3
"""
Quick FastAPI server test
"""
import subprocess
import time
import requests
import os
import signal

def quick_server_test():
    """Quick test of FastAPI server."""
    print("=== Quick FastAPI Server Test ===")

    os.chdir("c:\\project-kortana")

    # Start server
    print("Starting server on port 8003...")
    process = subprocess.Popen([
        "C:\\project-kortana\\venv311\\Scripts\\python.exe",
        "-m", "uvicorn",
        "src.kortana.main:app",
        "--host", "127.0.0.1",
        "--port", "8003"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for server to start
    time.sleep(4)

    success_count = 0
    total_tests = 2

    try:
        # Test health endpoint
        print("Testing /health...")
        response = requests.get("http://127.0.0.1:8003/health", timeout=3)
        if response.status_code == 200:
            print("✅ Health endpoint works!")
            print(f"   {response.json()}")
            success_count += 1
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")

        # Test database endpoint
        print("Testing /test-db...")
        response = requests.get("http://127.0.0.1:8003/test-db", timeout=3)
        if response.status_code == 200:
            result = response.json()
            if result.get("db_connection") == "ok":
                print("✅ Database endpoint works!")
                print(f"   {result}")
                success_count += 1
            else:
                print(f"❌ Database test failed: {result}")
        else:
            print(f"❌ Database endpoint failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
    finally:
        # Stop server
        print("Stopping server...")
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()

    print(f"\\nResults: {success_count}/{total_tests} tests passed")
    return success_count == total_tests

if __name__ == "__main__":
    result = quick_server_test()
    print("\\n=== Test Complete ===")
    if result:
        print("🎉 All FastAPI tests passed!")
    else:
        print("❌ Some tests failed.")
