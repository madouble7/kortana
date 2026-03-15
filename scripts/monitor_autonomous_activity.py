#!/usr/bin/env python3
"""
Autonomous Activity Monitor for Kor'tana
Provides real-time monitoring of autonomous system state through API/Database
"""

import sys
import time
from datetime import datetime
from typing import Any

import requests


class AutonomousMonitor:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.previous_state = {}
        self.start_time = datetime.now()

    def get_goals_state(self) -> list[dict[str, Any]]:
        """Get current goals and their states"""
        try:
            response = requests.get(f"{self.base_url}/goals/")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Error fetching goals: {e}")
            return []

    def get_tasks_for_goal(self, goal_id: int) -> list[dict[str, Any]]:
        """Get tasks for a specific goal"""
        try:
            response = requests.get(f"{self.base_url}/goals/{goal_id}/tasks")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Error fetching tasks for goal {goal_id}: {e}")
            return []

    def get_recent_memories(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent memories, especially CORE_BELIEF types"""
        try:
            response = requests.get(f"{self.base_url}/memories/?limit={limit}")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Error fetching memories: {e}")
            return []

    def detect_state_changes(self, current_state: dict) -> list[str]:
        """Detect changes in system state"""
        changes = []

        # Compare with previous state
        for key, value in current_state.items():
            if key not in self.previous_state:
                changes.append(f"🆕 New {key}: {value}")
            elif self.previous_state[key] != value:
                changes.append(
                    f"🔄 Changed {key}: {self.previous_state[key]} → {value}"
                )

        self.previous_state = current_state.copy()
        return changes

    def print_autonomous_activity(self):
        """Print current autonomous activity"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        runtime = datetime.now() - self.start_time

        print(f"\n{'=' * 60}")
        print(f"🤖 AUTONOMOUS ACTIVITY MONITOR - {timestamp}")
        print(f"⏱️  Runtime: {runtime}")
        print(f"{'=' * 60}")

        # Check goals
        goals = self.get_goals_state()
        active_goals = [
            g
            for g in goals
            if g.get("status") not in ["COMPLETED", "FAILED", "CANCELLED"]
        ]

        if active_goals:
            print(f"\n🎯 ACTIVE GOALS ({len(active_goals)}):")
            for goal in active_goals:
                status_emoji = {
                    "PENDING": "⏳",
                    "PLANNING": "🧠",
                    "EXECUTING": "⚡",
                    "VALIDATING": "✅",
                    "COMPLETED": "🎉",
                }.get(goal.get("status", ""), "❓")

                print(
                    f"  {status_emoji} [{goal.get('id')}] {goal.get('title', 'Unknown')}"
                )
                print(f"     Status: {goal.get('status', 'Unknown')}")
                print(f"     Created: {goal.get('created_at', 'Unknown')}")

                # Get tasks for this goal
                goal_id = goal.get("id")
                tasks = (
                    self.get_tasks_for_goal(goal_id) if isinstance(goal_id, int) else []
                )
                if tasks:
                    print(f"     📋 Tasks ({len(tasks)}):")
                    for task in tasks[-3:]:  # Show last 3 tasks
                        task_emoji = {
                            "PENDING": "⏳",
                            "IN_PROGRESS": "🔄",
                            "COMPLETED": "✅",
                            "FAILED": "❌",
                        }.get(task.get("status", ""), "❓")

                        print(
                            f"        {task_emoji} {task.get('action_type', 'Unknown')}: {task.get('status', 'Unknown')}"
                        )
                print()
        else:
            print("\n💤 No active goals - system idle")

        # Check recent memories (learning activity)
        memories = self.get_recent_memories(5)
        core_beliefs = [m for m in memories if m.get("memory_type") == "CORE_BELIEF"]

        if core_beliefs:
            print(f"\n🧠 RECENT LEARNING ({len(core_beliefs)} new beliefs):")
            for belief in core_beliefs:
                created = belief.get("created_at", "Unknown")
                content = belief.get("content", "No content")[:80] + "..."
                confidence = belief.get("confidence_score", 0)
                print(f"  💡 [{created}] Confidence: {confidence:.2f}")
                print(f"     {content}")
                print()
        else:
            print("\n🧠 No recent learning activity")

        # System health check
        try:
            health_response = requests.get(f"{self.base_url}/health")
            if health_response.status_code == 200:
                print("💚 System Health: OPERATIONAL")
            else:
                print(f"🟡 System Health: Response {health_response.status_code}")
        except Exception as e:
            print(f"❌ System Health: UNREACHABLE ({e})")

    def run_continuous_monitoring(self, interval: int = 10):
        """Run continuous monitoring loop"""
        print("🚀 Starting Autonomous Activity Monitor...")
        print(f"📡 Monitoring: {self.base_url}")
        print(f"⏰ Update interval: {interval} seconds")
        print("Press Ctrl+C to stop")

        try:
            while True:
                self.print_autonomous_activity()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            runtime = datetime.now() - self.start_time
            print(f"📊 Total monitoring time: {runtime}")


if __name__ == "__main__":
    monitor = AutonomousMonitor()

    # Check if server is running
    try:
        response = requests.get(f"{monitor.base_url}/health", timeout=5)
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        print("🔧 Please start the server first:")
        print("   python -m uvicorn src.kortana.main:app --reload --port 8000")
        sys.exit(1)

    # Run monitoring
    monitor.run_continuous_monitoring()
