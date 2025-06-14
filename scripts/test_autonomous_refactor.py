#!/usr/bin/env python3
"""
Test refactored autonomous tasks
"""

import sys

sys.path.insert(0, r"c:\project-kortana\src")

try:
    from kortana.core.autonomous_tasks import (
        get_execution_engine_instance,
        get_planning_engine_instance,
    )

    print("✅ Successfully imported refactored autonomous_tasks functions")

    # Test the function calls (they should work with fallback)
    planning = get_planning_engine_instance()
    execution = get_execution_engine_instance()
    print(f"✅ Planning engine: {type(planning)}")
    print(f"✅ Execution engine: {type(execution)}")

    print("\n🎉 Autonomous tasks refactoring test passed!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
