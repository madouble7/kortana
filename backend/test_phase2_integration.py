#!/usr/bin/env python
"""
Test Phase 2 integration: task_queue.py with dynamic classification
"""

import asyncio
import sys

from src.kortana.human_only_protocol import TaskClassification
from src.kortana.routers.task_queue import _hop, slugify


async def test_phase_2_integration():
    """Verify task_queue integration with HOP classifier"""

    print("Testing Phase 2: Task Queue Integration with Dynamic Classification")
    print("=" * 70)

    # Test 1: Slugify function
    slug = slugify("fix test failure")
    assert slug == "fix-test-failure"
    print(f"[PASS] slugify('fix test failure') -> '{slug}'")

    # Test 2: HOP instance exists and is callable
    assert _hop is not None
    assert hasattr(_hop, "classify_task")
    print("[PASS] HOP instance initialized in task_queue.py")

    # Test 3: Dynamic classification in task creation context
    # Simulating task creation for "fix_test_failure" in evolution/ branch
    context = {
        "branch": "evolution/abc-123-fix-test-failure",
        "task_name": "fix_test_failure",
        "task_type": "fix_test_failure",
    }

    task_type = context.get("task_type", "unknown")
    classification = _hop.classify_task(task_type=task_type, context=context)

    assert classification == TaskClassification.SELF_CORRECTION
    print(f"[PASS] Task classification dynamic resolution: {classification.value}")

    # Test 4: Enum value conversion (for DB storage)
    class_value = classification.value if hasattr(classification, "value") else str(classification)
    assert class_value == "self_correction"
    print(f"[PASS] Classification stored as enum value: '{class_value}'")

    # Test 5: Default classification handling
    default_context = {
        "branch": "feature/xyz-schema-update",
        "task_type": "schema_update",
    }

    schema_class = _hop.classify_task("schema_update", default_context)
    # In feature branch (not evolution/), should be HO
    assert schema_class == TaskClassification.HO
    print(f"[PASS] Non-evolution/ branch defaults to HO: {schema_class.value}")

    print("\n" + "=" * 70)
    print("Phase 2 Status: INTEGRATION SUCCESSFUL")
    print("=" * 70)
    print("\nPhase 2 Achievements:")
    print("- HOP classifier integrated into task_queue.py")
    print("- Dynamic classification resolved at task creation")
    print("- Branch context properly detected")
    print("- Enum values stored correctly for persistence")
    print("\nNext: Phase 3 - GitHub PR Automation")


if __name__ == "__main__":
    try:
        asyncio.run(test_phase_2_integration())
        sys.exit(0)
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
