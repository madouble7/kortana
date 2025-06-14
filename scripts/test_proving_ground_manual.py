#!/usr/bin/env python3
"""
Simple test to check server status and submit Genesis Protocol goal
"""

import requests

BASE_URL = "http://localhost:8000"


def test_server_health():
    """Test if the server is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


def submit_genesis_goal():
    """Submit the Genesis Protocol goal."""
    goal_data = {
        "description": """Genesis Protocol Refactoring - Core Software Engineering Task

OBJECTIVE: Refactor the existing genesis protocol creation functionality to improve code quality, maintainability, and performance.

SCOPE:
1. Analyze existing genesis protocol files (create_genesis_clean.py, create_genesis_correct.py)
2. Identify code duplication, inefficiencies, and architectural issues
3. Design and implement a cleaner, more modular architecture
4. Consolidate redundant functionality into a single, well-structured module
5. Add proper error handling, logging, and documentation
6. Ensure backward compatibility with existing functionality
7. Write comprehensive tests for the refactored code

This is your first autonomous software engineering task. Demonstrate your ability to analyze, plan, design, implement, and validate a significant code refactoring independently.""",
        "priority": 100,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/goals",
            json=goal_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        print(f"Goal submission: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Goal ID: {result.get('id')}")
            print(f"Status: {result.get('status')}")
            return True
        else:
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"Goal submission failed: {e}")
        return False


def check_goals():
    """Check current goals."""
    try:
        response = requests.get(f"{BASE_URL}/goals", timeout=5)
        if response.status_code == 200:
            goals = response.json()
            print(f"Current goals: {len(goals)}")
            for goal in goals:
                print(
                    f"  Goal {goal.get('id')}: {goal.get('status')} - {goal.get('description', '')[:50]}..."
                )
            return goals
        else:
            print(f"Failed to get goals: {response.status_code}")
            return []
    except Exception as e:
        print(f"Goal check failed: {e}")
        return []


def main():
    print("🚀 THE PROVING GROUND - Manual Launch")
    print("=" * 50)

    # Test server
    if test_server_health():
        print("✅ Server is running")

        # Check existing goals
        existing_goals = check_goals()

        # Submit new goal if none exist
        if not existing_goals:
            print("📋 Submitting Genesis Protocol goal...")
            if submit_genesis_goal():
                print("✅ Goal submitted successfully!")
                print("🎯 THE PROVING GROUND IS ACTIVE")
                print("   Monitor logs: data/autonomous_logs/")
                print("   Check status: http://localhost:8000/goals")
            else:
                print("❌ Goal submission failed")
        else:
            print("📋 Goals already exist - Proving Ground may be active")

    else:
        print("❌ Server not running")
        print("Start server with: python -m uvicorn src.kortana.main:app --port 8000")


if __name__ == "__main__":
    main()
