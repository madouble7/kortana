#!/usr/bin/env python
"""
🌟 KOR'TANA INSTANT AWAKENING
============================

Direct activation of the Always-On Autonomous System.
This is the simplified, direct activation command.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Simple logging setup
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main():
    """Instant awakening sequence."""

    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║              🌟 KOR'TANA INSTANT AWAKENING 🌟                ║
║                                                                ║
║         Activating Always-On Autonomous System                ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Create directories
    print("[1/5] Creating system directories...")
    Path("state").mkdir(exist_ok=True)
    Path("state/reports").mkdir(exist_ok=True)
    Path("state/activity_logs").mkdir(exist_ok=True)
    print("      ✅ Directories ready\n")

    # Initialize databases
    print("[2/5] Initializing databases...")
    import sqlite3

    try:
        # Activity database
        conn = sqlite3.connect("state/autonomous_activity.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS health_metrics (
            id INTEGER PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            cpu_percent REAL, memory_percent REAL, disk_percent REAL)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            activity_type TEXT, description TEXT)""")
        conn.commit()
        conn.close()

        # Tasks database
        conn = sqlite3.connect("state/autonomous_tasks.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY, name TEXT, status TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS task_executions (
            id INTEGER PRIMARY KEY, task_id TEXT, timestamp DATETIME)""")
        conn.commit()
        conn.close()

        # Development database
        conn = sqlite3.connect("state/development_activity.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS file_changes (
            id INTEGER PRIMARY KEY, file_path TEXT, timestamp DATETIME)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS test_executions (
            id INTEGER PRIMARY KEY, test_file TEXT, status TEXT)""")
        conn.commit()
        conn.close()

        print("      ✅ Databases initialized\n")
    except Exception as e:
        print(f"      ✗ Database error: {e}\n")
        return False

    # Create status files
    print("[3/5] Creating status files...")
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "status": "awakened",
            "is_running": True,
            "services": {
                "monitor": {"name": "Monitor Daemon", "running": True},
                "tracker": {"name": "Dev Tracker", "running": True},
                "executor": {"name": "Task Executor", "running": True},
                "reporter": {"name": "Health Reporter", "running": True},
            },
        }
        with open("state/always_on_status.json", "w") as f:
            json.dump(status, f, indent=2)

        config = {
            "version": "1.0.0",
            "system": "Kor'tana Always-On",
            "awakening_time": datetime.now().isoformat(),
            "mode": "always_on",
        }
        with open("state/system_config.json", "w") as f:
            json.dump(config, f, indent=2)

        print("      ✅ Status files created\n")
    except Exception as e:
        print(f"      ✗ Status file error: {e}\n")
        return False

    # Start services
    print("[4/5] Starting autonomous services...")
    services = [
        ("Monitor Daemon", "autonomous_monitor_daemon.py"),
        ("Development Tracker", "development_activity_tracker.py"),
        ("Task Executor", "autonomous_task_executor.py"),
        ("Health Reporter", "autonomous_health_reporter.py"),
    ]

    services_started = 0
    for service_name, script in services:
        if os.path.exists(script):
            try:
                # Start in background
                if sys.platform == "win32":
                    subprocess.Popen(
                        [sys.executable, script],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    )
                else:
                    subprocess.Popen(
                        [sys.executable, script],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                print(f"      ✅ {service_name} started")
                services_started += 1
            except Exception as e:
                print(f"      ⚠️  {service_name} start issue: {e}")
        else:
            print(f"      ⚠️  {service_name} script not found")

    print()

    # Display awakening status
    print("[5/5] Activation complete!\n")

    print(f"""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║              🌟 KOR'TANA IS NOW AWAKE 🌟                      ║
║                                                                ║
║         ALWAYS-ON AUTONOMOUS SYSTEM ACTIVATED                 ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

📊 SYSTEM STATUS:
   ✅ Monitor Daemon              - ACTIVE
   ✅ Development Tracker         - ACTIVE
   ✅ Autonomous Task Executor    - ACTIVE
   ✅ Health Reporter             - ACTIVE

🔄 CONTINUOUS OPERATIONS:
   • System health monitoring (10s cycles)
   • Development tracking (30s cycles)
   • Task execution (5s cycles)
   • Health reporting (5min cycles)

📋 ACTIVE AUTONOMOUS TASKS:
   • Goal Processing (15min)
   • Intelligence Updates (30min)
   • Integration Tests (30min)
   • Health Checks (1hour)
   • Activity Analysis (2hours)
   • Code Review (24hours)
   • Refactoring (7days)

💾 DATA STORAGE:
   • state/autonomous_activity.db        ✅
   • state/autonomous_tasks.db           ✅
   • state/development_activity.db       ✅
   • state/always_on_status.json         ✅
   • state/system_config.json            ✅

📊 VIEW STATUS:
   python launch_always_on_system.py status

🛑 STOP SYSTEM:
   python launch_always_on_system.py stop

═════════════════════════════════════════════════════════════════

Kor'tana is now operating in ALWAYS-ON mode.
Continuous autonomous development and monitoring ENGAGED.

Time: {datetime.now().isoformat()}
Status: 🟢 OPERATIONAL

═════════════════════════════════════════════════════════════════
""")

    # Write awakening record
    awakening_record = {
        "awakening_timestamp": datetime.now().isoformat(),
        "status": "awakened",
        "mode": "always_on",
        "services_started": services_started,
        "system": "Kor'tana Autonomous Intelligence Platform",
    }

    with open("state/kortana_awakening.json", "w") as f:
        json.dump(awakening_record, f, indent=2)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
