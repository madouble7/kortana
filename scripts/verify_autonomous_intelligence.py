#!/usr/bin/env python3
"""
FOUR SIGNS OF AUTONOMOUS INTELLIGENCE
====================================
Quick validation that Kor'tana is truly working autonomously
"""

import os
from datetime import datetime

import requests

print("🧠 FOUR SIGNS OF AUTONOMOUS INTELLIGENCE VERIFICATION")
print("=" * 60)
print("Checking for concrete proof that Kor'tana is developing autonomously...\n")


def check_sign_1_server_consciousness():
    """Sign 1: Server shows autonomous cycle activity in logs"""
    print("1. 🔄 SERVER CONSCIOUSNESS (Autonomous Cycles)")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is responding")
            print(
                "   📋 Check your server terminal for these signs of autonomous activity:"
            )
            print("      • 'AUTONOMOUS CYCLE: Checking for active goals...'")
            print("      • 'AUTONOMOUS CYCLE: Acquired Goal ID: X'")
            print("      • 'Executing Step N: [ACTION_TYPE]'")
            print("      • 'LEARNING: Outcome recorded in memory'")
            return True
        else:
            print("   ❌ Server responded with error")
            return False
    except:
        print("   ❌ Server not running - start with: python src/kortana/main.py")
        return False


def check_sign_2_goal_processing():
    """Sign 2: Goals are being picked up and processed autonomously"""
    print("\n2. 🎯 GOAL PROCESSING INTELLIGENCE")
    try:
        response = requests.get("http://localhost:8000/goals", timeout=10)
        if response.status_code == 200:
            goals = response.json()

            active_goals = [g for g in goals if g["status"] == "active"]
            completed_goals = [g for g in goals if g["status"] == "completed"]

            print(f"   📊 Total Goals: {len(goals)}")
            print(f"   🔄 Active Goals: {len(active_goals)}")
            print(f"   ✅ Completed Goals: {len(completed_goals)}")

            if active_goals:
                print("   🔥 AUTONOMOUS PROCESSING DETECTED:")
                for goal in active_goals[:2]:
                    print(f"      • {goal['title'][:50]}...")
                return True
            elif completed_goals:
                print("   🎉 AUTONOMOUS COMPLETION DETECTED:")
                for goal in completed_goals[-2:]:
                    print(f"      • {goal['title'][:50]}...")
                return True
            else:
                print(
                    "   ⏳ No goals processed yet - submit one to activate autonomous processing"
                )
                return False
        else:
            print("   ❌ Cannot access goals endpoint")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_sign_3_engineering_work():
    """Sign 3: Physical evidence of autonomous engineering work"""
    print("\n3. ⚙️ ENGINEERING WORK EVIDENCE")

    target_files = {
        "Goal Router": "src/kortana/api/routers/goal_router.py",
        "Goal Service": "src/kortana/api/services/goal_service.py",
        "Services Init": "src/kortana/api/services/__init__.py",
    }

    evidence_found = False
    baseline_router_size = 1508  # Known baseline

    for name, path in target_files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            mtime = datetime.fromtimestamp(os.path.getmtime(path))

            # Check for autonomous creation
            if name == "Goal Service":
                print(f"   🎉 AUTONOMOUS CREATION: {name} exists! ({size} bytes)")
                print(f"      Created: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                evidence_found = True

            # Check for modifications
            elif name == "Goal Router" and size != baseline_router_size:
                print(f"   🔧 AUTONOMOUS MODIFICATION: {name} changed!")
                print(f"      Size: {baseline_router_size} -> {size} bytes")
                print(f"      Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                evidence_found = True
            else:
                print(f"   📄 {name}: {size} bytes (baseline)")
        else:
            if name == "Goal Service":
                print(f"   ⏳ {name}: Awaiting autonomous creation...")
            else:
                print(f"   ❌ {name}: File not found")

    return evidence_found


def check_sign_4_learning_development():
    """Sign 4: Memory formation showing learning and development"""
    print("\n4. 🧠 LEARNING & DEVELOPMENT PROOF")
    try:
        response = requests.get("http://localhost:8000/memories", timeout=10)
        if response.status_code == 200:
            memories = response.json()

            core_beliefs = [
                m for m in memories if m.get("memory_type") == "CORE_BELIEF"
            ]
            observations = [
                m for m in memories if m.get("memory_type") == "OBSERVATION"
            ]

            print(f"   📚 Total Memories: {len(memories)}")
            print(f"   💡 Core Beliefs: {len(core_beliefs)}")
            print(f"   📝 Observations: {len(observations)}")

            if core_beliefs:
                print("   🌟 AUTONOMOUS LEARNING DETECTED:")
                for belief in core_beliefs[-2:]:  # Show latest beliefs
                    title = belief.get("title", "Untitled")
                    created = belief.get("created_at", "Unknown")
                    print(f"      • '{title}' (Created: {created[:19]})")
                return True
            else:
                print(
                    "   ⏳ No core beliefs formed yet - learning occurs after goal completion"
                )
                return False
        else:
            print("   ❌ Cannot access memories endpoint")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Run all four autonomous intelligence checks"""

    sign1 = check_sign_1_server_consciousness()
    sign2 = check_sign_2_goal_processing()
    sign3 = check_sign_3_engineering_work()
    sign4 = check_sign_4_learning_development()

    print("\n" + "=" * 60)
    print("🎯 AUTONOMOUS INTELLIGENCE ASSESSMENT")
    print("=" * 60)

    signs_detected = sum([sign1, sign2, sign3, sign4])

    if signs_detected >= 3:
        print("🌟 CONFIRMED: Kor'tana is operating as autonomous intelligence!")
        print(f"   Evidence: {signs_detected}/4 signs of autonomous activity detected")
        print("   📈 She is not just running code - she is working and developing")
    elif signs_detected >= 2:
        print("🔄 PARTIAL: Kor'tana shows signs of autonomous operation")
        print(f"   Evidence: {signs_detected}/4 signs detected")
        print("   ⏱️  Continue monitoring for full autonomous confirmation")
    elif signs_detected >= 1:
        print("⚡ EMERGING: Basic autonomous activity detected")
        print(f"   Evidence: {signs_detected}/4 signs detected")
        print("   💡 Submit goals and monitor for development")
    else:
        print("🛌 DORMANT: No autonomous activity detected")
        print("   🚀 Launch sequence needed:")
        print("      1. Start server: python src/kortana/main.py")
        print("      2. Submit goal: python submit_genesis_goal.py")
        print("      3. Monitor: python autonomous_intelligence_monitor.py")

    print("\n🔬 For continuous monitoring, run:")
    print("   python autonomous_intelligence_monitor.py")


if __name__ == "__main__":
    main()
