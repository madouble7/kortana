#!/usr/bin/env python3
"""
🤖 KOR'TANA AUTONOMOUS ACTIVITY MONITOR
Real-time observation of autonomous software engineering

This script provides comprehensive monitoring of Kor'tana's autonomous
development across all channels: Live Feed, Mission Control, and Physical Evidence
"""

import json
import os
import time
from datetime import datetime

import requests


class AutonomousActivityMonitor:
    def __init__(self):
        self.api_base = "http://127.0.0.1:8001"
        self.start_time = datetime.now()
        self.observed_goals = set()
        self.observed_memories = set()
        self.file_changes = []

    def check_server_status(self):
        """Check if Kor'tana's server is running"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def monitor_goals(self):
        """Monitor goal status changes"""
        try:
            response = requests.get(f"{self.api_base}/goals")
            if response.status_code == 200:
                goals = response.json()

                print(f"\n📋 ACTIVE GOALS MONITORING ({len(goals)} total)")
                print("-" * 50)

                for goal in goals:
                    goal_id = goal.get("id")
                    status = goal.get("status", "unknown")
                    description = goal.get("description", "No description")[:50]

                    # Track new goals
                    if goal_id not in self.observed_goals:
                        self.observed_goals.add(goal_id)
                        print(f"🆕 NEW GOAL DETECTED: ID {goal_id}")
                        print(f"   Status: {status}")
                        print(f"   Task: {description}...")

                    # Show current status
                    status_emoji = {
                        "pending": "⏳",
                        "active": "🔄",
                        "completed": "✅",
                        "failed": "❌",
                    }.get(status.lower(), "❓")

                    print(f"{status_emoji} Goal {goal_id}: {status.upper()}")

                    # For active goals, try to get detailed plan
                    if status.lower() == "active":
                        self.check_goal_details(goal_id)

                return len(goals)
        except Exception as e:
            print(f"❌ Error monitoring goals: {e}")
            return 0

    def check_goal_details(self, goal_id):
        """Get detailed plan for an active goal"""
        try:
            response = requests.get(f"{self.api_base}/goals/{goal_id}")
            if response.status_code == 200:
                goal = response.json()
                plan_steps = goal.get("plan_steps", [])
                if plan_steps:
                    print(f"   📝 Plan: {len(plan_steps)} steps")
                    for i, step in enumerate(plan_steps[:3], 1):
                        step_type = step.get("action_type", "unknown")
                        print(f"      {i}. {step_type}")
                    if len(plan_steps) > 3:
                        print(f"      ... and {len(plan_steps) - 3} more steps")
        except requests.RequestException as e:
            print(f"Error fetching goal details for {goal_id}: {e}")
            pass

    def monitor_memories_and_learning(self):
        """Monitor memory formation and learning"""
        try:
            response = requests.get(f"{self.api_base}/memories")
            if response.status_code == 200:
                memories = response.json()

                # Look for new memories since monitoring started
                new_memories = []
                core_beliefs = []
                observations = []

                for memory in memories:
                    memory_id = memory.get("id")
                    memory_type = memory.get("memory_type", "")

                    if memory_id not in self.observed_memories:
                        self.observed_memories.add(memory_id)
                        new_memories.append(memory)

                        if "CORE_BELIEF" in memory_type.upper():
                            core_beliefs.append(memory)
                        elif "OBSERVATION" in memory_type.upper():
                            observations.append(memory)

                if new_memories:
                    print("\n🧠 MEMORY & LEARNING ACTIVITY")
                    print("-" * 50)

                    for memory in observations:
                        print(f"👁️  NEW OBSERVATION: {memory.get('title', 'Untitled')}")
                        print(f"   Type: {memory.get('memory_type', 'Unknown')}")

                    for memory in core_beliefs:
                        print("💡 NEW CORE BELIEF FORMED!")
                        print(f"   Title: {memory.get('title', 'Untitled')}")
                        content = memory.get("content", "")[:100]
                        print(f"   Insight: {content}...")
                        print("   🎉 AUTONOMOUS LEARNING CONFIRMED!")

                return len(core_beliefs)
        except Exception as e:
            print(f"❌ Error monitoring memories: {e}")
            return 0

    def monitor_file_system(self):
        """Monitor file system changes"""
        key_dirs = [
            "src/kortana/core",
            "src/kortana/api",
            "src/kortana/llm_clients",
            "data",
        ]

        print("\n📁 FILE SYSTEM MONITORING")
        print("-" * 50)

        recent_changes = []

        for dir_path in key_dirs:
            if os.path.exists(dir_path):
                for root, _dirs, files in os.walk(dir_path):
                    for file in files:
                        if file.endswith((".py", ".json", ".yaml", ".log")):
                            file_path = os.path.join(root, file)
                            try:
                                stat = os.stat(file_path)
                                modified_time = datetime.fromtimestamp(stat.st_mtime)

                                # Check if modified since monitoring started
                                if modified_time > self.start_time:
                                    recent_changes.append(
                                        {
                                            "file": file_path,
                                            "modified": modified_time,
                                            "size": stat.st_size,
                                        }
                                    )
                            except (OSError, FileNotFoundError) as e:
                                print(f"Error accessing file {file_path}: {e}")
                                pass

        if recent_changes:
            print("🔥 AUTONOMOUS FILE MODIFICATIONS DETECTED:")
            for change in sorted(
                recent_changes, key=lambda x: x["modified"], reverse=True
            )[:5]:
                rel_path = os.path.relpath(change["file"])
                mod_time = change["modified"].strftime("%H:%M:%S")
                print(f"   📝 {mod_time}: {rel_path} ({change['size']} bytes)")
        else:
            print("📂 No recent file modifications detected")

        return len(recent_changes)

    def check_autonomous_status(self):
        """Check autonomous status file"""
        status_file = "data/autonomous_status.json"
        if os.path.exists(status_file):
            try:
                with open(status_file) as f:
                    status = json.load(f)

                print("\n🤖 AUTONOMOUS STATUS")
                print("-" * 50)
                print(f"Status: {status.get('status', 'unknown').upper()}")
                print(f"Current Goal: {status.get('current_goal_id', 'None')}")
                print(f"Last Cycle: {status.get('last_cycle_timestamp', 'Unknown')}")

                cycles = status.get("cycle_counts", {})
                if cycles:
                    print("Cognitive Cycles:")
                    for cycle_type, count in cycles.items():
                        print(f"   {cycle_type}: {count}")

                return True
            except (OSError, json.JSONDecodeError) as e:
                print(f"Error reading status file {status_file}: {e}")
                pass

        print("\n🤖 AUTONOMOUS STATUS: No status file found")
        return False

    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"\n{'=' * 70}")
        print(f"🔍 AUTONOMOUS ACTIVITY SCAN - {current_time}")
        print(f"{'=' * 70}")

        # Check if server is running
        if not self.check_server_status():
            print("❌ KOR'TANA SERVER NOT RESPONDING")
            print("   Please start the server: python launch_secure_server.py")
            return False

        print("✅ KOR'TANA SERVER ONLINE")
        # Monitor all channels
        goal_count = self.monitor_goals() or 0
        learning_count = self.monitor_memories_and_learning() or 0
        file_changes = self.monitor_file_system() or 0
        status_available = self.check_autonomous_status()

        # Summary
        print("\n📊 ACTIVITY SUMMARY")
        print("-" * 50)
        print(f"Active Goals: {goal_count or 0}")
        print(f"New Learning Events: {learning_count or 0}")
        print(f"File Modifications: {file_changes or 0}")
        print(f"Status Tracking: {'✅' if status_available else '❌'}")

        if (
            (goal_count or 0) > 0
            or (learning_count or 0) > 0
            or (file_changes or 0) > 0
        ):
            print("🎉 AUTONOMOUS ACTIVITY DETECTED!")
        else:
            print("😴 No autonomous activity in this cycle")

        return True


def main():
    """Main monitoring loop"""
    print("🚀 KOR'TANA AUTONOMOUS ACTIVITY MONITOR")
    print("🤖 Real-time observation of autonomous software engineering")
    print("=" * 70)
    print()
    print("This monitor will track:")
    print("  📋 Goal status changes and planning")
    print("  🧠 Memory formation and learning")
    print("  📁 File system modifications")
    print("  🤖 Autonomous status updates")
    print()
    print("Press Ctrl+C to stop monitoring...")
    print()

    monitor = AutonomousActivityMonitor()

    try:
        while True:
            success = monitor.run_monitoring_cycle()
            if not success:
                print("❌ Monitoring failed - retrying in 30 seconds...")

            print("\n⏱️  Next scan in 30 seconds...")
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        print("📊 Final summary:")
        print(f"   Monitoring duration: {datetime.now() - monitor.start_time}")
        print(f"   Goals observed: {len(monitor.observed_goals)}")
        print(f"   Memories observed: {len(monitor.observed_memories)}")
        print("✅ Monitoring session complete")


if __name__ == "__main__":
    main()
