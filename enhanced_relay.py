#!/usr/bin/env python3
"""
Enhanced Autonomous Relay with Context Management
================================================

Combines the existing autonomous relay with SQLite database for:
- Context package creation and storage
- Token usage tracking
- Agent handoff management
- Task summarization

Usage:
    python enhanced_relay.py --loop    # Run autonomous system
    python enhanced_relay.py --status  # Show system status
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path


class KortanaEnhancedRelay:
    """Enhanced autonomous relay with context management and DB integration"""

    def __init__(self, project_root: str = None):
        """Initialize the enhanced relay system"""
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent
        )
        self.logs_dir = self.project_root / "logs"
        self.queues_dir = self.project_root / "queues"
        self.data_dir = self.project_root / "data"
        self.db_path = self.project_root / "kortana.db"

        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        self.queues_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

        # Initialize database
        self._init_database()

        # Agent configuration
        self.agents = self._discover_agents()
        self.current_task_id = self._get_or_create_task_id()

        print("🔄 Enhanced Kor'tana Relay initialized")
        print(f"📁 Project: {self.project_root}")
        print(f"💾 Database: {self.db_path}")
        print(f"🤖 Agents: {list(self.agents.keys())}")
        print(f"📋 Task ID: {self.current_task_id}")

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Context table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS context (
                task_id TEXT PRIMARY KEY,
                summary TEXT,
                code TEXT,
                issues TEXT,
                commit_ref TEXT,
                timestamp TEXT,
                tokens INTEGER
            )
        """
        )

        # Agent activity table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                task_id TEXT,
                action_type TEXT,
                message_count INTEGER DEFAULT 0,
                tokens_used INTEGER DEFAULT 0,
                timestamp TEXT,
                metadata TEXT
            )
        """
        )

        # System state table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def _discover_agents(self) -> dict[str, dict]:
        """Auto-discover agents from log files"""
        agents = {}
        log_files = list(self.logs_dir.glob("*.log"))

        for log_file in log_files:
            agent_name = log_file.stem
            queue_file = self.queues_dir / f"{agent_name}_in.txt"

            # Ensure queue file exists
            queue_file.touch(exist_ok=True)

            agents[agent_name] = {
                "log": log_file,
                "queue": queue_file,
                "status": "discovered",
                "messages_processed": 0,
                "tokens_used": 0,
                "last_activity": None,
            }

        return agents

    def _get_or_create_task_id(self) -> str:
        """Get current task ID or create new one"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check for active task
        cursor.execute("SELECT value FROM system_state WHERE key = 'active_task_id'")
        result = cursor.fetchone()

        if result and result[0] and result[0] != "None":
            task_id = result[0]
        else:
            # Create new task ID
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            cursor.execute(
                """
                INSERT OR REPLACE INTO system_state (key, value, updated_at)
                VALUES ('active_task_id', ?, ?)
            """,
                (task_id, datetime.now().isoformat()),
            )
            conn.commit()

        conn.close()
        return task_id

    def _get_agent_new_messages(self, agent_name: str) -> list[str]:
        """Get new messages from agent log"""
        log_file = self.agents[agent_name]["log"]

        if not log_file.exists():
            return []

        # Read all lines
        try:
            with open(log_file, encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"⚠️  Error reading {log_file}: {e}")
            return []

        # For simplicity, get last few new lines (can be enhanced with state tracking)
        new_messages = []
        for line in lines[-5:]:  # Get last 5 lines
            line = line.strip()
            if line and not line.startswith("//"):
                new_messages.append(line)

        return new_messages

    def _relay_messages(self, source_agent: str, messages: list[str]):
        """Relay messages to other agents and log activity"""
        if not messages:
            return 0

        timestamp = datetime.now().strftime("%H:%M:%S")
        relayed_count = 0

        # Record agent activity in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO agent_activity
            (agent_name, task_id, action_type, message_count, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                source_agent,
                self.current_task_id,
                "relay",
                len(messages),
                datetime.now().isoformat(),
                json.dumps({"timestamp": timestamp}),
            ),
        )

        # Relay to other agents
        for target_agent, agent_info in self.agents.items():
            if target_agent == source_agent:
                continue

            queue_file = agent_info["queue"]

            try:
                with open(queue_file, "a", encoding="utf-8") as f:
                    for message in messages:
                        relay_message = f"[{timestamp}] {source_agent}: {message}"
                        f.write(relay_message + "\n")
                        relayed_count += 1

                print(f"📤 {source_agent} → {target_agent}: {len(messages)} messages")

            except Exception as e:
                print(f"⚠️  Error writing to {queue_file}: {e}")

        conn.commit()
        conn.close()

        return relayed_count

    def _create_context_package(self) -> dict:
        """Create a context package for the current task"""
        # Get recent activity from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT agent_name, action_type, message_count, timestamp
            FROM agent_activity
            WHERE task_id = ?
            ORDER BY timestamp DESC LIMIT 10
        """,
            (self.current_task_id,),
        )

        activities = cursor.fetchall()

        # Create context summary
        context = {
            "task_id": self.current_task_id,
            "timestamp": datetime.now().isoformat(),
            "agents_active": len(self.agents),
            "recent_activities": activities,
            "system_status": "operational",
        }

        # Store context package
        context_json = json.dumps(context, indent=2)
        estimated_tokens = len(context_json) // 4  # Rough estimate

        cursor.execute(
            """
            INSERT OR REPLACE INTO context
            (task_id, summary, timestamp, tokens)
            VALUES (?, ?, ?, ?)
        """,
            (
                self.current_task_id,
                context_json,
                datetime.now().isoformat(),
                estimated_tokens,
            ),
        )

        conn.commit()
        conn.close()

        return context

    def relay_cycle(self) -> dict[str, int]:
        """Enhanced relay cycle with database logging"""
        cycle_stats = {
            "agents_checked": 0,
            "messages_found": 0,
            "messages_relayed": 0,
            "context_packages": 0,
        }

        print(f"🔄 Enhanced relay cycle at {datetime.now().strftime('%H:%M:%S')}")

        for agent_name in self.agents.keys():
            cycle_stats["agents_checked"] += 1

            # Get new messages
            new_messages = self._get_agent_new_messages(agent_name)

            if new_messages:
                cycle_stats["messages_found"] += len(new_messages)
                print(f"📨 {agent_name}: {len(new_messages)} new messages")

                # Relay messages
                relayed = self._relay_messages(agent_name, new_messages)
                cycle_stats["messages_relayed"] += relayed

                # Update agent stats
                self.agents[agent_name]["messages_processed"] += len(new_messages)
                self.agents[agent_name]["last_activity"] = datetime.now().isoformat()

        # Create context package every 10 cycles (or when significant activity)
        if cycle_stats["messages_found"] > 0:
            self._create_context_package()
            cycle_stats["context_packages"] = 1

        return cycle_stats

    def print_enhanced_status(self):
        """Print enhanced status with database info"""
        print("\n" + "=" * 60)
        print("📊 KOR'TANA ENHANCED RELAY STATUS")
        print("=" * 60)

        # Agent status
        for agent_name, agent_info in self.agents.items():
            status = agent_info["status"]
            msg_count = agent_info["messages_processed"]
            last_activity = agent_info["last_activity"] or "never"

            emoji = {
                "active": "🟢",
                "idle": "🟡",
                "inactive": "⚪",
                "discovered": "🔵",
            }.get(status, "❓")
            print(
                f"{emoji} {agent_name:8} | {status:8} | {msg_count:3} msgs | {last_activity}"
            )

        # Database statistics
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM agent_activity WHERE task_id = ?",
            (self.current_task_id,),
        )
        activity_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM context")
        context_count = cursor.fetchone()[0]

        conn.close()

        print("\n💾 DATABASE:")
        print(f"   Task ID: {self.current_task_id}")
        print(f"   Activities: {activity_count}")
        print(f"   Contexts: {context_count}")
        print("=" * 60)

    def run_enhanced_loop(self, interval: int = 3):
        """Run enhanced autonomous loop"""
        print(f"🚀 Starting enhanced autonomous relay loop (interval: {interval}s)")
        print("📢 Press Ctrl+C to stop")

        cycle_count = 0

        try:
            while True:
                cycle_count += 1

                # Run enhanced relay cycle
                stats = self.relay_cycle()

                # Show status periodically
                if cycle_count % 10 == 0:
                    self.print_enhanced_status()

                # Show activity summary
                if stats["messages_found"] > 0:
                    print(
                        f"✅ Cycle {cycle_count}: {stats['messages_found']} found, {stats['messages_relayed']} relayed, {stats['context_packages']} contexts"
                    )
                elif cycle_count % 20 == 0:
                    print(
                        f"💓 Cycle {cycle_count}: System monitoring {stats['agents_checked']} agents"
                    )

                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n🛑 Enhanced relay stopped after {cycle_count} cycles")
            self.print_enhanced_status()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Kor'tana Enhanced Autonomous Relay")
    parser.add_argument(
        "--loop", action="store_true", help="Run continuous enhanced loop"
    )
    parser.add_argument(
        "--interval", type=int, default=3, help="Loop interval in seconds"
    )
    parser.add_argument("--status", action="store_true", help="Show enhanced status")

    args = parser.parse_args()

    # Initialize enhanced relay
    relay = KortanaEnhancedRelay()

    if args.status:
        relay.print_enhanced_status()
    elif args.loop:
        relay.run_enhanced_loop(args.interval)
    else:
        # Single enhanced cycle
        print("🔄 Running single enhanced relay cycle...")
        stats = relay.relay_cycle()
        print(f"✅ Complete: {stats}")
        relay.print_enhanced_status()


if __name__ == "__main__":
    main()
