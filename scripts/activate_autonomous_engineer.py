#!/usr/bin/env python3
"""
🚀 THE PROVING GROUND - AUTONOMOUS ENGINEER ACTIVATION
====================================================

This script assigns Kor'tana her first real software engineering task
and begins monitoring her autonomous development process.
"""

import time
from datetime import datetime

import requests

BASE_URL = "http://127.0.0.1:8000"

def check_server():
    """Verify server is online"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Error connecting to server: {e}")
        return False

def assign_autonomous_engineering_goal():
    """Assign the first autonomous software engineering goal"""

    goal_data = {
        "description": "Refactor the list_all_goals function in src/kortana/api/routers/goal_router.py. Create a new service layer function in a new file, src/kortana/api/services/goal_service.py, to handle the database query. The router must then be updated to call this new service function. After the refactor, run the full project test suite to ensure no regressions were introduced.",
        "priority": 1
    }

    print("🎯 ASSIGNING AUTONOMOUS SOFTWARE ENGINEERING GOAL")
    print("=" * 60)
    print(f"📋 Goal: {goal_data['description']}")
    print(f"⚡ Priority: {goal_data['priority']}")
    print()

    try:
        response = requests.post(f"{BASE_URL}/goals/", json=goal_data, timeout=10)

        if response.status_code == 201:
            goal = response.json()
            print("✅ Goal assigned successfully!")
            print(f"🆔 Goal ID: {goal['id']}")
            print(f"📊 Status: {goal['status']}")
            print(f"⏰ Created: {goal['created_at']}")
            print()
            print("🤖 Kor'tana should now begin autonomous planning and execution...")
            print("📺 Watch the server logs for autonomous activity!")
            return goal['id']
        else:
            print(f"❌ Failed to assign goal: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error assigning goal: {e}")
        return None

def monitor_goal_progress(goal_id):
    """Monitor the progress of the assigned goal"""
    print("\n🔍 MONITORING AUTONOMOUS PROGRESS")
    print("=" * 60)
    print("This will check goal status every 30 seconds...")
    print("Press Ctrl+C to stop monitoring")
    print()

    try:
        while True:
            try:
                response = requests.get(f"{BASE_URL}/goals/{goal_id}", timeout=5)
                if response.status_code == 200:
                    goal = response.json()
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] Goal {goal_id}: {goal['status']}")

                    if goal['status'] in ['COMPLETED', 'FAILED']:
                        print(f"\n🎉 Goal {goal_id} finished with status: {goal['status']}")
                        break
                else:
                    print(f"⚠️ Could not fetch goal status: {response.status_code}")

            except Exception as e:
                print(f"❌ Error checking goal: {e}")

            time.sleep(30)

    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")

if __name__ == "__main__":
    print("🚀 THE PROVING GROUND - AUTONOMOUS ENGINEER ACTIVATION")
    print("🤖 Initiating Kor'tana's First Software Engineering Assignment")
    print("=" * 70)
    print()

    # Check server
    if not check_server():
        print("❌ Server not available. Please start with:")
        print("   python -m uvicorn src.kortana.main:app --host 127.0.0.1 --port 8000")
        exit(1)

    print("✅ Server is online")

    # Assign the goal
    goal_id = assign_autonomous_engineering_goal()

    if goal_id:
        # Start monitoring
        monitor_goal_progress(goal_id)
    else:
        print("❌ Could not assign goal. Check server logs for details.")
