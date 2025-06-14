#!/usr/bin/env python3
"""
Quick server health check and goal submission for The Proving Ground
"""

import requests

BASE_URL = "http://localhost:8000"


def check_server_health():
    """Check if server is running and healthy."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy!")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Start it with:")
        print(
            "   python -m uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000 --reload"
        )
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def submit_genesis_protocol_goal():
    """Submit the Genesis Protocol refactoring goal."""

    goal_data = {
        "description": """Genesis Protocol Refactoring - First Autonomous Engineering Task

MISSION: Refactor existing genesis protocol creation functionality to demonstrate autonomous software engineering capabilities.

TECHNICAL SCOPE:
1. Analyze existing files: create_genesis_clean.py, create_genesis_correct.py
2. Identify code duplication, architectural issues, and improvement opportunities
3. Design a cleaner, more modular architecture
4. Implement consolidated functionality with proper error handling
5. Add comprehensive logging and documentation
6. Ensure backward compatibility with existing functionality
7. Create unit tests for the refactored code
8. Document the architectural improvements and design decisions

SUCCESS CRITERIA:
- Single, well-structured genesis protocol module
- Clear separation of concerns and modular design
- Comprehensive error handling and logging
- Full test coverage of core functionality
- Professional documentation explaining the refactored architecture
- All existing functionality preserved and enhanced
- Code quality improvements verified through static analysis

This is Kor'tana's first autonomous software engineering challenge. Demonstrate independent analysis, strategic planning, implementation excellence, and thorough validation.""",
        "priority": 100,
    }

    try:
        print("🎯 Submitting Genesis Protocol goal...")
        response = requests.post(
            f"{BASE_URL}/goals",
            json=goal_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ GENESIS PROTOCOL GOAL SUBMITTED SUCCESSFULLY!")
            print(f"   Goal ID: {result.get('id', 'Unknown')}")
            print(f"   Status: {result.get('status', 'Unknown')}")
            print(f"   Created: {result.get('created_at', 'Unknown')}")
            return True
        else:
            print(f"❌ Goal submission failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Goal submission error: {e}")
        return False


def check_current_goals():
    """Check what goals are currently in the system."""
    try:
        response = requests.get(f"{BASE_URL}/goals", timeout=5)
        if response.status_code == 200:
            goals = response.json()
            print(f"📋 Current goals in system: {len(goals)}")
            for goal in goals:
                print(
                    f"   Goal {goal.get('id')}: {goal.get('status')} - {goal.get('description', '')[:60]}..."
                )
            return goals
        else:
            print(f"⚠️  Failed to retrieve goals: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error checking goals: {e}")
        return []


def main():
    """Main execution for Proving Ground launch."""

    print("🚀 THE PROVING GROUND - LAUNCH VERIFICATION")
    print("=" * 60)

    # Step 1: Check server health
    if not check_server_health():
        print("\n🛑 Server must be running before proceeding.")
        print("Start the server first, then run this script again.")
        return False

    # Step 2: Check existing goals
    existing_goals = check_current_goals()

    # Step 3: Submit Genesis Protocol goal if none exists
    genesis_goal_exists = any(
        "Genesis Protocol" in goal.get("description", "") for goal in existing_goals
    )

    if not genesis_goal_exists:
        if submit_genesis_protocol_goal():
            print("\n🎉 THE PROVING GROUND IS NOW ACTIVE!")
            print("=" * 60)
            print("✅ Kor'tana has received her first autonomous engineering challenge")
            print("✅ Monitor her progress through logs and file changes")
            print("✅ Check goal status at: http://localhost:8000/goals")

            print("\n📊 MONITORING LOCATIONS:")
            print("   - Autonomous logs: data/autonomous_logs/")
            print("   - System status: data/phase5_status.json")
            print("   - File changes: Watch for new/modified files")
            print("   - Goal API: http://localhost:8000/goals")

            return True
        else:
            print("\n❌ Failed to submit Genesis Protocol goal")
            return False
    else:
        print("\n📋 Genesis Protocol goal already exists!")
        print("The Proving Ground may already be active.")
        return True


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 THE PROVING GROUND IS OPERATIONAL!")
        print("Monitor Kor'tana's autonomous engineering work in real-time.")
    exit(0 if success else 1)
