#!/usr/bin/env python3
"""
Test server connectivity and submit goal
"""

import sys

# Add project to path
sys.path.insert(0, r"c:\project-kortana")

try:
    import requests

    # Test server connectivity
    print("Testing server connectivity...")
    response = requests.get("http://127.0.0.1:8000/")
    print(f"Server response: {response.status_code}")

    # Test goals endpoint
    print("Testing goals endpoint...")
    goals_response = requests.get("http://127.0.0.1:8000/goals/")
    print(f"Goals endpoint response: {goals_response.status_code}")

    # Submit the goal
    goal_data = {
        "description": "Refactor the 'list_all_goals' function in 'src/kortana/api/routers/goal_router.py'. The database logic should be moved into a new service layer function within a new file named 'src/kortana/api/services/goal_service.py'. The router must then be updated to call this new service function. After the refactor is complete, run the full project test suite to ensure no regressions were introduced.",
        "priority": 100,
    }

    print("Submitting Genesis Protocol goal...")
    submit_response = requests.post(
        "http://127.0.0.1:8000/goals/submit", json=goal_data
    )

    print(f"Submit response status: {submit_response.status_code}")
    print(f"Submit response body: {submit_response.text}")

    if submit_response.status_code in [200, 201]:
        print("✅ GENESIS PROTOCOL GOAL SUBMITTED SUCCESSFULLY!")
        print("🎯 Phase 3: The Proving Ground is now ACTIVE")
        print("Kor'tana is beginning autonomous execution...")
    else:
        print("❌ Goal submission failed")

except ImportError:
    print("❌ requests module not available")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
