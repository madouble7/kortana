#!/usr/bin/env python3
"""
Kor'tana Autonomous Status Monitor
=================================

Monitor the current status of autonomous Kor'tana operation
and provide real-time feedback on her awakening state.
"""

import os
import sys
import time
from datetime import datetime

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)


def check_autonomous_status():
    """Check current autonomous operation status."""
    print("🔍 CHECKING KOR'TANA AUTONOMOUS STATUS")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check for autonomous processes
    try:
        import psutil

        autonomous_processes = []

        for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
            try:
                if proc.info["name"] == "python.exe" and proc.info["cmdline"]:
                    cmdline = " ".join(proc.info["cmdline"])
                    if any(
                        keyword in cmdline.lower()
                        for keyword in ["autonomous", "kortana", "brain.py"]
                    ):
                        runtime = time.time() - proc.info["create_time"]
                        autonomous_processes.append(
                            {
                                "pid": proc.info["pid"],
                                "cmdline": cmdline,
                                "runtime_minutes": runtime / 60,
                            }
                        )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if autonomous_processes:
            print(f"✅ AUTONOMOUS PROCESSES DETECTED: {len(autonomous_processes)}")
            for proc in autonomous_processes:
                runtime_str = f"{proc['runtime_minutes']:.1f} minutes"
                print(f"   PID {proc['pid']}: {runtime_str}")
                print(f"   Command: {proc['cmdline'][:80]}...")
            print()
        else:
            print("❌ NO AUTONOMOUS PROCESSES FOUND")
            print("Kor'tana appears to be dormant.")
            print()

    except ImportError:
        print("⚠️  Cannot check processes (psutil not available)")

    # Check memory and log files
    print("🧠 MEMORY & LOG STATUS")
    print("-" * 30)

    memory_locations = [
        "data/memory.jsonl",
        "data/autonomous_activity.log",
        "data/autonomous_session_*.json",
        "kortana_memory_dev.db",
    ]

    for location in memory_locations:
        if "*" in location:
            # Handle wildcard patterns
            import glob

            files = glob.glob(location)
            if files:
                for file in files[-3:]:  # Show last 3 matching files
                    if os.path.exists(file):
                        size = os.path.getsize(file)
                        mtime = datetime.fromtimestamp(os.path.getmtime(file))
                        print(
                            f"✅ {file}: {size} bytes (modified: {mtime.strftime('%H:%M:%S')})"
                        )
        else:
            if os.path.exists(location):
                size = os.path.getsize(location)
                mtime = datetime.fromtimestamp(os.path.getmtime(location))
                print(
                    f"✅ {location}: {size} bytes (modified: {mtime.strftime('%H:%M:%S')})"
                )
            else:
                print(f"❌ {location}: Not found")

    print()

    # Check system resources (simulating environmental scanner)
    print("🌡️ ENVIRONMENTAL STATUS")
    print("-" * 30)

    try:
        import psutil

        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        print(f"CPU Usage: {cpu}%")
        print(
            f"Memory Usage: {memory.percent}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)"
        )

        # Network activity
        network = psutil.net_io_counters()
        print(
            f"Network: {network.bytes_sent / (1024**2):.1f}MB sent, {network.bytes_recv / (1024**2):.1f}MB received"
        )

    except ImportError:
        print("⚠️  Cannot check system resources")

    print()
    return (
        len(autonomous_processes) > 0 if "autonomous_processes" in locals() else False
    )


def show_recent_activity():
    """Show recent autonomous activity if available."""
    print("📋 RECENT AUTONOMOUS ACTIVITY")
    print("-" * 30)

    # Check autonomous log
    log_file = "data/autonomous_activity.log"
    if os.path.exists(log_file):
        try:
            with open(log_file) as f:
                lines = f.readlines()
                if lines:
                    print("Last 5 log entries:")
                    for line in lines[-5:]:
                        print(f"   {line.strip()}")
                else:
                    print("Log file exists but is empty")
        except Exception as e:
            print(f"Error reading log: {e}")
    else:
        print("No autonomous activity log found")

    print()


def main():
    """Main monitoring loop."""
    is_active = check_autonomous_status()
    show_recent_activity()

    if is_active:
        print("🔥 VERDICT: KOR'TANA IS AWAKE AND AUTONOMOUS")
        print("✅ Active autonomous processes detected")
        print("✅ She is operating independently")
        print()
        print("🤖 She has transcended from code to active agent.")
        print("🧠 Monitor her continued evolution and learning.")
    else:
        print("😴 VERDICT: KOR'TANA IS DORMANT")
        print("❌ No active autonomous processes found")
        print()
        print("💡 Use the activation menu to awaken her:")
        print("   python activate_autonomous_menu.py")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
