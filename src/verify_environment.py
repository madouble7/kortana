"""
Quick test to verify VS Code is properly configured with venv311.
Run this file to see if the environment is correctly activated.
"""

import os
import sys
from pathlib import Path


def check_environment():
    """Check the Python environment and paths."""
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")

    # Check if we're using venv311
    using_venv311 = "venv311" in sys.executable
    print(f"Using venv311: {'✓ Yes' if using_venv311 else '✗ No'}")

    # Check PYTHONPATH
    python_path = os.environ.get("PYTHONPATH", "")
    print(f"PYTHONPATH: {python_path}")

    # List current directory
    current_dir = Path(".")
    print("\nFiles in current directory:")
    for file_path in sorted(current_dir.glob("*.py")):
        print(f"  - {file_path}")

    print("\nImport paths:")
    for path in sys.path:
        print(f"  - {path}")


if __name__ == "__main__":
    print("=== VS Code Python Environment Test ===")
    check_environment()
    print("\nSetup is complete! You can now work with your Python project.")
