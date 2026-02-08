#!/usr/bin/env python
"""Simple test runner that outputs results to a file."""

import os
import subprocess
import sys

# Set environment variables
env = os.environ.copy()
env["PYTHONPATH"] = os.path.join(os.getcwd(), "src")
env["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Run pytest
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
    env=env,
    capture_output=True,
    text=True
)

# Write output to file
with open("test_results.txt", "w") as f:
    f.write(result.stdout)
    f.write("\n\nSTDERR:\n")
    f.write(result.stderr)

# Also print to console
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr)

sys.exit(result.returncode)
