#!/usr/bin/env python3
"""
Kor'tana Autonomous Development Monitor
=====================================

Real-time monitoring tool to observe Kor'tana's autonomous development.
This script provides a dashboard view of her cognitive activity.
"""

import asyncio
from datetime import datetime
from pathlib import Path

import aiohttp

API_BASE = "http://localhost:8000"


class KortanaMonitor:
    def __init__(self):
        self.last_goal_count = 0
        self.last_memory_count = 0
        self.monitoring = True

    async def check_server_health(self):
        """Check if Kor'tana server is responding."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE}/health", timeout=2) as response:
                    return response.status == 200
        except:
            return False

    async def get_goals(self):
        """Get current goals and their status."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE}/goals/") as response:
                    if response.status == 200:
                        return await response.json()
        except:
            pass
        return []

    async def get_memories(self):
        """Get current memories to track learning."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE}/memories/") as response:
                    if response.status == 200:
                        return await response.json()
        except:
            pass
        return []

    def check_file_changes(self):
        """Check for recent file modifications."""
        project_root = Path("c:/project-kortana")
        recent_changes = []

        # Key files to monitor
        key_files = [
            "src/kortana/api/routers/goal_router.py",
            "src/kortana/core/services/goal_service.py",
            "data/autonomous_activity.log",
            "data/goals.jsonl",
        ]

        for file_path in key_files:
            full_path = project_root / file_path
            if full_path.exists():
                mtime = full_path.stat().st_mtime
                modified_time = datetime.fromtimestamp(mtime)
                age_minutes = (datetime.now() - modified_time).total_seconds() / 60

                if age_minutes < 30:  # Modified in last 30 minutes
                    recent_changes.append(
                        {
                            "file": file_path,
                            "modified": modified_time.strftime("%H:%M:%S"),
                            "age_minutes": round(age_minutes, 1),
                        }
                    )

        return recent_changes

    def print_header(self):
        """Print monitoring dashboard header."""
        print("\n" + "=" * 80)
        print("🔍 KOR'TANA AUTONOMOUS DEVELOPMENT MONITOR")
        print("=" * 80)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print("Press Ctrl+C to stop monitoring")
        print("-" * 80)

    def print_status(self, server_healthy, goals, memories, file_changes):
        """Print current status dashboard."""

        # Server Status
        status_emoji = "🟢" if server_healthy else "🔴"
        print(f"{status_emoji} SERVER: {'ONLINE' if server_healthy else 'OFFLINE'}")

        if not server_healthy:
            print("❌ Cannot connect to Kor'tana server at http://localhost:8000")
            print("💡 Make sure server is running: python src\\kortana\\main.py")
            return

        # Goals Analysis
        pending_goals = [g for g in goals if g.get("status") == "pending"]
        active_goals = [
            g for g in goals if g.get("status") in ["active", "in_progress"]
        ]
        completed_goals = [g for g in goals if g.get("status") == "completed"]

        print(
            f"🎯 GOALS: {len(goals)} total | "
            f"⏳ {len(pending_goals)} pending | "
            f"🔄 {len(active_goals)} active | "
            f"✅ {len(completed_goals)} completed"
        )

        # Show active goals
        for goal in active_goals:
            print(
                f"   🔄 ACTIVE: Goal {goal.get('id')} - {goal.get('description', '')[:50]}..."
            )

        # Memory/Learning Analysis
        core_beliefs = [m for m in memories if m.get("memory_type") == "CORE_BELIEF"]
        observations = [m for m in memories if m.get("memory_type") == "OBSERVATION"]

        print(
            f"🧠 MEMORY: {len(memories)} total | "
            f"💡 {len(core_beliefs)} beliefs | "
            f"📝 {len(observations)} observations"
        )

        # Detect new learning
        if len(memories) > self.last_memory_count:
            new_memories = len(memories) - self.last_memory_count
            print(f"   🆕 +{new_memories} new memories since last check!")

        # File Changes
        print(f"📁 RECENT FILE CHANGES ({len(file_changes)} files modified <30min):")
        for change in file_changes[:5]:  # Show max 5 recent changes
            print(
                f"   📝 {change['file']} (modified {change['modified']}, {change['age_minutes']}min ago)"
            )

        # Update counters
        self.last_goal_count = len(goals)
        self.last_memory_count = len(memories)

        print("-" * 80)

    def print_autonomous_indicators(self, goals, memories):
        """Print indicators of autonomous activity."""

        # Recent activity indicators
        recent_activity = []

        # Check for recently completed goals
        for goal in goals:
            if goal.get("status") == "completed" and goal.get("completed_at"):
                # This is a simplified check - in reality you'd parse the timestamp
                recent_activity.append(
                    f"✅ Completed: {goal.get('description', '')[:40]}..."
                )

        # Check for recent learning
        recent_beliefs = [m for m in memories if m.get("memory_type") == "CORE_BELIEF"]
        if recent_beliefs:
            latest_belief = recent_beliefs[-1]
            content = latest_belief.get("content", "")[:60]
            recent_activity.append(f"🧠 Latest Belief: {content}...")

        if recent_activity:
            print("🤖 AUTONOMOUS ACTIVITY DETECTED:")
            for activity in recent_activity[-3:]:  # Show last 3 activities
                print(f"   {activity}")
        else:
            print("⏳ Monitoring for autonomous activity...")

        print()

    async def monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                self.print_header()

                # Gather current state
                server_healthy = await self.check_server_health()
                goals = await self.get_goals()
                memories = await self.get_memories()
                file_changes = self.check_file_changes()

                # Display status
                self.print_status(server_healthy, goals, memories, file_changes)

                if server_healthy:
                    self.print_autonomous_indicators(goals, memories)

                # Wait before next check
                await asyncio.sleep(10)  # Check every 10 seconds

            except KeyboardInterrupt:
                print("\n\n🛑 Monitoring stopped by user")
                self.monitoring = False
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                await asyncio.sleep(5)


async def main():
    """Start the monitoring dashboard."""
    print("🚀 Starting Kor'tana Autonomous Development Monitor...")
    print("This tool will show real-time autonomous activity indicators.")
    print()

    monitor = KortanaMonitor()
    await monitor.monitor_loop()


if __name__ == "__main__":
    asyncio.run(main())
