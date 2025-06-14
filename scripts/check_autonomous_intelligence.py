#!/usr/bin/env python3
"""
Quick Autonomous Intelligence Check
Rapid verification of current autonomous activity
"""

import json
import os
from datetime import datetime, timedelta

import requests


def quick_intelligence_check():
    print("🔍 QUICK AUTONOMOUS INTELLIGENCE CHECK")
    print("=" * 50)

    # Check 1: Server Status
    print("1. 🖥️  Checking server status...")
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is ONLINE and responding")
            server_online = True
        else:
            print(f"   ❌ Server returned status {response.status_code}")
            server_online = False
    except requests.RequestException as e:
        print(f"   ❌ Server is OFFLINE or not responding: {e}")
        print("   💡 Start with: python launch_secure_server.py")
        server_online = False

    if not server_online:
        return False

    # Check 2: Active Goals
    print("\n2. 🎯 Checking for active goals...")
    try:
        response = requests.get("http://127.0.0.1:8000/goals")
        if response.status_code == 200:
            goals = response.json()
            active_goals = [g for g in goals if g.get("status", "").lower() == "active"]

            if goals:
                print(f"   📋 Total goals: {len(goals)}")
                print(f"   🔄 Active goals: {len(active_goals)}")

                for goal in active_goals:
                    print(
                        f"   ⚡ Goal {goal.get('id')}: {goal.get('description', 'No description')[:50]}..."
                    )
            else:
                print("   📝 No goals found")
                print("   💡 Create one with: python assign_genesis_goal.py")
        else:
            print(f"   ❌ Could not fetch goals (status {response.status_code})")
    except Exception as e:
        print(f"   ❌ Error checking goals: {e}")

    # Check 3: Recent Learning
    print("\n3. 🧠 Checking for recent learning activity...")
    try:
        response = requests.get("http://127.0.0.1:8000/memories")
        if response.status_code == 200:
            memories = response.json()

            # Look for recent memories (last 24 hours)
            recent_memories = []
            core_beliefs = []

            for memory in memories:
                created_at = memory.get("created_at", "")
                memory_type = memory.get("memory_type", "")

                if "CORE_BELIEF" in memory_type.upper():
                    core_beliefs.append(memory)

                # Check if recent (simplified check)
                if created_at and "2025-06-13" in created_at:  # Today's date
                    recent_memories.append(memory)

            print(f"   📚 Total memories: {len(memories)}")
            print(f"   🆕 Recent memories: {len(recent_memories)}")
            print(f"   💡 Core beliefs: {len(core_beliefs)}")

            if core_beliefs:
                latest_belief = core_beliefs[-1]
                print(
                    f"   🌟 Latest belief: {latest_belief.get('title', 'Untitled')[:40]}..."
                )
                print("   ✅ AUTONOMOUS LEARNING CONFIRMED!")
            else:
                print("   📝 No core beliefs formed yet")

        else:
            print(f"   ❌ Could not fetch memories (status {response.status_code})")
    except Exception as e:
        print(f"   ❌ Error checking memories: {e}")

    # Check 4: File System Activity
    print("\n4. 📁 Checking for recent file modifications...")
    key_files = [
        "src/kortana/core/brain.py",
        "src/kortana/core/planning_engine.py",
        "src/kortana/core/enhanced_model_router.py",
        "data/autonomous_activity.log",
        "data/autonomous_status.json",
    ]

    recent_changes = 0
    for file_path in key_files:
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            modified_time = datetime.fromtimestamp(stat.st_mtime)

            # Check if modified in last hour
            if modified_time > datetime.now() - timedelta(hours=1):
                recent_changes += 1
                print(f"   📝 Recently modified: {file_path}")

    if recent_changes > 0:
        print(f"   ✅ {recent_changes} files modified recently")
        print("   🔥 AUTONOMOUS ACTIVITY DETECTED!")
    else:
        print("   😴 No recent file modifications")

    # Check 5: Status File
    print("\n5. 🤖 Checking autonomous status...")
    status_file = "data/autonomous_status.json"
    if os.path.exists(status_file):
        try:
            with open(status_file) as f:
                status = json.load(f)

            current_status = status.get("status", "unknown")
            current_goal = status.get("current_goal_id")
            last_cycle = status.get("last_cycle_timestamp", "unknown")

            print(f"   📊 Status: {current_status.upper()}")
            print(f"   🎯 Current goal: {current_goal or 'None'}")
            print(f"   ⏰ Last cycle: {last_cycle}")

            if current_status.lower() == "active":
                print("   ✅ AUTONOMOUS SYSTEM IS ACTIVE!")
            else:
                print("   😴 Autonomous system is idle")

        except Exception as e:
            print(f"   ❌ Error reading status: {e}")
    else:
        print("   📝 No status file found")

    # Overall Assessment
    print("\n" + "=" * 50)
    print("🏆 AUTONOMOUS INTELLIGENCE ASSESSMENT")
    print("=" * 50)

    if server_online:
        print("✅ Infrastructure: Server operational")
        print("💡 Ready for autonomous goal assignment")
        print("\nNext steps:")
        print("1. python assign_genesis_goal.py    # Assign a task")
        print("2. python monitor_autonomous_intelligence.py    # Watch her work")
        print("3. Wait 5-10 minutes and observe the four channels")
        return True
    else:
        print("❌ Infrastructure: Server not running")
        print("🔧 Fix: python launch_secure_server.py")
        return False


if __name__ == "__main__":
    quick_intelligence_check()
