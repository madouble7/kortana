#!/usr/bin/env python3
"""
Kor'tana System Demo
===================
Demonstrates all three automation levels
"""

import os
import subprocess
import sys
import time
from pathlib import Path


def demo_manual_mode():
    """Demonstrate manual mode operation"""
    print("\n" + "=" * 50)
    print(" DEMO: MANUAL MODE")
    print("=" * 50)
    print("\nManual mode allows you to run individual cycles and commands.")
    print("Perfect for testing, debugging, or when you want full control.")

    input("\nPress Enter to run a single relay cycle...")

    result = subprocess.run(
        [sys.executable, "relays/relay.py"], capture_output=True, text=True
    )

    print("\nRelay cycle output:")
    print("-" * 20)
    print(result.stdout if result.stdout else "No output")

    input("\nPress Enter to check system status...")

    result = subprocess.run(
        [sys.executable, "relays/relay.py", "--status"], capture_output=True, text=True
    )

    print("\nSystem status:")
    print("-" * 15)
    print(result.stdout if result.stdout else "No output")


def demo_semi_auto_mode():
    """Demonstrate semi-auto mode operation"""
    print("\n" + "=" * 50)
    print(" DEMO: SEMI-AUTO MODE")
    print("=" * 50)
    print("\nSemi-auto mode runs background processes that you can monitor.")
    print("Great for development and when you want to see what's happening.")

    print("\nStarting background relay process...")

    # Start a background process for demo
    proc = subprocess.Popen(
        ["cmd", "/c", "relays\\run_relay.bat"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    print(f"Background process started (PID: {proc.pid})")
    print("In real mode, this would run continuously every 5 minutes.")

    # Let it run for a few seconds
    print("\nLetting it run for 10 seconds...")
    time.sleep(10)

    # Terminate for demo
    proc.terminate()
    print("Demo process terminated.")
    print("\nIn real semi-auto mode:")
    print("- Relay runs every 5 minutes")
    print("- Handoff monitoring every 10 minutes")
    print("- You can close windows to stop")


def demo_hands_off_mode():
    """Demonstrate hands-off mode setup"""
    print("\n" + "=" * 50)
    print(" DEMO: HANDS-OFF MODE")
    print("=" * 50)
    print("\nHands-off mode uses Windows Task Scheduler for full automation.")
    print("Perfect for production - runs even when you're not logged in.")

    print("\nChecking if scheduled tasks exist...")

    # Check for existing tasks
    result = subprocess.run(
        ["schtasks", "/query", "/fo", "csv"], capture_output=True, text=True
    )

    if "KorTana" in result.stdout:
        print("[OK] Kor'tana scheduled tasks found")
        lines = result.stdout.split("\n")
        for line in lines:
            if "KorTana" in line:
                parts = line.split(",")
                if len(parts) > 0:
                    task_name = parts[0].strip('"')
                    print(f"  - {task_name}")
    else:
        print("[INFO] No scheduled tasks found")
        print("To set up hands-off mode:")
        print("1. Run: python setup_task_scheduler.py")
        print("2. Tasks will run automatically every 5-10 minutes")
        print("3. View logs to monitor activity")


def main():
    """Main demo function"""
    print("=" * 60)
    print(" KOR'TANA AUTONOMOUS SYSTEM DEMONSTRATION")
    print("=" * 60)
    print("\nThis demo shows all three automation levels:")
    print("1. Manual Mode - Run commands when needed")
    print("2. Semi-Auto Mode - Background monitoring")
    print("3. Hands-Off Mode - Full automation")

    while True:
        print("\n" + "-" * 40)
        print("Choose demo mode:")
        print("1. Manual Mode Demo")
        print("2. Semi-Auto Mode Demo")
        print("3. Hands-Off Mode Demo")
        print("4. Run System Verification")
        print("5. Launch Automation Control")
        print("0. Exit")

        choice = input("\nEnter choice (0-5): ").strip()

        try:
            if choice == "1":
                demo_manual_mode()
            elif choice == "2":
                demo_semi_auto_mode()
            elif choice == "3":
                demo_hands_off_mode()
            elif choice == "4":
                print("\nRunning system verification...")
                subprocess.run([sys.executable, "verify_system.py"])
            elif choice == "5":
                print("\nLaunching automation control...")
                subprocess.run(["automation_control.bat"], shell=True)
            elif choice == "0":
                break
            else:
                print("Invalid choice. Please try again.")

        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user.")
            break
        except Exception as e:
            print(f"\nError during demo: {e}")

    print("\nDemo complete. System is ready for autonomous operation!")
    print("\nTo start production use:")
    print("  automation_control.bat")


if __name__ == "__main__":
    # Change to the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    main()
