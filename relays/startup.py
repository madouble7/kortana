#!/usr/bin/env python3
"""
Autonomous Kor'tana Startup
===========================

Quick startup script for the autonomous agent system.
Choose between test mode or full autonomous operation.

Usage:
    python relays/startup.py
"""

import os
import subprocess
import sys


def run_test():
    """Run autonomy test"""
    print("🧪 Running autonomy test...")
    subprocess.run([sys.executable, "test_autonomy.py"])


def run_full_system():
    """Run full autonomous system"""
    print("🚀 Starting full autonomous agent system...")
    print("Note: This will run continuously until Ctrl+C")
    input("Press Enter to continue or Ctrl+C to cancel...")
    subprocess.run([sys.executable, "master_orchestrator.py"])


def main():
    """Startup menu"""
    print("🤖 AUTONOMOUS KOR'TANA SYSTEM")
    print("=" * 40)
    print()
    print("Choose operation mode:")
    print("1. Test autonomy (quick verification)")
    print("2. Run full autonomous system")
    print("3. Exit")
    print()

    while True:
        choice = input("Enter choice (1-3): ").strip()

        if choice == "1":
            run_test()
            break
        elif choice == "2":
            run_full_system()
            break
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    # Change to relays directory if not already there
    if not os.path.basename(os.getcwd()) == "relays":
        if os.path.exists("relays"):
            os.chdir("relays")
        else:
            print("Error: Please run from the kortana directory or relays subdirectory")
            sys.exit(1)

    main()
