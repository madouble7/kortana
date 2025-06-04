"""
Script to verify Python interpreter is correctly configured and accessible to VS Code.
This script will output the Python version and interpreter path.
"""

import os
import sys


def main():
    print("Python version:", sys.version)
    print("Python interpreter path:", sys.executable)

    # Print environment variables
    print("\nPYTHONPATH:", os.environ.get("PYTHONPATH", "Not set"))

    # Check if the virtual environment is activated
    venv = os.environ.get("VIRTUAL_ENV", "Not activated")
    print("Virtual environment:", venv)

    # List available modules
    print("\nChecking for key modules:")
    try:
        import numpy

        print("numpy available:", numpy.__version__)
    except ImportError:
        print("numpy not found")

    try:
        import pandas

        print("pandas available:", pandas.__version__)
    except ImportError:
        print("pandas not found")

    # Print working directory
    print("\nCurrent working directory:", os.getcwd())

    # List base directories in project
    print("\nProject structure:")
    for item in os.listdir(".."):
        if os.path.isdir(os.path.join("..", item)):
            print(f"- {item}/")
        else:
            print(f"- {item}")


if __name__ == "__main__":
    main()
    main()
