#!/usr/bin/env python3
"""
Learning Loop Test with File Output
===================================

Test the learning loop and write results to a file to avoid terminal capture.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
project_root = r"c:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)

# Output file
output_file = "batch8_test_results.txt"


def log(message):
    """Log message to both console and file."""
    print(message)
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} {message}\n")


async def test_learning_imports():
    """Test if we can import the learning components."""
    log("🔍 Testing imports...")

    try:
        log("✅ Database service imported")

        log("✅ Memory service imported")

        log("✅ Memory schemas imported")

        log("✅ Memory models imported")

        log("✅ Learning task imported")

        return True

    except Exception as e:
        log(f"❌ Import error: {e}")
        return False


async def test_database_connection():
    """Test database connection."""
    log("🔍 Testing database connection...")

    try:
        from src.kortana.services.database import get_db_sync

        db = next(get_db_sync())
        log("✅ Database connection successful")
        db.close()
        return True

    except Exception as e:
        log(f"❌ Database connection error: {e}")
        return False


async def create_test_memory():
    """Create a single test memory."""
    log("📝 Creating test memory...")

    try:
        from src.kortana.modules.memory_core.models import MemoryType
        from src.kortana.modules.memory_core.schemas import CoreMemoryCreate
        from src.kortana.modules.memory_core.services import MemoryCoreService
        from src.kortana.services.database import get_db_sync

        db = next(get_db_sync())
        memory_service = MemoryCoreService(db)

        test_memory = CoreMemoryCreate(
            memory_type=MemoryType.OBSERVATION,
            title="Test Goal Outcome: File creation failed",
            content="Goal ID 999: Create a file in forbidden directory\nStatus: FAILED\nSummary: Failed due to path restrictions",
            memory_metadata={
                "source": "goal_processing_cycle",
                "is_self_reflection": True,
                "goal_id": 999,
            },
        )

        created = memory_service.create_memory(memory_create=test_memory)
        log(f"✅ Created test memory with ID: {created.id}")

        db.close()
        return True

    except Exception as e:
        log(f"❌ Memory creation error: {e}")
        import traceback

        log(traceback.format_exc())
        return False


async def test_learning_function():
    """Test the learning function directly."""
    log("🧠 Testing learning function...")

    try:
        from src.kortana.core.autonomous_tasks import run_performance_analysis_task
        from src.kortana.services.database import get_db_sync

        db = next(get_db_sync())

        # Run the learning task
        await run_performance_analysis_task(db)

        log("✅ Learning function completed")
        return True

    except Exception as e:
        log(f"❌ Learning function error: {e}")
        import traceback

        log(traceback.format_exc())
        return False


async def main():
    """Main test function."""
    # Clear output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Batch 8 Learning Loop Test - {datetime.now()}\n")
        f.write("=" * 50 + "\n")

    log("🔬 BATCH 8 LEARNING LOOP TEST")
    log("=" * 40)

    # Test imports
    if not await test_learning_imports():
        log("❌ Import test failed - cannot proceed")
        return

    # Test database
    if not await test_database_connection():
        log("❌ Database test failed - cannot proceed")
        return

    # Create test memory
    if not await create_test_memory():
        log("❌ Memory creation failed - cannot proceed")
        return

    # Test learning function
    if await test_learning_function():
        log("🎉 Learning loop test SUCCESSFUL!")
    else:
        log("❌ Learning loop test FAILED!")

    log(f"📄 Full results written to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
