#!/usr/bin/env python
"""Diagnostic script to verify environment is ready for testing."""

import os
import subprocess
import sys


def diagnose():
    """Run diagnostic checks."""
    os.chdir(r"c:\kortana")

    print("=" * 70)
    print("ENVIRONMENT DIAGNOSTIC")
    print("=" * 70 + "\n")

    # Check 1: Python executable exists
    venv_python = r"c:\kortana\.kortana_config_test_env\Scripts\python.exe"
    print(f"1. Checking venv Python: {venv_python}")
    if os.path.exists(venv_python):
        print("   ✓ Python executable exists\n")
    else:
        print(f"   ✗ NOT FOUND: {venv_python}\n")
        return False

    # Check 2: Pytest is installed
    print("2. Checking pytest installation...")
    result = subprocess.run(
        [venv_python, "-m", "pip", "show", "pytest"], capture_output=True, text=True
    )
    if result.returncode == 0:
        print("   ✓ pytest is installed\n")
    else:
        print("   ✗ pytest NOT installed\n")
        return False

    # Check 3: Can import kortana
    print("3. Checking kortana package...")
    env = os.environ.copy()
    env["PYTHONPATH"] = r"c:\kortana\src"
    result = subprocess.run(
        [venv_python, "-c", 'import kortana; print("kortana imported successfully")'],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"   ✓ {result.stdout.strip()}\n")
    else:
        print(f"   ✗ Import failed: {result.stderr}\n")
        return False

    # Check 4: Display test files
    print("4. Checking test files...")
    test_dir = r"c:\kortana\tests"
    if os.path.isdir(test_dir):
        test_files = [
            f
            for f in os.listdir(test_dir)
            if f.startswith("test_") and f.endswith(".py")
        ]
        print(f"   ✓ Found {len(test_files)} test files:")
        for f in test_files[:5]:
            print(f"      - {f}")
        if len(test_files) > 5:
            print(f"      ... and {len(test_files) - 5} more")
        print()
    else:
        print(f"   ✗ Test directory not found: {test_dir}\n")
        return False

    # Check 5: Run pytest discovery
    print("5. Running pytest discovery...")
    result = subprocess.run(
        [venv_python, "-m", "pytest", "--collect-only", "-q", "tests/"],
        env=env,
        capture_output=True,
        text=True,
        cwd=r"c:\kortana",
    )
    if result.returncode == 0:
        lines = result.stdout.split("\n")
        # Get counts
        collected = [l for l in lines if "collected" in l or "test session" in l]
        if collected:
            print(f"   ✓ {collected[0]}\n")
        else:
            print("   ✓ Tests discovered\n")
    else:
        print(f"   ⚠ Discovery had warnings: {result.stderr[:200]}\n")

    return True


if __name__ == "__main__":
    success = diagnose()
    if success:
        print("=" * 70)
        print("READY TO RUN TESTS!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("=" * 70)
        print("SETUP INCOMPLETE - Fix issues above first")
        print("=" * 70)
        sys.exit(1)
