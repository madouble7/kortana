#!/usr/bin/env python3
"""Repair the environment and run tests."""

import os
import subprocess
import sys

venv_python = r"c:\kortana\.kortana_config_test_env\Scripts\python.exe"

print("=" * 60)
print("REPAIR AND TEST KOR'TANA")
print("=" * 60)

# Step 1: Verify Python works
print("\n✓ Step 1: Checking Python...")
result = subprocess.run([venv_python, "--version"], capture_output=True, text=True)
print(f"  {result.stdout.strip()}")

# Step 2: Install pytest
print("\n✓ Step 2: Installing pytest...")
result = subprocess.run(
    [venv_python, "-m", "pip", "install", "pytest", "--quiet"],
    capture_output=True,
    text=True,
)
if result.returncode == 0:
    print("  pytest installed successfully")
else:
    print(f"  Error: {result.stderr}")
    sys.exit(1)

# Step 3: List key packages
print("\n✓ Step 3: Checking installed packages...")
result = subprocess.run(
    [venv_python, "-m", "pip", "list"], capture_output=True, text=True
)
packages = [
    line
    for line in result.stdout.split("\n")
    if any(pkg in line.lower() for pkg in ["discord", "pytest", "kortana"])
]
for pkg in packages:
    if pkg.strip():
        print(f"  {pkg}")

# Step 4: Run tests
print("\n✓ Step 4: Running tests...")
os.environ["PYTHONPATH"] = r"c:\kortana\src"
result = subprocess.run(
    [venv_python, "-m", "pytest", r"c:\kortana\tests\test_brain.py", "-v"],
    capture_output=True,
    text=True,
    cwd=r"c:\kortana",
)

print("\n" + "=" * 60)
print("TEST OUTPUT:")
print("=" * 60)
print(result.stdout)
if result.stderr:
    print("ERRORS:")
    print(result.stderr)

if result.returncode == 0:
    print("\n✅ TESTS PASSED!")
else:
    print(f"\n❌ Tests failed with code {result.returncode}")
    print("\nIf this still fails, we'll use the simpler approach...")

print("=" * 60)
