"""
Run Tests

This script runs the test suite for the Kor'tana project.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Run the test suite."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"Working in directory: {os.getcwd()}")

    # Set PYTHONPATH to include the project root
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    # Check if pytest is installed
    try:
        subprocess.run(
            [sys.executable, "-c", "import pytest"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        print("pytest not found. Installing...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"],
            check=True,
        )

    # Run the tests
    print("\nRunning tests...\n")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", "tests"], env=env
        )

        if result.returncode == 0:
            print("\nAll tests passed!")
        else:
            print(f"\nSome tests failed with return code {result.returncode}")

        return result.returncode
    except Exception as e:
        print(f"\nError running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
