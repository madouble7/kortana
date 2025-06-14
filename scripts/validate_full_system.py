#!/usr/bin/env python3
"""
Full System Validation Script
============================
Tests that our circular dependency refactoring has resolved import issues
and that quality assurance tools can now run without hanging.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# Set up project root
project_root = Path(r"C:\project-kortana")
os.chdir(project_root)
sys.path.insert(0, str(project_root))

print("=" * 70)
print("FULL SYSTEM VALIDATION - POST CIRCULAR DEPENDENCY REFACTOR")
print("=" * 70)


def run_with_timeout(cmd, timeout=30, shell=True):
    """Run a command with timeout to prevent hanging."""
    try:
        print(f"\n🔧 Running: {cmd}")
        print(f"   Timeout: {timeout}s")

        start_time = time.time()
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=project_root,
        )

        elapsed = time.time() - start_time
        print(f"   Completed in: {elapsed:.2f}s")

        if result.returncode == 0:
            print("   ✅ SUCCESS")
        else:
            print(f"   ⚠️  Return code: {result.returncode}")

        return result

    except subprocess.TimeoutExpired:
        print(f"   ❌ TIMEOUT after {timeout}s")
        return None
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return None


def test_key_imports():
    """Test that key modules can be imported without circular dependency issues."""
    print("\n📦 Testing Key Module Imports")
    print("-" * 40)

    critical_imports = [
        "src.config.schema",
        "src.kortana.core.services",
        "src.kortana.core.brain",
        "src.kortana.memory.brain_router",
        "phase5_advanced_autonomous",
    ]

    success_count = 0
    for module in critical_imports:
        try:
            print(f"   Importing {module}...", end=" ")
            __import__(module)
            print("✅")
            success_count += 1
        except Exception as e:
            print(f"❌ {e}")

    print(f"\n   Import Success Rate: {success_count}/{len(critical_imports)}")
    return success_count == len(critical_imports)


def test_pytest_collection():
    """Test pytest test collection without hanging."""
    print("\n🧪 Testing Pytest Test Collection")
    print("-" * 40)

    # First try just collection
    result = run_with_timeout("python -m pytest --collect-only -q", timeout=30)

    if result is None:
        print(
            "   ❌ pytest collection TIMED OUT (circular dependency issue likely persists)"
        )
        return False
    elif result.returncode == 0:
        print("   ✅ pytest collection SUCCESSFUL")
        print(f"   Output preview: {result.stdout[:200]}...")
        return True
    else:
        print("   ⚠️  pytest collection completed with errors")
        print(f"   stderr: {result.stderr[:200]}...")
        return result.returncode in [1, 5]  # 1=tests failed, 5=no tests collected


def test_mypy_analysis():
    """Test mypy static analysis without hanging."""
    print("\n🔍 Testing Mypy Static Analysis")
    print("-" * 40)

    # Test on a specific file first
    result = run_with_timeout(
        "python -c \"import mypy.api; print('mypy available')\"", timeout=10
    )

    if result is None:
        print("   ❌ mypy not available or hanging")
        return False
    elif result.returncode == 0:
        print("   ✅ mypy is available")

        # Try analysis on a small file
        result = run_with_timeout("python -m mypy src/config/schema.py", timeout=20)
        if result is None:
            print("   ❌ mypy analysis TIMED OUT")
            return False
        else:
            print("   ✅ mypy analysis COMPLETED")
            return True
    else:
        print("   ⚠️  mypy not properly installed")
        return False


def test_autonomous_system():
    """Test that the autonomous system can be imported and initialized."""
    print("\n🤖 Testing Autonomous System Initialization")
    print("-" * 40)

    try:
        from phase5_advanced_autonomous import AdvancedAutonomousKortana

        print("   ✅ Phase 5 import successful")

        kortana = AdvancedAutonomousKortana()
        print("   ✅ Phase 5 instance created")

        # Test basic functionality
        if hasattr(kortana, "autonomous_state"):
            print("   ✅ Autonomous state available")

        if hasattr(kortana, "_gather_comprehensive_context"):
            print("   ✅ Context gathering method available")

        if hasattr(kortana, "_process_strategic_insights"):
            print("   ✅ Strategic insights method available")

        return True

    except Exception as e:
        print(f"   ❌ Autonomous system test failed: {e}")
        return False


def main():
    """Run full system validation."""

    results = {}

    # Test 1: Key Imports
    results["imports"] = test_key_imports()

    # Test 2: Pytest Collection
    results["pytest"] = test_pytest_collection()

    # Test 3: Mypy Analysis
    results["mypy"] = test_mypy_analysis()

    # Test 4: Autonomous System
    results["autonomous"] = test_autonomous_system()

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(results.values())
    total = len(results)

    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test.upper():15} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 FULL SYSTEM VALIDATION: SUCCESS!")
        print("✅ Circular dependencies resolved")
        print("✅ Quality assurance tools operational")
        print("✅ Ready for Proving Ground phase")
    else:
        print(f"\n⚠️  PARTIAL SUCCESS: {passed}/{total}")
        print("Some issues remain that need attention")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
