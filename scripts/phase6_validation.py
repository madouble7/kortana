#!/usr/bin/env python3
"""
Phase 6: Full System Validation
Test that circular dependencies are resolved and tools work properly
"""

import os
import subprocess
import sys
import time
from datetime import datetime

# Set up environment
project_root = r"c:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)


def run_command(cmd, description, timeout=300):
    """Run a command and capture output with timeout"""
    print(f"\n{'=' * 60}")
    print(f"🧪 {description}")
    print(f"{'=' * 60}")
    print(f"Command: {cmd}")
    print(f"Timeout: {timeout}s")
    print("-" * 60)

    start_time = time.time()

    try:
        # Run the command
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=project_root,
        )

        end_time = time.time()
        duration = end_time - start_time

        print(f"✅ Command completed in {duration:.2f}s")
        print(f"Return code: {result.returncode}")

        if result.stdout:
            print("\n📤 STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("\n⚠️  STDERR:")
            print(result.stderr)

        return result.returncode == 0, result.stdout, result.stderr, duration

    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out after {timeout}s")
        return False, "", f"Timeout after {timeout}s", timeout
    except Exception as e:
        print(f"❌ Command failed with exception: {e}")
        return False, "", str(e), 0


def main():
    """Run the full system validation"""
    print("🚀 PHASE 6: FULL SYSTEM VALIDATION")
    print("=" * 60)
    print("Testing that circular dependency fixes resolved blocking issues")
    print(f"Project root: {project_root}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # Test 1: Basic import test
    print("\n🧪 TEST 1: Basic Import Validation")
    success, stdout, stderr, duration = run_command(
        "C:\\project-kortana\\venv311\\Scripts\\python.exe -c \"import src.kortana.main; print('✅ Main module imports successfully')\"",
        "Basic FastAPI import test",
        30,
    )
    results.append(("Basic Import", success, duration))

    # Test 2: pytest collection (the main test)
    print("\n🧪 TEST 2: pytest Collection Test")
    success, stdout, stderr, duration = run_command(
        "C:\\project-kortana\\venv311\\Scripts\\python.exe -m pytest --collect-only --tb=short",
        "pytest test collection (was hanging before fix)",
        120,
    )
    results.append(("pytest Collection", success, duration))

    # Test 3: mypy type checking
    print("\n🧪 TEST 3: mypy Type Checking")
    success, stdout, stderr, duration = run_command(
        "C:\\project-kortana\\venv311\\Scripts\\python.exe -m mypy src/kortana/core --ignore-missing-imports",
        "mypy static type checking (was hanging before fix)",
        180,
    )
    results.append(("mypy Type Check", success, duration))

    # Test 4: Quick functional test
    print("\n🧪 TEST 4: Quick Functional Test")
    success, stdout, stderr, duration = run_command(
        "C:\\project-kortana\\venv311\\Scripts\\python.exe -m pytest tests/ -v --tb=short -x --timeout=60",
        "Quick functional test run",
        120,
    )
    results.append(("Functional Tests", success, duration))

    # Summary
    print("\n" + "=" * 60)
    print("📊 PHASE 6 VALIDATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed, duration in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name:20} ({duration:6.2f}s)")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 PHASE 6 VALIDATION: COMPLETE SUCCESS!")
        print("✅ Circular dependencies resolved")
        print("✅ Tools no longer hang")
        print("✅ System is ready for Genesis Protocol")
        print("🚀 Ready to proceed to The Proving Ground!")
    else:
        print("⚠️  PHASE 6 VALIDATION: PARTIAL SUCCESS")
        print("Some tests failed - review output above")
        print("May need additional fixes before Genesis Protocol")

    print("=" * 60)
    print(f"Validation completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
