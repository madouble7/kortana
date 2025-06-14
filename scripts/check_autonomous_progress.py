#!/usr/bin/env python3
"""
Quick script to check autonomous progress
"""


import requests


def check_goal_status():
    try:
        response = requests.get("http://127.0.0.1:8000/goals/5", timeout=5)
        if response.status_code == 200:
            goal = response.json()
            print("✅ GOAL STATUS CHECK")
            print("=" * 40)
            print(f"ID: {goal['id']}")
            print(f"Status: {goal['status']}")
            print(f"Description: {goal['description'][:100]}...")
            print(f"Priority: {goal['priority']}")
            print(f"Created: {goal['created_at']}")
            print(f"Completed: {goal.get('completed_at', 'Not yet')}")
            print()
            return goal
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def check_recent_memories():
    try:
        response = requests.get("http://127.0.0.1:8000/memories/", timeout=5)
        if response.status_code == 200:
            memories = response.json()
            print("🧠 RECENT MEMORY ACTIVITY")
            print("=" * 40)
            if memories:
                for memory in memories[-5:]:  # Last 5 memories
                    print(f"- {memory.get('content', 'No content')[:80]}...")
            else:
                print("No memories found")
            print()
            return memories
        else:
            print(f"❌ Memory check error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Memory exception: {e}")
        return None

if __name__ == "__main__":
    print("🔍 AUTONOMOUS PROGRESS CHECK")
    print("=" * 50)
    print()

    goal = check_goal_status()
    memories = check_recent_memories()

    if goal:
        if goal['status'] == 'PENDING':
            print("🤖 Kor'tana should be processing this goal...")
            print("💡 Check server logs for autonomous activity!")
        elif goal['status'] == 'IN_PROGRESS':
            print("🚀 Kor'tana is actively working on this goal!")
        elif goal['status'] == 'COMPLETED':
            print("🎉 Goal completed! Check the implementation.")
        elif goal['status'] == 'FAILED':
            print("❌ Goal failed. Check logs for details.")
