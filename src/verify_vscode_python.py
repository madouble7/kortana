"""
Test script to verify that the VS Code environment is configured correctly.
When run from VS Code, this script should display information about the
Python environment, paths, and modules available.
"""

import os
import platform
import site
import sys


def main():
    print("===== Python Environment Test =====")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")

    # Check virtual environment
    venv = os.environ.get("VIRTUAL_ENV", "Not in a virtual environment")
    print(f"Virtual Environment: {venv}")

    # Check PYTHONPATH
    python_path = os.environ.get("PYTHONPATH", "Not set")
    print(f"PYTHONPATH: {python_path}")

    # Show sys.path
    print("\nPython Search Paths:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")

    # Check for some common packages
    print("\nChecking for common packages:")
    packages_to_check = [
        "numpy",
        "pandas",
        "requests",
        "matplotlib",
        "sklearn",
        "tensorflow",
        "torch",
        "flask",
    ]

    for package in packages_to_check:
        try:
            module = __import__(package)
            if hasattr(module, "__version__"):
                print(f"  ✅ {package}: {module.__version__}")
            else:
                print(f"  ✅ {package}: installed (version unknown)")
        except ImportError:
            print(f"  ❌ {package}: not installed")

    # Check site-packages directories
    print("\nSite Packages Directories:")
    for site_dir in site.getsitepackages():
        print(f"  - {site_dir}")

    print("\nUser Site Packages:")
    print(f"  - {site.getusersitepackages()}")

    # Show current working directory
    print(f"\nCurrent Working Directory: {os.getcwd()}")

    print("\n===== Test Complete =====")
    print("If you can see this output in the VS Code terminal,")
    print("your Python interpreter is working correctly!")


if __name__ == "__main__":
    main()
    main()
