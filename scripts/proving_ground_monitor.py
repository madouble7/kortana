#!/usr/bin/env python3
"""
PROVING GROUND REAL-TIME MONITOR
===============================
Track Kor'tana's autonomous engineering activity
"""

import os
import time
from datetime import datetime

print("🔬 PROVING GROUND - REAL-TIME AUTONOMOUS MONITOR")
print("=" * 60)
print("Tracking Kor'tana's first software engineering task...")
print()

# Target files to monitor
TARGET_FILES = {
    "goal_router.py": "src/kortana/api/routers/goal_router.py",
    "goal_service.py": "src/kortana/api/services/goal_service.py",
    "services/__init__.py": "src/kortana/api/services/__init__.py",
}

# Baseline measurements
BASELINE_ROUTER_SIZE = 1508  # Known size from previous checks


def get_file_info(filepath):
    """Get file information or return None if file doesn't exist."""
    if os.path.exists(filepath):
        stat = os.path.getsize(filepath)
        mtime = os.path.getmtime(filepath)
        return {
            "exists": True,
            "size": stat,
            "modified": datetime.fromtimestamp(mtime).strftime("%H:%M:%S"),
            "status": "MODIFIED"
            if stat != BASELINE_ROUTER_SIZE and "goal_router" in filepath
            else "BASELINE",
        }
    else:
        return {
            "exists": False,
            "size": 0,
            "modified": "N/A",
            "status": "AWAITING CREATION",
        }


def monitor_files():
    """Monitor target files for changes."""

    print(f"📊 FILE STATUS - {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 60)

    changes_detected = False

    for name, filepath in TARGET_FILES.items():
        info = get_file_info(filepath)

        status_icon = "✅" if info["exists"] else "⏳"

        print(
            f"{status_icon} {name:<20} | Size: {info['size']:<6} | Modified: {info['modified']:<8} | {info['status']}"
        )

        # Detect changes
        if (
            name == "goal_router.py"
            and info["exists"]
            and info["size"] != BASELINE_ROUTER_SIZE
        ):
            changes_detected = True
            print(
                f"   🚨 CHANGE DETECTED: Size changed from {BASELINE_ROUTER_SIZE} to {info['size']}"
            )

        if name == "goal_service.py" and info["exists"]:
            changes_detected = True
            print(f"   🎉 NEW FILE CREATED: {name} ({info['size']} bytes)")

    if changes_detected:
        print("\n🔥 AUTONOMOUS ENGINEERING ACTIVITY DETECTED!")
        print("   Kor'tana is actively refactoring the codebase!")
    else:
        print("\n⏳ Monitoring... (No changes detected yet)")

    print("=" * 60)
    return changes_detected


if __name__ == "__main__":
    print("Starting real-time monitoring...")
    print("Press Ctrl+C to stop")
    print()

    activity_detected = False

    try:
        while True:
            changes = monitor_files()

            if changes and not activity_detected:
                activity_detected = True
                print("\n🎯 FIRST AUTONOMOUS CHANGES DETECTED!")
                print("   Continuing to monitor progress...")

            time.sleep(5)  # Check every 5 seconds
            print()

    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")
        print("Final status check...")
        monitor_files()

        if activity_detected:
            print("\n🎉 AUTONOMOUS ENGINEERING ACTIVITY WAS OBSERVED!")
            print("   Check the modified files to see Kor'tana's work!")
        else:
            print("\n📋 No autonomous activity detected during monitoring")
            print("   Verify the server is running and goal was submitted")
