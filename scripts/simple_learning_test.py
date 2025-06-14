#!/usr/bin/env python3
"""
Simple Learning Loop Test
=========================

Direct test of the learning loop functionality without API dependencies.
"""

import asyncio
import os
import sys

# Add project root to path
project_root = r"c:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)

# Import required modules
from src.kortana.modules.memory_core.models import MemoryType
from src.kortana.modules.memory_core.schemas import CoreMemoryCreate
from src.kortana.modules.memory_core.services import MemoryCoreService
from src.kortana.services.database import get_db_sync


async def create_test_memories():
    """Create test memories to simulate goal outcomes."""
    print("📝 Creating test memories to simulate goal outcomes...")

    db = next(get_db_sync())
    memory_service = MemoryCoreService(db)

    # Create a success memory
    success_memory = CoreMemoryCreate(
        memory_type=MemoryType.OBSERVATION,
        title="Autonomous Goal Outcome: Create test file (COMPLETED)",
        content="Goal ID 1: Create a file in the docs folder named 'test_success.md'\nStatus: COMPLETED\nSummary: Successfully created file with proper content.",
        memory_metadata={
            "source": "goal_processing_cycle",
            "is_self_reflection": True,
            "goal_id": 1,
        },
    )

    # Create a failure memory
    failure_memory = CoreMemoryCreate(
        memory_type=MemoryType.OBSERVATION,
        title="Autonomous Goal Outcome: Create forbidden file (FAILED)",
        content="Goal ID 2: Attempt to create a file in a forbidden directory '/etc/test_fail.txt'\nStatus: FAILED\nSummary: Failed due to security restrictions - cannot write to system directories.",
        memory_metadata={
            "source": "goal_processing_cycle",
            "is_self_reflection": True,
            "goal_id": 2,
        },
    )

    # Save memories
    success_created = memory_service.create_memory(memory_create=success_memory)
    failure_created = memory_service.create_memory(memory_create=failure_memory)

    print(f"✅ Created success memory: ID {success_created.id}")
    print(f"✅ Created failure memory: ID {failure_created.id}")

    db.close()
    return True


async def test_learning_loop():
    """Test the learning loop with mock data."""
    print("\n🧠 Testing Learning Loop...")

    try:
        # Import the learning function
        from src.kortana.core.autonomous_tasks import run_performance_analysis_task

        # Get database session
        db = next(get_db_sync())

        # Run the learning loop
        await run_performance_analysis_task(db)

        print("✅ Learning loop completed!")
        return True

    except Exception as e:
        print(f"❌ Error in learning loop: {e}")
        import traceback

        traceback.print_exc()
        return False


async def check_core_beliefs():
    """Check if any core beliefs were created."""
    print("\n💡 Checking for new core beliefs...")

    db = next(get_db_sync())
    memory_service = MemoryCoreService(db)

    try:
        # Get all core beliefs
        from src.kortana.modules.memory_core import models

        core_beliefs = (
            db.query(models.CoreMemory)
            .filter(models.CoreMemory.memory_type == MemoryType.CORE_BELIEF)
            .all()
        )

        if core_beliefs:
            print(f"✅ Found {len(core_beliefs)} core belief(s):")
            for belief in core_beliefs:
                print(f"   💭 {belief.title}")
                print(f"      Content: {belief.content}")
                print(f"      Created: {belief.created_at}")
                print()
        else:
            print("❌ No core beliefs found.")

        return len(core_beliefs) > 0

    except Exception as e:
        print(f"❌ Error checking core beliefs: {e}")
        return False
    finally:
        db.close()


async def main():
    print("🔬 SIMPLE LEARNING LOOP TEST")
    print("=" * 40)
    print("Testing Kor'tana's ability to learn from experience...")
    print()

    # Step 1: Create test memories
    await create_test_memories()

    # Step 2: Run learning loop
    learning_success = await test_learning_loop()

    # Step 3: Check results
    beliefs_created = await check_core_beliefs()

    print("\n📊 TEST RESULTS")
    print("=" * 20)
    if learning_success and beliefs_created:
        print("🎉 SUCCESS! Kor'tana's learning loop is working!")
        print("✅ She can analyze her experiences and form new beliefs.")
    elif learning_success:
        print("⚠️  PARTIAL SUCCESS: Learning loop ran but no beliefs created.")
        print("   This might be expected if no patterns were detected.")
    else:
        print("❌ FAILURE: Learning loop encountered errors.")

    print("\n🧠 Kor'tana's first lesson test complete!")


if __name__ == "__main__":
    asyncio.run(main())
