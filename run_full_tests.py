#!/usr/bin/env python
"""Run full test suite with proper environment setup."""

import os
import subprocess
import sys


def main():
    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "src")
    env["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

    # Run pytest
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"], env=env
    )

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
