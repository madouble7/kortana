#!/usr/bin/env python3
"""
GENESIS PROTOCOL PHASE 3: THE PROVING GROUND
Real-time monitoring of Kor'tana's autonomous software engineering performance
"""

import sys
from datetime import datetime

sys.path.append(".")


def check_genesis_goal_status():
    """Check the status of Genesis Protocol goals"""
    try:
        from src.kortana.core.goal_manager import GoalManager
        from src.kortana.modules.memory_core.services import MemoryCoreService
        from src.kortana.services.database import SessionLocal

        db = SessionLocal()
        try:
            memory_manager = MemoryCoreService(db)
            goal_manager = GoalManager(memory_manager=memory_manager)

            print(f"🔬 PROVING GROUND MONITOR - {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 60)

            # Check all goals
            all_goals = goal_manager.prioritize_goals()
            active_goals = goal_manager.list_active_goals()

            print("📊 GOAL SUMMARY:")
            print(f"   Total Goals: {len(all_goals)}")
            print(f"   Active Goals: {len(active_goals)}")

            # Look for Genesis Protocol goals
            genesis_keywords = ["genesis", "refactor", "goal_router", "list_all_goals"]
            genesis_goals = []

            for goal in all_goals:
                for keyword in genesis_keywords:
                    if keyword.lower() in goal.description.lower():
                        genesis_goals.append(goal)
                        break

            print(f"\n🔥 GENESIS PROTOCOL GOALS: {len(genesis_goals)}")

            if genesis_goals:
                for i, goal in enumerate(genesis_goals):
                    print(f"\n   Goal {goal.id} (Genesis #{i + 1}):")
                    print(f"   📝 Description: {goal.description[:100]}...")
                    print(f"   🎯 Status: {goal.status}")
                    print(f"   📈 Priority: {goal.priority}")
                    print(f"   📅 Created: {goal.created_at}")
                    if hasattr(goal, "updated_at") and goal.updated_at:
                        print(f"   🔄 Updated: {goal.updated_at}")

                    # Check if it's in progress or completed
                    if goal.status in ["IN_PROGRESS", "COMPLETED"]:
                        print("   🚀 GENESIS PROTOCOL ACTIVE!")
                        return goal
            else:
                print("   ❌ No Genesis Protocol goals found")
                print("   💡 The goal may need to be created/activated")

            return None

        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error checking goals: {e}")
        return None


def monitor_autonomous_activity():
    """Monitor logs and system activity"""
    print("\n🔍 AUTONOMOUS ACTIVITY MONITOR:")

    # Check for recent log files
    import os

    log_files = [
        "genesis_run.log",
        "genesis_run_shell.log",
        "logs/kortana.log",
        "kortana.log",
    ]

    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"   📄 Found log: {log_file}")
            # Show last few lines
            try:
                with open(log_file, encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        print(f"      Last entry: {lines[-1].strip()}")
            except Exception as e:
                print(f"      Error reading log file {log_file}: {e}")
                pass
        else:
            print(f"   ❌ No log: {log_file}")


def main():
    """Main monitoring loop"""
    print("🚀 GENESIS PROTOCOL PHASE 3: THE PROVING GROUND")
    print("🔬 MONITORING KOR'TANA'S AUTONOMOUS SOFTWARE ENGINEERING")
    print("=" * 70)

    # Check current goal status
    genesis_goal = check_genesis_goal_status()

    # Monitor activity
    monitor_autonomous_activity()

    if genesis_goal:
        print(f"\n✅ GENESIS PROTOCOL GOAL DETECTED: {genesis_goal.status}")
        if genesis_goal.status == "IN_PROGRESS":
            print("🔥 AUTONOMOUS ENGINEERING IN PROGRESS!")
            print("📊 Continue monitoring for completion...")
        elif genesis_goal.status == "COMPLETED":
            print("🎯 GOAL COMPLETED! Ready for code review phase.")
        elif genesis_goal.status == "PENDING":
            print("⏳ Goal pending - autonomous brain may need to be active.")
    else:
        print("\n💡 RECOMMENDATION: Activate Genesis Protocol goal")
        print("   Run: python activate_genesis_protocol.py")

    print("\n" + "=" * 70)
    print("🔬 Monitoring snapshot complete. Run again to check progress.")


if __name__ == "__main__":
    main()
