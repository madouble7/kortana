#!/usr/bin/env python3
"""
Submit the official Genesis Protocol Proving Ground test goal
"""

import requests

# The goal data
goal_data = {
    "description": "Refactor the 'list_all_goals' function in 'src/kortana/api/routers/goal_router.py'. The database logic should be moved into a new service layer function within a new file named 'src/kortana/api/services/goal_service.py'. The router must then be updated to call this new service function. After the refactor is complete, run the full project test suite to ensure no regressions were introduced.",
    "priority": 100,
}


def submit_genesis_goal():
    """Submit the Genesis Protocol test goal"""
    try:
        print("🚀 GENESIS PROTOCOL - PHASE 3: THE PROVING GROUND")
        print("=" * 60)
        print("Submitting autonomous software engineering test goal...")
        print()
        print(f"Goal Description: {goal_data['description']}")
        print(f"Priority: {goal_data['priority']}")
        print()

        # Submit the goal
        response = requests.post(
            "http://127.0.0.1:8000/goals/submit",
            json=goal_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print("✅ Goal submitted successfully!")
            print(f"Goal ID: {result.get('id', 'Unknown')}")
            print(f"Status: {result.get('status', 'Unknown')}")
            print()
            print("🎯 AUTONOMOUS OPERATION INITIATED")
            print("Kor'tana will now:")
            print("1. Analyze the current code structure")
            print("2. Plan the refactoring approach")
            print("3. Create the new service layer")
            print("4. Refactor the router function")
            print("5. Run comprehensive tests")
            print("6. Validate the implementation")
            print()
            print("Monitor progress at: http://127.0.0.1:8000/docs")
            print("=" * 60)
            return True
        else:
            print(f"❌ Failed to submit goal. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Kor'tana server on port 8000")
        print("Please ensure the server is running:")
        print("python -m uvicorn src.kortana.main:app --host 127.0.0.1 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error submitting goal: {e}")
        return False


if __name__ == "__main__":
    submit_genesis_goal()
