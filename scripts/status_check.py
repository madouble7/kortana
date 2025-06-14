#!/usr/bin/env python3
"""
Simple Status Check for Kor'tana
"""

import requests


def check_status():
    print("🔍 KOR'TANA STATUS CHECK")
    print("=" * 30)

    try:
        # Check server
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        print(f"Server: {'✅ Online' if response.status_code == 200 else '❌ Offline'}")

        # Check goals
        response = requests.get("http://127.0.0.1:8000/goals", timeout=5)
        if response.status_code == 200:
            goals = response.json()
            print(f"Goals: {len(goals)} total")

            for goal in goals:
                status = goal.get("status", "unknown")
                desc = goal.get("description", "No description")[:50]
                print(f"  Goal {goal.get('id')}: {status.upper()} - {desc}...")
        else:
            print(f"Goals: Error {response.status_code}")

        # Check memories
        response = requests.get("http://127.0.0.1:8000/memories", timeout=5)
        if response.status_code == 200:
            memories = response.json()
            print(f"Memories: {len(memories)} total")

            core_beliefs = [
                m for m in memories if "CORE_BELIEF" in m.get("memory_type", "").upper()
            ]
            print(f"Core Beliefs: {len(core_beliefs)} formed")
        else:
            print(f"Memories: Error {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    check_status()
