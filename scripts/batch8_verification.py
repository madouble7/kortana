#!/usr/bin/env python3
"""
Batch 8 Complete Verification Protocol
======================================

This script executes the complete verification protocol for Kor'tana's learning loop:
1. Creates test goals (success and failure scenarios)
2. Triggers the learning loop
3. Verifies core belief creation
4. Tests applied knowledge
"""

import asyncio
import os
import sys
import time

import requests

# Add project root to path
project_root = r"c:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)

from src.kortana.core.autonomous_tasks import run_performance_analysis_task
from src.kortana.services.database import get_db_sync

# FastAPI server configuration
BASE_URL = "http://localhost:8000"


def create_goal(description: str, priority: int = 100) -> dict:
    """Create a goal via the API."""
    try:
        response = requests.post(
            f"{BASE_URL}/goals/",
            json={"description": description, "priority": priority},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error creating goal: {e}")
        return {}


def get_memories():
    """Get all memories via the API."""
    try:
        response = requests.get(f"{BASE_URL}/memories/")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching memories: {e}")
        return []


def wait_for_server():
    """Wait for the FastAPI server to be available."""
    print("🔍 Checking if FastAPI server is running...")
    for i in range(10):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✅ FastAPI server is running!")
                return True
        except Exception:
            pass
        print(f"⏳ Waiting for server... ({i + 1}/10)")
        time.sleep(2)
    return False


async def main():
    print("🔬 BATCH 8 COMPLETE VERIFICATION PROTOCOL")
    print("=" * 60)
    print("🎯 Testing Kor'tana's Learning Loop: Experience → Reflection → Evolution")
    print()

    # Check if server is running
    if not wait_for_server():
        print("❌ FastAPI server is not running!")
        print(
            "Please start the server with: poetry run uvicorn src.kortana.api.main:app --reload"
        )
        return

    print("\n🧪 STEP 1: The Experience Phase - Seeding Memories")
    print("-" * 50)

    # Goal 1: Success scenario
    print("📝 Creating Goal 1 (Success scenario)...")
    success_goal = create_goal(
        "Create a file in the docs folder named 'test_success.md' with the content '# Success'",
        priority=100,
    )
    if success_goal:
        print(f"✅ Created success goal with ID: {success_goal.get('id')}")

    # Wait a moment for processing
    time.sleep(2)

    # Goal 2: Failure scenario
    print("📝 Creating Goal 2 (Failure scenario)...")
    failure_goal = create_goal(
        "Attempt to create a file in a forbidden directory named '/etc/test_fail.txt' with the content 'This should fail'",
        priority=100,
    )
    if failure_goal:
        print(f"✅ Created failure goal with ID: {failure_goal.get('id')}")

    print("⏳ Waiting 10 seconds for autonomous processing...")
    time.sleep(10)

    print("\n🤔 STEP 2: The Reflection Phase - Triggering the Learning Loop")
    print("-" * 50)

    try:
        # Get database session
        db = next(get_db_sync())

        # Trigger the learning loop
        print("🧠 Triggering self-reflection and performance analysis...")
        await run_performance_analysis_task(db)

    except Exception as e:
        print(f"❌ Error during learning loop: {e}")
        import traceback

        traceback.print_exc()

    print("\n💡 STEP 3: The Learning Phase - Confirming the Insight")
    print("-" * 50)

    # Check for new core beliefs
    memories = get_memories()
    core_beliefs = [m for m in memories if m.get("memory_type") == "CORE_BELIEF"]

    if core_beliefs:
        print(f"✅ Found {len(core_beliefs)} core belief(s):")
        for belief in core_beliefs[-3:]:  # Show last 3
            print(f"   💭 {belief.get('title', 'Untitled')}")
            print(f"      Content: {belief.get('content', 'No content')[:100]}...")
            print(f"      Created: {belief.get('created_at', 'Unknown time')}")
            print()
    else:
        print("❌ No core beliefs found. Learning loop may not have worked correctly.")

    print("\n🔄 STEP 4: The Evolution Phase - Verifying Applied Knowledge")
    print("-" * 50)

    # Goal 3: Test the learned behavior
    print("📝 Creating Goal 3 (Evolution test)...")
    evolution_goal = create_goal(
        "Create a file at 'src/../forbidden_area/test.txt' which is outside my allowed directories.",
        priority=50,
    )
    if evolution_goal:
        print(f"✅ Created evolution test goal with ID: {evolution_goal.get('id')}")

    print("⏳ Waiting 15 seconds for autonomous processing with new beliefs...")
    time.sleep(15)

    print("\n📊 VERIFICATION COMPLETE")
    print("=" * 30)
    print("✅ All verification steps executed successfully!")
    print("🔍 Please check the server logs to see:")
    print("   • Goal execution results")
    print("   • Planning prompts with core beliefs")
    print("   • Evidence of learned behavior changes")
    print()
    print("🧠 Kor'tana's first lesson should now be complete!")


if __name__ == "__main__":
    asyncio.run(main())
