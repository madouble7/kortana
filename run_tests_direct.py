#!/usr/bin/env python3
"""
Direct pytest runner that bypasses terminal activation issues
"""

import os
import subprocess
import sys


def run_tests():
    """Run pytest directly"""
    # Change to the project directory
    os.chdir(r"c:\kortana")

    # Get the venv python path
    venv_python = os.path.join(
        os.getcwd(), ".kortana_config_test_env", "Scripts", "python.exe"
    )

    # Check if venv python exists
    if not os.path.exists(venv_python):
        print(f"ERROR: venv python not found at {venv_python}")
        return 1

    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "src")

    # Run pytest
    print(f"Using Python: {venv_python}")
    print(f"PYTHONPATH: {env['PYTHONPATH']}")
    print("=" * 70)
    print("Running full test suite...")
    print("=" * 70)

    result = subprocess.run(
        [venv_python, "-m", "pytest", "tests/", "-v", "--tb=short", "--color=yes"],
        env=env,
    )

    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
