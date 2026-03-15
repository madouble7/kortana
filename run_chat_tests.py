#!/usr/bin/env python
"""
Chat functionality test runner.
Runs tests and displays results with clear formatting.
"""

import os
import subprocess
import sys

# Set up environment
os.environ["PYTHONPATH"] = r"c:\kortana\src"
os.chdir(r"c:\kortana")

print("=" * 70)
print("🗣️  KOR'TANA CHAT FUNCTIONALITY TEST SUITE")
print("=" * 70)
print()

# Run pytest with the chat functionality tests
test_file = r"tests\test_chat_functionality.py"

print(f"Running tests from: {test_file}")
print("-" * 70)
print()

try:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            test_file,
            "-v",
            "--tb=short",
            "-s",
        ],
        capture_output=False,
        text=True,
    )

    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"⚠️  SOME TESTS HAD ISSUES (Return code: {result.returncode})")
    print("=" * 70)

    sys.exit(result.returncode)

except Exception as e:
    print(f"❌ Error running tests: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
