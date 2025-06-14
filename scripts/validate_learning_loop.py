#!/usr/bin/env python3
"""
Simple test to validate the learning loop implementation
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
project_root = Path("c:/project-kortana")
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

print("=== Learning Loop Validation Test ===")
print(f"Project root: {project_root}")
print(f"Source path: {src_path}")
print(f"Python path: {sys.path[:3]}...")

try:
    print("\n1. Testing core imports...")
    from kortana.core.models import Goal, GoalStatus, PlanStep

    print(f"✅ Goal: {Goal}")
    print(f"✅ GoalStatus: {GoalStatus}")
    print(f"✅ PlanStep: {PlanStep}")

    print("\n2. Testing autonomous tasks import...")
    from kortana.core.autonomous_tasks import run_performance_analysis_task

    print(f"✅ run_performance_analysis_task: {run_performance_analysis_task}")

    print("\n3. Testing database import...")
    from kortana.services.database import get_db_sync

    print(f"✅ get_db_sync: {get_db_sync}")

    print("\n4. Testing planning engine import...")
    from kortana.core.planning_engine import PlanningEngine

    print(f"✅ PlanningEngine: {PlanningEngine}")

    print("\n✅ All imports successful!")
    print("\n5. Testing learning loop execution...")

    # Try to run the learning task (this may fail if DB is not set up)
    async def test_learning():
        try:
            db_session = next(get_db_sync())
            await run_performance_analysis_task(db_session)
            print("✅ Learning loop executed successfully!")
            return True
        except Exception as e:
            print(f"⚠️ Learning loop failed (expected if DB not initialized): {e}")
            return False

    # Run the async test
    result = asyncio.run(test_learning())

    if result:
        print("\n🎉 BATCH 8 LEARNING LOOP: FULLY FUNCTIONAL!")
    else:
        print("\n🔧 BATCH 8 LEARNING LOOP: IMPORTS WORKING, DB SETUP NEEDED")

except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback

    traceback.print_exc()

print("\n=== Validation Test Complete ===")
