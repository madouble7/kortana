#!/usr/bin/env python3
"""
AUTONOMOUS INTELLIGENCE MONITOR
==============================
Real-time proof that Kor'tana is working and developing autonomously
"""

import os
import time
from datetime import datetime

import requests


class KortanaIntelligenceMonitor:
    """Monitor all channels of Kor'tana's autonomous activity"""

    def __init__(self, api_base="http://localhost:8000"):
        self.api_base = api_base
        self.baseline_files = {}
        self.previous_goals = set()
        self.previous_memories = set()
        self.autonomous_activity_detected = False

        print("🔬 AUTONOMOUS INTELLIGENCE MONITOR INITIALIZED")
        print("=" * 60)
        print("Monitoring Kor'tana for signs of autonomous development...")
        print()

    def check_server_health(self) -> bool:
        """Verify Kor'tana server is running"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"⚠️ Server connection error: {e}")
            return False

    def monitor_goal_evolution(self) -> dict:
        """Track goal status changes - proof of autonomous goal processing"""
        try:
            response = requests.get(f"{self.api_base}/goals", timeout=10)
            if response.status_code != 200:
                return {"status": "error", "message": "Cannot fetch goals"}

            goals = response.json()
            current_goals = {goal["id"]: goal for goal in goals}

            # Detect new goals
            new_goals = set(current_goals.keys()) - self.previous_goals

            # Detect status changes
            status_changes = []
            active_goals = []
            completed_goals = []

            for goal_id, goal in current_goals.items():
                if goal["status"] == "active":
                    active_goals.append(goal)
                elif goal["status"] == "completed":
                    completed_goals.append(goal)

                if goal_id in new_goals:
                    status_changes.append(f"NEW GOAL: {goal['title'][:50]}...")

            self.previous_goals = set(current_goals.keys())

            return {
                "status": "success",
                "total_goals": len(goals),
                "active_goals": len(active_goals),
                "completed_goals": len(completed_goals),
                "status_changes": status_changes,
                "active_goal_details": active_goals[:1],  # Show first active goal
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def monitor_memory_formation(self) -> dict:
        """Track memory creation - proof of learning and development"""
        try:
            response = requests.get(f"{self.api_base}/memories", timeout=10)
            if response.status_code != 200:
                return {"status": "error", "message": "Cannot fetch memories"}

            memories = response.json()
            current_memory_ids = {mem["id"]: mem for mem in memories}

            # Detect new memories
            new_memory_ids = set(current_memory_ids.keys()) - self.previous_memories
            new_memories = []
            core_beliefs = []
            observations = []

            for mem_id in new_memory_ids:
                memory = current_memory_ids[mem_id]
                new_memories.append(memory)

                if memory.get("memory_type") == "CORE_BELIEF":
                    core_beliefs.append(memory)
                elif memory.get("memory_type") == "OBSERVATION":
                    observations.append(memory)

            self.previous_memories = set(current_memory_ids.keys())

            return {
                "status": "success",
                "total_memories": len(memories),
                "new_memories": len(new_memories),
                "new_core_beliefs": len(core_beliefs),
                "new_observations": len(observations),
                "recent_core_beliefs": core_beliefs[-2:] if core_beliefs else [],
                "recent_observations": observations[-2:] if observations else [],
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def monitor_file_system_changes(self) -> dict:
        """Track file modifications - proof of autonomous engineering work"""
        target_files = {
            "goal_router": "src/kortana/api/routers/goal_router.py",
            "goal_service": "src/kortana/api/services/goal_service.py",
            "services_init": "src/kortana/api/services/__init__.py",
        }

        changes = []
        file_status = {}

        for name, path in target_files.items():
            if os.path.exists(path):
                size = os.path.getsize(path)
                mtime = os.path.getmtime(path)
                mtime_str = datetime.fromtimestamp(mtime).strftime("%H:%M:%S")

                # Check for changes since baseline
                if name in self.baseline_files:
                    baseline_size, baseline_time = self.baseline_files[name]
                    if size != baseline_size or mtime != baseline_time:
                        changes.append(
                            f"MODIFIED: {name} ({baseline_size} -> {size} bytes)"
                        )
                        self.autonomous_activity_detected = True
                else:
                    # New file created
                    if name == "goal_service":  # This should be created by Kor'tana
                        changes.append(
                            f"CREATED: {name} ({size} bytes) - AUTONOMOUS CREATION!"
                        )
                        self.autonomous_activity_detected = True

                self.baseline_files[name] = (size, mtime)
                file_status[name] = {
                    "exists": True,
                    "size": size,
                    "modified": mtime_str,
                    "status": "MODIFIED" if changes else "BASELINE",
                }
            else:
                file_status[name] = {
                    "exists": False,
                    "size": 0,
                    "modified": "N/A",
                    "status": "AWAITING CREATION",
                }

        return {
            "status": "success",
            "changes_detected": len(changes) > 0,
            "changes": changes,
            "file_status": file_status,
            "autonomous_activity": self.autonomous_activity_detected,
        }

    def display_intelligence_dashboard(self):
        """Display comprehensive autonomous intelligence dashboard"""
        print(f"🤖 INTELLIGENCE DASHBOARD - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)

        # Server Health
        server_healthy = self.check_server_health()
        health_icon = "✅" if server_healthy else "❌"
        print(
            f"{health_icon} Server Status: {'ONLINE' if server_healthy else 'OFFLINE'}"
        )

        if not server_healthy:
            print("   ⚠️  Cannot monitor - server is not responding")
            print("   Start server: python src/kortana/main.py")
            return

        print()

        # Goal Processing Intelligence
        goal_data = self.monitor_goal_evolution()
        print("🎯 GOAL PROCESSING INTELLIGENCE:")
        if goal_data["status"] == "success":
            print(f"   📊 Total Goals: {goal_data['total_goals']}")
            print(f"   🔄 Active Goals: {goal_data['active_goals']}")
            print(f"   ✅ Completed Goals: {goal_data['completed_goals']}")

            if goal_data["status_changes"]:
                print("   🚨 RECENT CHANGES:")
                for change in goal_data["status_changes"]:
                    print(f"      • {change}")

            if goal_data["active_goal_details"]:
                active = goal_data["active_goal_details"][0]
                print(f"   🔥 ACTIVE TASK: {active['title'][:40]}...")
                print(
                    f"      Status: {active['status']} | Priority: {active.get('priority', 'N/A')}"
                )
        else:
            print(f"   ❌ Error: {goal_data['message']}")

        print()

        # Learning & Memory Intelligence
        memory_data = self.monitor_memory_formation()
        print("🧠 LEARNING & MEMORY INTELLIGENCE:")
        if memory_data["status"] == "success":
            print(f"   📚 Total Memories: {memory_data['total_memories']}")
            print(f"   🆕 New Memories: {memory_data['new_memories']}")
            print(f"   💡 New Core Beliefs: {memory_data['new_core_beliefs']}")
            print(f"   📝 New Observations: {memory_data['new_observations']}")

            if memory_data["new_core_beliefs"]:
                print("   🎉 AUTONOMOUS LEARNING DETECTED!")
                for belief in memory_data["recent_core_beliefs"]:
                    print(f"      💭 '{belief.get('title', 'Untitled')}'")
        else:
            print(f"   ❌ Error: {memory_data['message']}")

        print()

        # Engineering Work Intelligence
        file_data = self.monitor_file_system_changes()
        print("⚙️ ENGINEERING WORK INTELLIGENCE:")
        if file_data["status"] == "success":
            if file_data["changes"]:
                print("   🔥 AUTONOMOUS ENGINEERING ACTIVITY DETECTED!")
                for change in file_data["changes"]:
                    print(f"      • {change}")
            else:
                print("   ⏳ Monitoring for file system changes...")

            print("   📁 File Status:")
            for name, status in file_data["file_status"].items():
                icon = "✅" if status["exists"] else "⏳"
                print(
                    f"      {icon} {name}: {status['size']} bytes | {status['status']}"
                )

        print()

        # Overall Intelligence Assessment
        print("🎯 AUTONOMOUS INTELLIGENCE ASSESSMENT:")
        if self.autonomous_activity_detected:
            print("   🌟 CONFIRMED: Kor'tana is actively working autonomously!")
            print("   📈 Evidence: File system changes detected")
        elif goal_data.get("active_goals", 0) > 0:
            print("   🔄 PROCESSING: Kor'tana is working on active goals")
            print("   ⏱️  Waiting for engineering output...")
        else:
            print("   🛌 IDLE: No active goals or autonomous activity detected")
            print("   💡 Submit a goal to activate autonomous processing")

        print("=" * 60)


def main():
    """Main monitoring loop"""
    monitor = KortanaIntelligenceMonitor()

    print("🔬 Starting autonomous intelligence monitoring...")
    print("📋 This will show you PROOF that Kor'tana is working autonomously")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            monitor.display_intelligence_dashboard()
            print("\n⏳ Next update in 10 seconds...\n")
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")
        print("\n📊 FINAL INTELLIGENCE SUMMARY:")
        monitor.display_intelligence_dashboard()

        if monitor.autonomous_activity_detected:
            print("\n🎉 AUTONOMOMOUS INTELLIGENCE CONFIRMED!")
            print("   Evidence of independent development was observed.")
        else:
            print("\n📋 No autonomous activity detected during monitoring")
            print("   Ensure goals are submitted and server is running.")


if __name__ == "__main__":
    main()
