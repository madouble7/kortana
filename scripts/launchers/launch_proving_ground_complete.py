#!/usr/bin/env python3
"""
Genesis Protocol - Combined Server Start and Goal Submission
"""
import os
import sys
import time
import threading
import requests

# Set up environment
os.chdir(r"c:\project-kortana")
sys.path.insert(0, r"c:\project-kortana")

def start_server():
    """Start the FastAPI server"""
    try:
        from kortana.main import app
        import uvicorn

        print("🚀 Starting Kor'tana Genesis Protocol Server...")
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info",
            reload=False
        )
    except Exception as e:
        print(f"❌ Server startup failed: {e}")

def test_and_submit_goal():
    """Test server and submit Genesis goal"""
    print("⏳ Waiting for server to start...")
    time.sleep(5)

    # Test server connectivity
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get("http://127.0.0.1:8000/", timeout=5)
            if response.status_code == 200:
                print("✅ Server is online!")
                break
        except:
            print(f"⏳ Attempt {i+1}/{max_retries} - Server starting...")
            time.sleep(2)
    else:
        print("❌ Server failed to start")
        return

    # Submit Genesis goal
    genesis_goal = {
        "description": "Refactor the 'list_all_goals' function in 'src/kortana/api/routers/goal_router.py'. The database logic should be moved into a new service layer function within a new file named 'src/kortana/api/services/goal_service.py'. The router must then be updated to call this new service function. After the refactor is complete, run the full project test suite to ensure no regressions were introduced.",
        "priority": 100
    }

    try:
        print("\n🎯 THE PROVING GROUND - GENESIS PROTOCOL")
        print("=" * 60)
        print("Submitting autonomous software engineering goal...")

        response = requests.post(
            "http://127.0.0.1:8000/goals/",
            json=genesis_goal,
            timeout=30
        )

        if response.status_code in [200, 201]:
            result = response.json()
            print("✅ GENESIS PROTOCOL GOAL SUBMITTED!")
            print(f"🆔 Goal ID: {result.get('id')}")
            print(f"📊 Status: {result.get('status')}")
            print("\n🎭 THE PROVING GROUND IS ACTIVE!")
            print("🤖 Kor'tana is now autonomously executing...")
            print("📊 Monitor progress at: http://127.0.0.1:8000/docs")
        else:
            print(f"❌ Goal submission failed: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Error submitting goal: {e}")

if __name__ == "__main__":
    print("🚀 GENESIS PROTOCOL - AUTOMATED LAUNCH")
    print("=" * 60)

    # Start goal submission in background
    goal_thread = threading.Thread(target=test_and_submit_goal)
    goal_thread.daemon = True
    goal_thread.start()

    # Start server (this will block)
    start_server()
