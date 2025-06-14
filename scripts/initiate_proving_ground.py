#!/usr/bin/env python3
"""
GENESIS PROTOCOL - Direct Goal Submission for The Proving Ground
"""

import requests

# The Genesis Protocol Goal
genesis_goal = {
    "description": "Refactor the 'list_all_goals' function in 'src/kortana/api/routers/goal_router.py'. The database logic should be moved into a new service layer function within a new file named 'src/kortana/api/services/goal_service.py'. The router must then be updated to call this new service function. After the refactor is complete, run the full project test suite to ensure no regressions were introduced.",
    "priority": 100,
}


def initiate_proving_ground():
    """Submit the Genesis Protocol goal and initiate The Proving Ground"""

    print("🚀 THE PROVING GROUND - GENESIS PROTOCOL")
    print("=" * 60)
    print("🎯 AUTONOMOUS SOFTWARE ENGINEERING INITIATION")
    print("=" * 60)

    try:
        print("📡 Connecting to Kor'tana...")  # Submit the Genesis goal
        response = requests.post(
            "http://127.0.0.1:8000/goals/", json=genesis_goal, timeout=30
        )

        if response.status_code in [200, 201]:
            result = response.json()

            print("✅ GENESIS PROTOCOL GOAL SUBMITTED!")
            print(f"🆔 Goal ID: {result.get('id')}")
            print(f"📊 Status: {result.get('status')}")

            print("\n🎭 THE PROVING GROUND IS ACTIVE!")
            print("🤖 Kor'tana is now autonomously executing...")
            print("📊 Monitor progress at: http://127.0.0.1:8000/docs")
            return True

        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    initiate_proving_ground()
