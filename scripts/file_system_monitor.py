#!/usr/bin/env python3
"""
File System Monitor for Autonomous Activity
Tracks file changes made by Kor'tana's autonomous operations
"""

import hashlib
import os
import time
from datetime import datetime


class FileSystemMonitor:
    def __init__(self, watch_dirs: list[str] = None):
        if watch_dirs is None:
            self.watch_dirs = [
                "src/kortana",
                "tests/",
                "docs/",
                "requirements.txt",
                "pyproject.toml",
                "*.py",
            ]
        else:
            self.watch_dirs = watch_dirs

        self.baseline: dict[str, str] = {}
        self.start_time = datetime.now()
        self.change_count = 0

    def get_file_hash(self, file_path: str) -> str:
        """Get MD5 hash of file content"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def scan_files(self) -> set[str]:
        """Scan all files in watch directories"""
        current_files = set()

        for dir_path in self.watch_dirs:
            if dir_path.endswith(".txt") or dir_path.endswith(".toml"):
                # Single file
                if os.path.exists(dir_path):
                    current_files.add(dir_path)
            elif os.path.exists(dir_path):
                # Directory
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        if file.endswith(
                            (".py", ".txt", ".md", ".yaml", ".yml", ".json", ".toml")
                        ):
                            file_path = os.path.join(root, file)
                            current_files.add(file_path)

        return current_files

    def create_baseline(self):
        """Create initial baseline of file states"""
        current_files = self.scan_files()

        for file_path in current_files:
            self.baseline[file_path] = self.get_file_hash(file_path)

        print("📁 File System Monitor Initialized")
        print(f"🔍 Watching {len(self.baseline)} files for autonomous changes")
        print(f"📂 Monitoring directories: {', '.join(self.watch_dirs)}")
        print("-" * 60)

    def check_for_changes(self) -> list[str]:
        """Check for file system changes"""
        changes = []
        current_files = self.scan_files()

        # Check for new files
        for file_path in current_files:
            if file_path not in self.baseline:
                changes.append(f"🆕 NEW FILE: {file_path}")
                self.baseline[file_path] = self.get_file_hash(file_path)
                self.change_count += 1

        # Check for modified files
        for file_path in list(self.baseline.keys()):
            if file_path in current_files:
                current_hash = self.get_file_hash(file_path)
                if current_hash != self.baseline[file_path]:
                    changes.append(f"✏️  MODIFIED: {file_path}")
                    self.baseline[file_path] = current_hash
                    self.change_count += 1
            else:
                # File was deleted
                changes.append(f"🗑️  DELETED: {file_path}")
                del self.baseline[file_path]
                self.change_count += 1

        return changes

    def print_status(self):
        """Print current monitoring status"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        runtime = datetime.now() - self.start_time

        print(f"\n{'=' * 60}")
        print(f"📁 FILE SYSTEM MONITOR - {timestamp}")
        print(f"⏱️  Runtime: {runtime}")
        print(f"📊 Total Changes Detected: {self.change_count}")
        print(f"📂 Files Monitored: {len(self.baseline)}")
        print(f"{'=' * 60}")

    def analyze_changes(self, changes: list[str]):
        """Analyze the nature of changes for autonomous activity patterns"""
        if not changes:
            return

        print(f"\n🚨 AUTONOMOUS ACTIVITY DETECTED ({len(changes)} changes):")

        # Categorize changes
        new_files = [c for c in changes if "NEW FILE" in c]
        modified_files = [c for c in changes if "MODIFIED" in c]
        deleted_files = [c for c in changes if "DELETED" in c]

        if new_files:
            print(f"\n🆕 New Files Created ({len(new_files)}):")
            for change in new_files:
                file_path = change.split(": ", 1)[1]
                print(f"   📄 {file_path}")

                # Check if it looks like code generation
                if file_path.endswith(".py"):
                    print("      🤖 Python code generation detected")
                elif file_path.endswith((".md", ".txt")):
                    print("      📝 Documentation generation detected")
                elif file_path.endswith((".yaml", ".yml", ".json")):
                    print("      ⚙️  Configuration file generation detected")

        if modified_files:
            print(f"\n✏️  Modified Files ({len(modified_files)}):")
            for change in modified_files:
                file_path = change.split(": ", 1)[1]
                print(f"   📄 {file_path}")

                # Detect autonomous patterns
                if "planning_engine" in file_path:
                    print("      🧠 Planning engine modification - strategic thinking")
                elif "execution_engine" in file_path:
                    print(
                        "      ⚡ Execution engine modification - capability expansion"
                    )
                elif "memory" in file_path or "learning" in file_path:
                    print(
                        "      🧠 Memory/Learning system modification - knowledge formation"
                    )
                elif "test" in file_path:
                    print("      🧪 Test modification - validation improvement")

        if deleted_files:
            print(f"\n🗑️  Deleted Files ({len(deleted_files)}):")
            for change in deleted_files:
                file_path = change.split(": ", 1)[1]
                print(f"   📄 {file_path}")
                print("      🧹 Code cleanup or refactoring detected")

    def run_continuous_monitoring(self, interval: int = 5):
        """Run continuous file system monitoring"""
        self.create_baseline()

        print(f"🚀 Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                changes = self.check_for_changes()

                if changes:
                    self.analyze_changes(changes)
                    self.print_status()
                else:
                    # Just show a brief status every 30 seconds
                    if int(time.time()) % 30 == 0:
                        print(
                            f"📁 Monitoring... ({len(self.baseline)} files, {self.change_count} total changes)"
                        )

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n🛑 File monitoring stopped by user")
            runtime = datetime.now() - self.start_time
            print(f"📊 Total monitoring time: {runtime}")
            print(f"📈 Total changes detected: {self.change_count}")


if __name__ == "__main__":
    monitor = FileSystemMonitor()
    monitor.run_continuous_monitoring()
