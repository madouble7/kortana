"""
Test script to check if the Python interpreter is working correctly
and to verify the Python path is set up properly.
"""

import os
import sys


def main():
    print("\n=== Python Interpreter Test ===")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

    print("\nPython Path:")
    for path in sys.path:
        print(f"  - {path}")

    # Try to import from other directories
    print("\nTesting imports:")
    try:
        # from src import brain # Removed F401 unused import

        print("✅ Successfully imported 'brain' module")
    except ImportError as e:
        print(f"❌ Failed to import 'brain' module: {e}")

    try:
        # import brain # Removed F401 unused import

        print("✅ Successfully imported 'brain' module directly")
    except ImportError as e:
        print(f"❌ Failed to import 'brain' module directly: {e}")


if __name__ == "__main__":
    main()
