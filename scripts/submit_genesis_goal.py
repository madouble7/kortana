#!/usr/bin/env python3
"""
Genesis Protocol Goal Submission
================================
Submit the refactoring goal to Kor'tana via API
"""

from datetime import datetime

import requests

# Genesis Protocol Goal
GENESIS_GOAL = {
    "title": "Genesis Protocol: Refactor Goal Router Service Layer",
    "description": "Create a service layer for goal_router.py by extracting business logic into goal_service.py, following clean architecture patterns. This is Kor'tana's first autonomous software engineering task.",
    "priority": "critical",
    "status": "pending",
    "assigned_to": "autonomous_agent",
    "metadata": {
        "batch": "9",
        "protocol": "genesis",
        "phase": "3_proving_ground",
        "target_file": "src/kortana/api/routers/goal_router.py",
        "create_file": "src/kortana/api/services/goal_service.py",
        "timestamp": datetime.utcnow().isoformat(),
    },
}


def submit_genesis_goal():
    """Submit the Genesis Protocol goal to Kor'tana."""

    print("🎯 SUBMITTING GENESIS PROTOCOL GOAL")
    print("=" * 50)
    try:
        # Submit the goal
        response = requests.post(
            "http://localhost:8000/goals", json=GENESIS_GOAL, timeout=10
        )

        if response.status_code == 200 or response.status_code == 201:
            goal_data = response.json()
            print("✅ GOAL SUBMITTED SUCCESSFULLY!")
            print(f"   Goal ID: {goal_data.get('id', 'N/A')}")
            print(f"   Status: {goal_data.get('status', 'N/A')}")
            print(f"   Assigned to: {goal_data.get('assigned_to', 'N/A')}")

            print("\n🔬 THE PROVING GROUND IS NOW ACTIVE")
            print("   Kor'tana should begin autonomous processing...")
            print("   Monitor files for changes!")

            return True

        else:
            print(f"❌ Error submitting goal: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Kor'tana server")
        print("   Make sure the server is running on localhost:8000")
        print("   Run: python src/kortana/main.py")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def check_server_status():
    """Check if the Kor'tana server is running"""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Kor'tana server is running and healthy")
            return True
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Kor'tana server on port 8000")
        return False
    except Exception as e:
        print(f"❌ Error checking server status: {e}")
        return False


if __name__ == "__main__":
    print("🧬 GENESIS PROTOCOL ACTIVATION")
    print("=" * 50)
    print("Testing Kor'tana's first autonomous software engineering task")
    print()

    # Check server status first
    if check_server_status():
        print()
        success = submit_genesis_goal()

        if success:
            print()
            print("🎉 GENESIS PROTOCOL INITIATED!")
            print("Monitor the server logs to watch Kor'tana work autonomously.")
            print("Check goal status at: http://127.0.0.1:8000/goals/")
        else:
            print()
            print("❌ GENESIS PROTOCOL FAILED TO INITIATE")
    else:
        print()
        print("Please start the Kor'tana server first:")
        print("python -m uvicorn src.kortana.main:app --host 127.0.0.1 --port 8000")
