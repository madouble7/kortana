"""
Run Fixed Kor'tana

This script runs the fixed version of Kor'tana:
1. Fixes the indentation issues in brain.py
2. Runs the brain module
"""

import os
import subprocess
import sys


def main():
    """Fix and run Kor'tana."""
    print("Fixing indentation in brain.py...")
    subprocess.run([sys.executable, "fix_indentation.py"])

    print("\nRunning Kor'tana...")
    os.environ["PYTHONPATH"] = os.getcwd()
    subprocess.run([sys.executable, "-m", "src.kortana.core.brain"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
