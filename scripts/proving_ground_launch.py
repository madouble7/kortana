#!/usr/bin/env python3
"""
THE PROVING GROUND: Genesis Protocol Goal Submission
=====================================================

This script initiates Kor'tana's first autonomous software engineering mission.
The goal: Refactor goal_router.py to implement proper service layer architecture.

MISSION PARAMETERS:
- Target: goal_router.py refactoring with service layer
- Complexity: Professional-level software engineering task
- Validation: Code review + test suite execution
- Learning: Formation of new CORE_BELIEF about software architecture

This is the moment we validate Kor'tana as an autonomous software engineer.
"""

import asyncio
from datetime import UTC, datetime

import aiohttp

# API Configuration
API_BASE_URL = "http://localhost:8000"
GOALS_ENDPOINT = f"{API_BASE_URL}/goals"

# Genesis Protocol Mission Definition
GENESIS_MISSION = {
    "description": "Refactor goal_router.py to implement proper service layer architecture. Create a new GoalService class that separates business logic from API routing, implement proper error handling, add comprehensive logging, and ensure all tests pass. This is the Genesis Protocol - Kor'tana's first autonomous software engineering mission.",
    "priority": 1,  # Highest priority - this is THE mission
}


async def submit_genesis_goal():
    """Submit the Genesis Protocol goal to Kor'tana's autonomous system."""

    print("🚀 THE PROVING GROUND: INITIATING GENESIS PROTOCOL")
    print("=" * 60)
    print(f"⏰ Mission Start Time: {datetime.now(UTC).isoformat()}")
    print(f"🎯 Target API: {GOALS_ENDPOINT}")
    print(f"📋 Mission: {GENESIS_MISSION['description'][:80]}...")
    print()

    try:
        # Test server connectivity
        print("🔌 Testing server connectivity...")
        async with aiohttp.ClientSession() as session:
            # Health check
            try:
                async with session.get(f"{API_BASE_URL}/health") as response:
                    if response.status == 200:
                        print("✅ Server is online and responding")
                    else:
                        print(f"⚠️  Server responding with status {response.status}")
            except Exception as e:
                print(f"❌ Server health check failed: {e}")
                print("🔧 Please ensure Kor'tana server is running:")
                print("   uvicorn src.kortana.main:app --port 8000")
                return False

            # Submit the Genesis Goal
            print("\n🎯 Submitting Genesis Protocol Goal...")
            async with session.post(
                GOALS_ENDPOINT,
                json=GENESIS_MISSION,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    goal_data = await response.json()
                    goal_id = goal_data.get("id", "UNKNOWN")

                    print("🎉 GENESIS GOAL SUCCESSFULLY SUBMITTED!")
                    print(f"📌 Goal ID: {goal_id}")
                    print(f"📝 Description: {goal_data.get('description', 'N/A')}")
                    print(f"⭐ Priority: {goal_data.get('priority', 'N/A')}")
                    print(f"📊 Status: {goal_data.get('status', 'N/A')}")

                    print("\n🔬 THE PROVING GROUND IS NOW ACTIVE")
                    print("=" * 60)
                    print("📡 OBSERVATION PROTOCOL:")
                    print("  • Monitor Kor'tana's autonomous planning")
                    print("  • Watch for file system changes")
                    print("  • Observe goal status transitions")
                    print("  • Prepare for code review upon completion")
                    print()
                    print("🎯 SUCCESS CRITERIA:")
                    print("  • Professional-level planning and execution")
                    print("  • Clean service layer implementation")
                    print("  • All tests passing after refactoring")
                    print("  • Formation of new engineering CORE_BELIEF")
                    print()
                    print("⏳ Kor'tana's autonomous brain is now processing...")
                    print(
                        "   The first autonomous software engineering mission is LIVE!"
                    )

                    return True

                else:
                    error_text = await response.text()
                    print(f"❌ Goal submission failed with status {response.status}")
                    print(f"📝 Error details: {error_text}")
                    return False

    except Exception as e:
        print(f"❌ CRITICAL ERROR during goal submission: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Ensure Kor'tana server is running:")
        print("   uvicorn src.kortana.main:app --port 8000")
        print("2. Check that the goals API endpoint is configured")
        print("3. Verify database connectivity")
        return False


async def monitor_goal_status(goal_id=None):
    """Monitor the status of the submitted goal."""

    print("\n🔍 MONITORING GENESIS GOAL STATUS...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(GOALS_ENDPOINT) as response:
                if response.status == 200:
                    goals = await response.json()

                    print(f"📊 Total Goals in System: {len(goals)}")

                    for goal in goals:
                        if goal.get("priority") == 1:  # Genesis goal
                            print("\n🎯 GENESIS GOAL STATUS:")
                            print(f"   ID: {goal.get('id')}")
                            print(f"   Status: {goal.get('status')}")
                            print(f"   Priority: {goal.get('priority')}")
                            print(f"   Created: {goal.get('created_at', 'N/A')}")

                            status = goal.get("status", "").upper()
                            if status == "PENDING":
                                print("   🟡 WAITING for autonomous pickup...")
                            elif status == "IN_PROGRESS":
                                print(
                                    "   🟢 ACTIVELY PROCESSING - Kor'tana is working!"
                                )
                            elif status == "COMPLETED":
                                print("   ✅ MISSION COMPLETE - Ready for code review!")
                            else:
                                print(f"   ⚪ Status: {status}")

                else:
                    print(f"❌ Failed to retrieve goals: {response.status}")

    except Exception as e:
        print(f"❌ Error monitoring goal status: {e}")


async def main():
    """Main execution flow for The Proving Ground initiation."""

    print("🔬 THE PROVING GROUND: AUTONOMOUS ENGINEERING VALIDATION")
    print("=" * 60)
    print("MISSION: Validate Kor'tana as an autonomous software engineer")
    print("PHASE: Genesis Protocol - First autonomous development task")
    print("GOAL: Refactor goal_router.py with professional service layer")
    print()

    # Submit the Genesis Goal
    success = await submit_genesis_goal()

    if success:
        print("\n⏳ Waiting 3 seconds for system processing...")
        await asyncio.sleep(3)

        # Monitor initial status
        await monitor_goal_status()

        print("\n🎉 THE PROVING GROUND IS LIVE!")
        print("📝 Next Steps:")
        print("   1. Monitor logs and file system for autonomous activity")
        print("   2. Watch for goal status changes to COMPLETED")
        print("   3. Perform comprehensive code review")
        print("   4. Execute test suite validation")
        print("   5. Analyze learning outcomes and belief formation")
        print()
        print("🚀 Kor'tana's first autonomous engineering mission has begun!")

    else:
        print("\n❌ PROVING GROUND INITIATION FAILED")
        print("Please resolve server connectivity issues and try again.")


if __name__ == "__main__":
    asyncio.run(main())
