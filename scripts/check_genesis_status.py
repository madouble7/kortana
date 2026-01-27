#!/usr/bin/env python3
"""
PROVING GROUND: GOAL STATUS CHECKER
Check if Kor'tana has processed the Genesis Protocol goal
"""

import sys

sys.path.append(".")


def check_goal_status():
    try:
        from kortana.core.goal_manager import GoalManager
        from kortana.modules.memory_core.services import MemoryCoreService
        from kortana.services.database import SessionLocal

        db = SessionLocal()
        try:
            memory_manager = MemoryCoreService(db)
            goal_manager = GoalManager(memory_manager=memory_manager)

            print("🔍 GENESIS PROTOCOL GOAL STATUS CHECK")
            print("=" * 50)

            # Get all goals
            all_goals = goal_manager.prioritize_goals()
            print(f"📊 Total goals in system: {len(all_goals)}")

            # Look for Genesis goals
            genesis_goals = []
            for goal in all_goals:
                desc_lower = goal.description.lower()
                if any(
                    keyword in desc_lower
                    for keyword in [
                        "genesis",
                        "refactor",
                        "goal_router",
                        "list_all_goals",
                    ]
                ):
                    genesis_goals.append(goal)

            if genesis_goals:
                print(f"\n🔥 GENESIS PROTOCOL GOALS FOUND: {len(genesis_goals)}")
                for i, goal in enumerate(genesis_goals):
                    print(f"\n--- Genesis Goal {i + 1} ---")
                    print(f"ID: {goal.id}")
                    print(f"Status: {goal.status}")
                    print(f"Priority: {goal.priority}")
                    print(f"Created: {goal.created_at}")
                    print(f"Description: {goal.description[:200]}...")

                    if hasattr(goal, "updated_at") and goal.updated_at:
                        print(f"Updated: {goal.updated_at}")

                    # Show the highest priority Genesis goal status
                    if i == 0:
                        print(f"\n🎯 PRIMARY GENESIS GOAL STATUS: {goal.status}")
                        if goal.status == "COMPLETED":
                            print("✅ GOAL COMPLETED! Ready for code review.")
                        elif goal.status == "IN_PROGRESS":
                            print("🔄 GOAL IN PROGRESS! Autonomous engineering active.")
                        elif goal.status == "PENDING":
                            print("⏳ GOAL PENDING: Awaiting autonomous processing.")
                        elif goal.status == "FAILED":
                            print("❌ GOAL FAILED: Check logs for errors.")
            else:
                print("\n❌ NO GENESIS PROTOCOL GOALS FOUND")
                print("💡 May need to run: python activate_genesis_protocol.py")

            # Check recent activity
            active_goals = goal_manager.list_active_goals()
            print(f"\n📈 CURRENTLY ACTIVE GOALS: {len(active_goals)}")
            for goal in active_goals[:3]:  # Show first 3
                print(f"   • {goal.id}: {goal.description[:60]}...")

        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error checking goal status: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    check_goal_status()
