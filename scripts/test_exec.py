#!/usr/bin/env python
"""
Simple Python Environment Diagnostic Script

This script prints basic information about the Python environment
it's being executed in, to help diagnose issues with execution
paths and environment variables.
"""

import os
import platform
import sys


def main():
    """Print basic environment information."""
    print("--- test_exec.py diagnostic script ---")
    print("Execution: SUCCESS")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Python Version: {platform.python_version()}")
    print(f"Python Executable: {os.path.basename(sys.executable)}")
    print()
    print("PYTHONPATH (sys.path):")
    for i, path in enumerate(sys.path):
        print(f"  [{i}] {path}")
    print("--- end of diagnostic ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
