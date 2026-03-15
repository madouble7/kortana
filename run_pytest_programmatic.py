#!/usr/bin/env python3
"""
Run pytest programmatically without relying on terminal
"""

import os
import sys

# Set up paths
os.chdir(r"c:\kortana")
sys.path.insert(0, os.path.join(os.getcwd(), "src"))

# Set environment variable
os.environ["PYTHONPATH"] = os.path.join(os.getcwd(), "src")

# Import and run pytest programmatically
import pytest

print("=" * 70)
print("Running Full Test Suite")
print("=" * 70)

# Run pytest
exit_code = pytest.main(["tests/", "-v", "--tb=short", "--color=yes"])

print("=" * 70)
print(f"Test run completed with exit code: {exit_code}")
print("=" * 70)

sys.exit(exit_code)
