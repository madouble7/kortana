#!/usr/bin/env python3
"""
Genesis Protocol Goal Assignment
Submit the autonomous refactoring goal to Kor'tana
"""

import requests


def assign_genesis_goal():
    """Assign the Genesis Protocol refactoring goal to Kor'tana"""

    # The Genesis Protocol goal - simplified for API compatibility
    goal_data = {
        "description": "Genesis Protocol: Refactor the model routing system to use enhanced_model_router.py with cost optimization and centralized configuration. This is Kor'tana's first autonomous software engineering task.",
        "priority": 1,  # High priority as integer (1 = highest)
    }  # Server endpoint
    url = "http://127.0.0.1:8001/goals"

    print("🎯 GENESIS PROTOCOL - GOAL ASSIGNMENT")
    print("=" * 50)
    print()
    print("📋 Goal Details:")
    print(f"Description: {goal_data['description'][:80]}...")
    print(f"Priority: {goal_data['priority']} (1 = highest)")
    print()

    try:
        print("📡 Submitting goal to Kor'tana...")
        response = requests.post(
            url,
            json=goal_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS: Goal submitted successfully!")
            print(f"📝 Goal ID: {result.get('id', 'Unknown')}")
            print(f"📊 Status: {result.get('status', 'Unknown')}")
            print()
            print(
                "🤖 Kor'tana has received her first autonomous software engineering goal!"
            )
            print("🔍 Monitor logs and file system for autonomous activity...")
            return True
        else:
            print(f"❌ Failed to submit goal. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to Kor'tana server")
        print("Please ensure the server is running at http://127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def check_server_status():
    """Check if Kor'tana server is online"""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"❌ Server connection error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Genesis Protocol Goal Assignment System")
    print()

    # Check server status
    if check_server_status():
        print("✅ Kor'tana server is online")
        assign_genesis_goal()
    else:
        print("❌ Kor'tana server is not responding")
        print("Please start the server first using:")
        print("  python -m uvicorn src.kortana.main:app --host 127.0.0.1 --port 8000")
