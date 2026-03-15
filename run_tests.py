#!/usr/bin/env python3
"""
Run the full test suite with proper environment setup
"""

import os
import subprocess
import sys


def main():
    os.chdir(r"c:\kortana")

    # Use the venv's Python directly
    venv_python = r".\.kortana_config_test_env\Scripts\python.exe"

    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = r"c:\kortana\src"
    env["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

    # Run pytest
    print("=" * 70)
    print("Running full test suite...")
    print("=" * 70)

    result = subprocess.run(
        [venv_python, "-m", "pytest", r"tests/", "-v", "--tb=short"], env=env
    )

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
