#!/usr/bin/env python
"""
Test suite for Volitional Self-Correction Engine
Validates dynamic classification logic and SELF_CORRECTION tier functionality
"""

import sys

from src.kortana.human_only_protocol import HumanOnlyProtocol, TaskClassification


def test_volitional_self_correction_engine():
    """Comprehensive validation of dynamic classification"""
    hop = HumanOnlyProtocol()

    # Test 1: fix_test_failure in evolution/ branch
    result = hop.classify_task("fix_test_failure", {"branch": "evolution/abc-123-fix-test"})
    assert result == TaskClassification.SELF_CORRECTION
    print("[PASS] fix_test_failure in evolution/ -> SELF_CORRECTION")

    # Test 2: fix_test_failure in main branch
    result = hop.classify_task("fix_test_failure", {"branch": "main"})
    assert result == TaskClassification.HO
    print("[PASS] fix_test_failure in main -> HO")

    # Test 3: schema_update in evolution/
    result = hop.classify_task("schema_update", {"branch": "evolution/xyz-schema"})
    assert result == TaskClassification.SELF_CORRECTION
    print("[PASS] schema_update in evolution/ -> SELF_CORRECTION")

    # Test 4: code_refactor in evolution/
    result = hop.classify_task("code_refactor", {"branch": "evolution/refactor-123"})
    assert result == TaskClassification.AUTO
    print("[PASS] code_refactor in evolution/ -> AUTO")

    # Test 5: Unknown task defaults to HO
    result = hop.classify_task("unknown_task", {})
    assert result == TaskClassification.HO
    print("[PASS] unknown_task -> HO (safe default)")

    # Test 6: SELF_CORRECTION enum exists
    assert hasattr(TaskClassification, "SELF_CORRECTION")
    print("[PASS] TaskClassification.SELF_CORRECTION enum defined")

    # Test 7: SELF_CORRECTION value is correct
    assert TaskClassification.SELF_CORRECTION.value == "self_correction"
    print("[PASS] SELF_CORRECTION value = 'self_correction'")

    print("\n" + "=" * 70)
    print("SUCCESS: Volitional Self-Correction Engine validation complete")
    print("=" * 70)
    print("\nPhase 1 Status: OPERATIONAL")
    print("- Dynamic classification: WORKING")
    print("- Evolution/ branch detection: WORKING")
    print("- SELF_CORRECTION tier: ACTIVE")
    print("- Autonomous remediation path: READY")


if __name__ == "__main__":
    try:
        test_volitional_self_correction_engine()
        sys.exit(0)
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
