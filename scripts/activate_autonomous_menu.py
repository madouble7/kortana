#!/usr/bin/env python3
"""
Kor'tana Autonomous Activation Menu
==================================

Choose how to activate Kor'tana's autonomous capabilities.
"""

import os
import subprocess
import sys


def show_menu():
    """Display the autonomous activation menu."""
    print("🤖 KOR'TANA AUTONOMOUS ACTIVATION")
    print("=" * 40)
    print()
    print("Choose activation method:")
    print()
    print("1. 🔥 CONTINUOUS AUTONOMOUS MODE")
    print("   - Runs until you stop her")
    print("   - Full autonomous operation")
    print("   - Auto-restart on errors")
    print()
    print("2. 🚀 STANDARD AUTONOMOUS MODE")
    print("   - Enhanced brain.py autonomous mode")
    print("   - 15-min planning, 5-min tasks, 1-hour learning")
    print("   - Interactive with autonomous background")
    print()
    print("3. 📊 CHECK AUTONOMOUS STATUS")
    print("   - See if Kor'tana is currently running")
    print("   - Check system readiness")
    print()
    print("4. 🛑 STOP AUTONOMOUS OPERATION")
    print("   - Stop any running autonomous processes")
    print()
    print("5. ❌ EXIT")
    print()


def check_autonomous_status():
    """Check if autonomous Kor'tana is running."""
    print("🔍 CHECKING AUTONOMOUS STATUS")
    print("-" * 30)

    # Check for running Python processes
    try:
        import psutil

        autonomous_processes = []

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if proc.info["name"] == "python.exe" and proc.info["cmdline"]:
                    cmdline = " ".join(proc.info["cmdline"])
                    if "autonomous" in cmdline.lower() or "brain.py" in cmdline:
                        autonomous_processes.append(
                            {"pid": proc.info["pid"], "cmdline": cmdline}
                        )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if autonomous_processes:
            print(f"✅ Found {len(autonomous_processes)} autonomous process(es):")
            for proc in autonomous_processes:
                print(f"   PID {proc['pid']}: {proc['cmdline']}")
        else:
            print("❌ No autonomous Kor'tana processes found")

    except ImportError:
        print("⚠️  psutil not available - cannot check running processes")

    print()


def stop_autonomous():
    """Stop autonomous processes."""
    print("🛑 STOPPING AUTONOMOUS OPERATION")
    print("-" * 30)

    try:
        import psutil

        stopped = 0

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if proc.info["name"] == "python.exe" and proc.info["cmdline"]:
                    cmdline = " ".join(proc.info["cmdline"])
                    if "autonomous" in cmdline.lower() or "brain.py" in cmdline:
                        print(f"Stopping PID {proc.info['pid']}: {cmdline}")
                        proc.terminate()
                        stopped += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if stopped > 0:
            print(f"✅ Stopped {stopped} autonomous process(es)")
        else:
            print("❌ No autonomous processes found to stop")

    except ImportError:
        print("⚠️  psutil not available - cannot stop processes automatically")
        print("Please manually stop any running Python processes")

    print()


def main():
    """Main menu loop."""
    # Change to project directory
    project_root = r"C:\project-kortana"
    os.chdir(project_root)

    while True:
        show_menu()

        try:
            choice = input("Enter choice (1-5): ").strip()
            print()

            if choice == "1":
                print("🔥 Launching CONTINUOUS AUTONOMOUS MODE...")
                print("This will run Kor'tana continuously until stopped.")
                print("Use Ctrl+C to stop or option 4 from another terminal.")
                print()

                try:
                    subprocess.run([sys.executable, "run_autonomous_continuous.py"])
                except KeyboardInterrupt:
                    print("\n🛑 Stopped by user")

            elif choice == "2":
                print("🚀 Launching STANDARD AUTONOMOUS MODE...")
                print("Use Ctrl+C to return to interactive mode.")
                print()

                try:
                    subprocess.run(
                        [sys.executable, "src/kortana/core/brain.py", "--autonomous"]
                    )
                except KeyboardInterrupt:
                    print("\n🛑 Stopped by user")

            elif choice == "3":
                check_autonomous_status()

            elif choice == "4":
                stop_autonomous()

            elif choice == "5":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please enter 1-5.")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
