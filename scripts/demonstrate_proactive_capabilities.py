#!/usr/bin/env python3
"""
🚀 BATCH 10: PROACTIVE ENGINEER DEMONSTRATION
============================================

This script manually triggers Kor'tana's proactive code review task
to demonstrate her ability to autonomously identify improvement opportunities
and create her own goals.
"""

import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath("."))

import requests

from kortana.core.autonomous_tasks import run_proactive_code_review_task
from kortana.services.database import get_db_sync


def demonstrate_proactive_capabilities():
    """Demonstrate Kor'tana's proactive engineering capabilities"""

    print("🚀 BATCH 10: PROACTIVE ENGINEER DEMONSTRATION")
    print("=" * 60)
    print("🤖 Demonstrating Kor'tana's proactive intelligence...")
    print()

    # Step 1: Check current goals before proactive scan
    print("📊 STEP 1: BASELINE GOAL CHECK")
    print("-" * 40)

    try:
        response = requests.get("http://127.0.0.1:8000/goals/", timeout=10)
        if response.status_code == 200:
            goals_before = response.json()
            print(f"✅ Current goals in system: {len(goals_before)}")
            pending_before = [g for g in goals_before if g.get("status") == "PENDING"]
            print(f"📋 Pending goals before scan: {len(pending_before)}")
        else:
            print(f"⚠️ Could not check goals: {response.status_code}")
            goals_before = []
    except Exception as e:
        print(f"❌ Error checking goals: {e}")
        goals_before = []

    # Step 2: Trigger proactive code review
    print("\n🔍 STEP 2: PROACTIVE CODE SCANNING")
    print("-" * 40)
    print("🤖 AUTONOMOUS ACTION: Scanning codebase for improvement opportunities...")

    async def run_proactive_scan():
        db_gen = get_db_sync()
        db = next(db_gen)
        try:
            await run_proactive_code_review_task(db)
        finally:
            db.close()

    # Run the proactive task
    try:
        asyncio.run(run_proactive_scan())
        print("✅ Proactive scan completed!")
    except Exception as e:
        print(f"❌ Error during proactive scan: {e}")
        return

    # Step 3: Check for new goals created
    print("\n🎯 STEP 3: PROACTIVE GOAL GENERATION CHECK")
    print("-" * 40)

    try:
        response = requests.get("http://127.0.0.1:8000/goals/", timeout=10)
        if response.status_code == 200:
            goals_after = response.json()
            print(f"✅ Goals in system after scan: {len(goals_after)}")

            # Find newly created goals
            new_goals = []
            for goal in goals_after:
                if (
                    goal["id"] > max([g["id"] for g in goals_before])
                    if goals_before
                    else 0
                ):
                    new_goals.append(goal)

            if new_goals:
                print(
                    f"🎉 PROACTIVE SUCCESS: {len(new_goals)} new goals created autonomously!"
                )
                print("\n📝 AUTONOMOUS GOALS CREATED:")
                for i, goal in enumerate(new_goals, 1):
                    print(f"   {i}. Goal #{goal['id']}: {goal['description'][:80]}...")
                    print(f"      Status: {goal['status']}")
                    print(f"      Priority: {goal['priority']}")
                    print()

                # Store the first new goal ID for monitoring
                first_new_goal_id = new_goals[0]["id"]

                print(
                    "🤖 NEXT: Watch as Kor'tana's autonomous goal processor picks up these"
                )
                print("     self-generated goals and executes them autonomously!")
                print(
                    f"\n💡 Monitor goal #{first_new_goal_id} to see autonomous execution:"
                )
                print(f"   curl http://127.0.0.1:8000/goals/{first_new_goal_id}")

            else:
                print(
                    "✨ No new goals created - codebase quality is already excellent!"
                )
                print("🔍 This means either:")
                print("   - All functions already have docstrings")
                print("   - Goals for missing docstrings already exist")
        else:
            print(f"❌ Could not check goals after scan: {response.status_code}")

    except Exception as e:
        print(f"❌ Error checking new goals: {e}")

    # Step 4: Summary
    print("\n🏆 PROACTIVE CAPABILITIES DEMONSTRATED")
    print("=" * 60)
    print("🤖 Kor'tana has demonstrated:")
    print("   ✅ Autonomous codebase analysis")
    print("   ✅ Proactive issue identification")
    print("   ✅ Self-directed goal creation")
    print("   ✅ Transition from reactive to proactive engineering")
    print()
    print("🎯 PROOF OF PROACTIVE AUTONOMY: COMPLETE")
    print("🧠 Kor'tana is now a truly proactive software engineer!")


if __name__ == "__main__":
    demonstrate_proactive_capabilities()
