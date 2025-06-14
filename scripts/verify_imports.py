#!/usr/bin/env python3
"""
Import Verification Script for Kor'tana
========================================
Tests all critical imports to verify the system is ready for autonomous operation.
"""

import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_import(module_name, description):
    """Test importing a module and report results."""
    try:
        print(f"Testing {description}...", end=" ")
        __import__(module_name)
        print("✅ SUCCESS")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        if "traceback" in sys.argv:
            traceback.print_exc()
        return False


def main():
    """Run comprehensive import tests."""
    print("🔍 IMPORT VERIFICATION SUITE")
    print("=" * 50)

    tests = [
        ("kortana.core.scheduler", "Autonomous Scheduler"),
        ("kortana.core.covenant", "Covenant Enforcer"),
        ("kortana.core.goal_framework", "Goal Framework"),
        ("kortana.core.goals.engine", "Goal Engine"),
        ("kortana.core.goals.generator", "Goal Generator"),
        ("kortana.core.goals.prioritizer", "Goal Prioritizer"),
        ("kortana.core.execution_engine", "Execution Engine"),
        ("kortana.core.task_management.coordinator", "Task Coordinator"),
        ("kortana.core.environmental_scanner", "Environmental Scanner"),
        ("kortana.memory.memory_manager", "Memory Manager"),
        ("kortana.core.brain", "Brain Module"),
    ]

    passed = 0
    total = len(tests)

    for module, description in tests:
        if test_import(module, description):
            passed += 1

    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {passed}/{total} imports successful")

    if passed == total:
        print("🎉 All imports successful! System ready for autonomous operation.")
        return True
    else:
        print(f"⚠️  {total - passed} imports failed. Review errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
