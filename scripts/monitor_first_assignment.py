#!/usr/bin/env python3
"""
🔍 THE PROVING GROUND MONITOR
Monitor Kor'tana's first autonomous engineering assignment in real-time
"""

import sqlite3
import time
from datetime import datetime
from pathlib import Path


def check_autonomous_progress():
    """Monitor Kor'tana's autonomous development progress."""

    print("🔍 THE PROVING GROUND - AUTONOMOUS DEVELOPMENT MONITOR")
    print("=" * 60)
    print("Watching Kor'tana's first autonomous engineering assignment...")
    print("")

    # Files to monitor
    service_file = Path("src/kortana/api/services/goal_service.py")
    router_file = Path("src/kortana/api/routers/goal_router.py")
    services_dir = Path("src/kortana/api/services")

    # Get original router file timestamp
    router_original_time = router_file.stat().st_mtime if router_file.exists() else None

    print("📋 ASSIGNMENT STATUS:")
    print("   Task: Refactor list_all_goals function and create service layer")
    print("   Expected outputs:")
    print("   - Create: src/kortana/api/services/goal_service.py")
    print("   - Modify: src/kortana/api/routers/goal_router.py")
    print("   - Execute: Test suite validation")
    print("")

    cycle = 1
    while cycle <= 20:  # Monitor for 20 cycles
        print(f"🔄 Monitoring Cycle {cycle} - {datetime.now().strftime('%H:%M:%S')}")

        # Check goal status in database
        try:
            conn = sqlite3.connect("kortana.db")
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM goals WHERE id = 2")
            result = cursor.fetchone()
            goal_status = result[0] if result else "unknown"
            conn.close()
            print(f"   📊 Goal Status: {goal_status}")
        except Exception as e:
            print(f"   📊 Goal Status: Error checking - {e}")

        # Check services directory
        services_exists = services_dir.exists()
        print(
            f"   📁 Services Directory: {'✅ EXISTS' if services_exists else '❌ NOT CREATED'}"
        )

        # Check service file
        service_exists = service_file.exists()
        print(
            f"   📄 goal_service.py: {'✅ CREATED' if service_exists else '❌ NOT CREATED'}"
        )

        # Check router modifications
        if router_file.exists():
            current_time = router_file.stat().st_mtime
            if router_original_time and current_time > router_original_time:
                print("   📝 goal_router.py: ✅ MODIFIED")
            else:
                print("   📝 goal_router.py: ⏳ NOT MODIFIED")
        else:
            print("   📝 goal_router.py: ❌ NOT FOUND")

        # Check for autonomous activity signs
        if service_exists and services_exists:
            print("   🎉 AUTONOMOUS FILE CREATION DETECTED!")

            # Try to read the service file content
            try:
                with open(service_file) as f:
                    content = f.read()
                print(f"   📖 Service file size: {len(content)} characters")
                if "list_all_goals" in content:
                    print("   ✅ Service contains list_all_goals function!")
            except Exception as e:
                print(f"   ❌ Error reading service file: {e}")

        print("")
        time.sleep(3)  # Check every 3 seconds
        cycle += 1

    print("🏁 Monitoring session complete.")
    print("If no autonomous activity was detected, Kor'tana may need:")
    print("- Her autonomous learning loop to be active")
    print("- Goal processing engine to be running")
    print("- Planning engine to be operational")


if __name__ == "__main__":
    check_autonomous_progress()
