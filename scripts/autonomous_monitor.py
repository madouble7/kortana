#!/usr/bin/env python3
"""
GENESIS PROTOCOL PHASE 3: CONTINUOUS MONITORING SYSTEM
Real-time observation of Kor'tana's autonomous software engineering performance
"""

import hashlib
import os
from datetime import datetime


class ProvingGroundMonitor:
    def __init__(self):
        self.baseline = {}
        self.target_files = [
            "src/kortana/api/routers/goal_router.py",
            "src/kortana/api/services/goal_service.py",  # Expected new file
        ]
        self.target_dirs = [
            "src/kortana/api/services/",  # Expected new directory
        ]
        self.log_files = [
            "genesis_run.log",
            "genesis_run_shell.log",
            "logs/kortana.log",
            "kortana.log",
        ]

    def get_file_info(self, filepath):
        """Get comprehensive file information"""
        try:
            if os.path.exists(filepath):
                stat = os.stat(filepath)
                with open(filepath, "rb") as f:
                    content_hash = hashlib.md5(f.read()).hexdigest()

                with open(filepath, encoding="utf-8") as f:
                    content = f.read()
                    line_count = len(content.split("\n"))

                return {
                    "exists": True,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "hash": content_hash,
                    "lines": line_count,
                    "content_preview": content[:200] + "..."
                    if len(content) > 200
                    else content,
                }
            else:
                return {"exists": False}
        except Exception as e:
            return {"exists": False, "error": str(e)}

    def establish_baseline(self):
        """Establish baseline state before monitoring"""
        print("🔬 ESTABLISHING PROVING GROUND BASELINE")
        print("=" * 60)

        for filepath in self.target_files:
            info = self.get_file_info(filepath)
            self.baseline[filepath] = info

            if info["exists"]:
                print(f"📄 {filepath}: {info['size']} bytes, {info['lines']} lines")
                print(f"   🕒 Modified: {info['modified']}")
                print(f"   🔍 Hash: {info['hash'][:8]}...")
            else:
                print(f"❌ {filepath}: NOT EXISTS (expected for new files)")

        # Check directories
        for dirpath in self.target_dirs:
            exists = os.path.exists(dirpath)
            self.baseline[dirpath] = {"exists": exists, "type": "directory"}
            print(f"📁 {dirpath}: {'EXISTS' if exists else 'NOT EXISTS'}")

        print(f"\n✅ Baseline established at {datetime.now().strftime('%H:%M:%S')}")
        return self.baseline

    def detect_changes(self):
        """Detect any changes from baseline"""
        changes = {}

        for filepath in self.target_files:
            current = self.get_file_info(filepath)
            baseline = self.baseline.get(filepath, {"exists": False})

            if current["exists"] != baseline["exists"]:
                if current["exists"]:
                    changes[filepath] = {"type": "CREATED", "info": current}
                else:
                    changes[filepath] = {"type": "DELETED", "info": baseline}
            elif current["exists"] and baseline["exists"]:
                if current["hash"] != baseline["hash"]:
                    changes[filepath] = {
                        "type": "MODIFIED",
                        "info": current,
                        "baseline": baseline,
                    }

        # Check directories
        for dirpath in self.target_dirs:
            current_exists = os.path.exists(dirpath)
            baseline_exists = self.baseline.get(dirpath, {}).get("exists", False)

            if current_exists != baseline_exists:
                changes[dirpath] = {
                    "type": "DIR_CREATED" if current_exists else "DIR_DELETED",
                    "exists": current_exists,
                }

        return changes

    def check_logs(self):
        """Check for autonomous activity in logs"""
        log_activity = {}

        for log_file in self.log_files:
            if os.path.exists(log_file):
                try:
                    stat = os.stat(log_file)
                    with open(log_file, encoding="utf-8") as f:
                        lines = f.readlines()

                    log_activity[log_file] = {
                        "exists": True,
                        "size": stat.st_size,
                        "lines": len(lines),
                        "last_modified": datetime.fromtimestamp(stat.st_mtime),
                        "recent_entries": lines[-3:] if lines else [],
                    }
                except Exception as e:
                    log_activity[log_file] = {"exists": True, "error": str(e)}
            else:
                log_activity[log_file] = {"exists": False}

        return log_activity

    def generate_report(self, changes, logs):
        """Generate monitoring report"""
        print(
            f"\n🔍 PROVING GROUND MONITORING REPORT - {datetime.now().strftime('%H:%M:%S')}"
        )
        print("=" * 60)

        if changes:
            print("🚨 CHANGES DETECTED:")
            for filepath, change in changes.items():
                if change["type"] == "CREATED":
                    print(f"   ✨ NEW FILE: {filepath}")
                    print(f"      📏 Size: {change['info']['size']} bytes")
                    print(f"      📄 Lines: {change['info']['lines']}")
                    print("      🎯 GENESIS PROTOCOL SUCCESS INDICATOR!")

                elif change["type"] == "MODIFIED":
                    print(f"   🔄 MODIFIED: {filepath}")
                    old_size = change["baseline"]["size"]
                    new_size = change["info"]["size"]
                    print(
                        f"      📏 Size: {old_size} → {new_size} bytes ({new_size - old_size:+d})"
                    )

                    old_lines = change["baseline"]["lines"]
                    new_lines = change["info"]["lines"]
                    print(
                        f"      📄 Lines: {old_lines} → {new_lines} ({new_lines - old_lines:+d})"
                    )
                    print("      🎯 REFACTORING SUCCESS INDICATOR!")

                elif change["type"] == "DIR_CREATED":
                    print(f"   📁 NEW DIRECTORY: {filepath}")
                    print("      🎯 SERVICE LAYER CREATION DETECTED!")
        else:
            print(
                "⏳ No changes detected yet - autonomous processing may be in progress..."
            )

        # Log activity summary
        active_logs = [log for log, info in logs.items() if info["exists"]]
        if active_logs:
            print(f"\n📊 LOG ACTIVITY: {len(active_logs)} active log files")
            for log_file in active_logs[:2]:  # Show top 2
                info = logs[log_file]
                if "recent_entries" in info and info["recent_entries"]:
                    print(f"   📄 {log_file}: {info['lines']} lines")
                    for entry in info["recent_entries"]:
                        print(f"      {entry.strip()}")

        return len(changes) > 0


def main():
    monitor = ProvingGroundMonitor()

    print("🚀 GENESIS PROTOCOL PHASE 3: THE PROVING GROUND")
    print("🔬 AUTONOMOUS SOFTWARE ENGINEERING MONITORING ACTIVE")
    print("=" * 70)

    # Establish baseline
    monitor.establish_baseline()

    # Single monitoring check
    print("\n🔍 SCANNING FOR AUTONOMOUS ACTIVITY...")
    changes = monitor.detect_changes()
    logs = monitor.check_logs()

    # Generate report
    activity_detected = monitor.generate_report(changes, logs)

    if activity_detected:
        print("\n🔥 GENESIS PROTOCOL ACTIVITY DETECTED!")
        print("🎯 Kor'tana is making progress on her autonomous engineering task!")
    else:
        print("\n⏳ Monitoring complete - continue observing for autonomous progress")

    print("\n" + "=" * 70)
    print("🔬 Observer standing by for further developments...")


if __name__ == "__main__":
    main()
