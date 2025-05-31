#!/usr/bin/env python3
"""
Kor'tana Autonomous Relay System
===============================

Minimal viable orchestration for proto-autonomy.
Scans all agent logs, relays new messages to queues, prevents duplicates.

Usage:
    python relays/autonomous_relay.py
    python relays/autonomous_relay.py --loop    # Run forever
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class KortanaRelay:
    """Autonomous relay system for agent orchestration"""

    def __init__(self, project_root: str = None):
        """Initialize the relay system"""
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent
        )
        self.logs_dir = self.project_root / "logs"
        self.queues_dir = self.project_root / "queues"
        self.relay_state_file = self.project_root / "data" / "relay_state.json"

        # Track what we've already relayed to prevent duplicates
        self.relay_state = self._load_relay_state()

        # Agent configuration
        self.agents = self._discover_agents()

        print("🔄 Kor'tana Relay initialized")
        print(f"📁 Logs: {self.logs_dir}")
        print(f"📥 Queues: {self.queues_dir}")
        print(f"🤖 Agents: {list(self.agents.keys())}")

    def _discover_agents(self) -> Dict[str, Dict[str, Path]]:
        """Auto-discover agents from log and queue files"""
        agents = {}

        # Find all log files
        log_files = list(self.logs_dir.glob("*.log"))

        for log_file in log_files:
            agent_name = log_file.stem  # Remove .log extension
            queue_file = self.queues_dir / f"{agent_name}_in.txt"

            agents[agent_name] = {
                "log": log_file,
                "queue": queue_file,
                "status": "discovered",
            }

            # Ensure queue file exists
            queue_file.parent.mkdir(exist_ok=True)
            queue_file.touch(exist_ok=True)

        return agents

    def _load_relay_state(self) -> Dict[str, Dict[str, any]]:
        """Load relay state to track what's been processed"""
        if self.relay_state_file.exists():
            try:
                with open(self.relay_state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        return {}

    def _save_relay_state(self):
        """Save relay state to prevent duplicate processing"""
        self.relay_state_file.parent.mkdir(exist_ok=True)
        with open(self.relay_state_file, "w") as f:
            json.dump(self.relay_state, f, indent=2)

    def _get_new_messages(self, agent_name: str) -> List[str]:
        """Get new messages from agent log since last relay"""
        log_file = self.agents[agent_name]["log"]

        if not log_file.exists():
            return []

        # Get current state for this agent
        agent_state = self.relay_state.get(agent_name, {})
        last_line_count = agent_state.get("last_line_count", 0)
        last_processed_time = agent_state.get("last_processed_time", "")

        # Read all lines from log
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"⚠️  Error reading {log_file}: {e}")
            return []

        # Get new lines since last processing
        new_lines = lines[last_line_count:]

        # Filter out empty lines and clean up
        new_messages = []
        for line in new_lines:
            line = line.strip()
            if line and not line.startswith("//"):  # Skip comments
                new_messages.append(line)

        # Update state
        if new_messages:
            self.relay_state[agent_name] = {
                "last_line_count": len(lines),
                "last_processed_time": datetime.now().isoformat(),
                "messages_processed": agent_state.get("messages_processed", 0)
                + len(new_messages),
            }

        return new_messages

    def _relay_to_all_other_agents(self, source_agent: str, messages: List[str]):
        """Relay messages to all other agents' queues"""
        if not messages:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        relayed_count = 0

        for target_agent, agent_info in self.agents.items():
            if target_agent == source_agent:
                continue  # Don't relay to self

            queue_file = agent_info["queue"]

            try:
                with open(queue_file, "a", encoding="utf-8") as f:
                    for message in messages:
                        # Format: [timestamp] source_agent: message
                        relay_message = f"[{timestamp}] {source_agent}: {message}"
                        f.write(relay_message + "\n")
                        relayed_count += 1

                print(f"📤 {source_agent} → {target_agent}: {len(messages)} messages")

            except Exception as e:
                print(f"⚠️  Error writing to {queue_file}: {e}")

        return relayed_count

    def _check_agent_status(self, agent_name: str) -> str:
        """Check if agent is active based on recent activity"""
        agent_state = self.relay_state.get(agent_name, {})
        last_time = agent_state.get("last_processed_time", "")

        if not last_time:
            return "inactive"

        try:
            last_dt = datetime.fromisoformat(last_time)
            now = datetime.now()
            minutes_since = (now - last_dt).total_seconds() / 60

            if minutes_since < 5:
                return "active"
            elif minutes_since < 30:
                return "idle"
            else:
                return "inactive"
        except:
            return "unknown"

    def relay_cycle(self) -> Dict[str, int]:
        """Single relay cycle - check all agents and relay new messages"""
        cycle_stats = {
            "agents_checked": 0,
            "messages_found": 0,
            "messages_relayed": 0,
            "active_agents": 0,
        }

        print(f"🔄 Relay cycle started at {datetime.now().strftime('%H:%M:%S')}")

        for agent_name in self.agents.keys():
            cycle_stats["agents_checked"] += 1

            # Check for new messages
            new_messages = self._get_new_messages(agent_name)

            if new_messages:
                cycle_stats["messages_found"] += len(new_messages)
                print(f"📨 {agent_name}: {len(new_messages)} new messages")

                # Relay to all other agents
                relayed = self._relay_to_all_other_agents(agent_name, new_messages)
                cycle_stats["messages_relayed"] += relayed

            # Check agent status
            status = self._check_agent_status(agent_name)
            if status == "active":
                cycle_stats["active_agents"] += 1

            self.agents[agent_name]["status"] = status

        # Save state after each cycle
        self._save_relay_state()

        return cycle_stats

    def print_status(self):
        """Print current system status"""
        print("\n" + "=" * 50)
        print("📊 KOR'TANA RELAY STATUS")
        print("=" * 50)

        for agent_name, agent_info in self.agents.items():
            status = agent_info["status"]
            emoji = {
                "active": "🟢",
                "idle": "🟡",
                "inactive": "⚪",
                "discovered": "🔵",
            }.get(status, "❓")

            agent_state = self.relay_state.get(agent_name, {})
            msg_count = agent_state.get("messages_processed", 0)
            last_time = agent_state.get("last_processed_time", "never")

            print(
                f"{emoji} {agent_name:8} | {status:8} | {msg_count:3} msgs | last: {last_time}"
            )

        print("=" * 50)

    def run_loop(self, interval: int = 2):
        """Run continuous relay loop"""
        print(f"🚀 Starting autonomous relay loop (interval: {interval}s)")
        print("📢 Press Ctrl+C to stop")

        cycle_count = 0

        try:
            while True:
                cycle_count += 1

                # Run relay cycle
                stats = self.relay_cycle()

                # Print periodic status
                if cycle_count % 10 == 0:  # Every 20 seconds
                    self.print_status()

                # Show cycle summary if activity
                if stats["messages_found"] > 0:
                    print(
                        f"✅ Cycle {cycle_count}: {stats['messages_found']} found, {stats['messages_relayed']} relayed"
                    )
                elif cycle_count % 30 == 0:  # Show heartbeat every minute
                    print(
                        f"💓 Cycle {cycle_count}: Monitoring {stats['agents_checked']} agents, {stats['active_agents']} active"
                    )

                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n🛑 Relay loop stopped after {cycle_count} cycles")
            self.print_status()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Kor'tana Autonomous Relay System")
    parser.add_argument("--loop", action="store_true", help="Run continuous relay loop")
    parser.add_argument(
        "--interval", type=int, default=2, help="Loop interval in seconds"
    )
    parser.add_argument("--status", action="store_true", help="Show status and exit")

    args = parser.parse_args()

    # Initialize relay system
    relay = KortanaRelay()

    if args.status:
        relay.print_status()
    elif args.loop:
        relay.run_loop(args.interval)
    else:
        # Single cycle
        print("🔄 Running single relay cycle...")
        stats = relay.relay_cycle()
        print(
            f"✅ Complete: {stats['messages_found']} found, {stats['messages_relayed']} relayed"
        )
        relay.print_status()


if __name__ == "__main__":
    main()
