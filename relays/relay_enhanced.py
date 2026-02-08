#!/usr/bin/env python3
"""
Enhanced Autonomous Relay with Context Management
================================================

Enhanced version of the Kor'tana autonomous relay that includes:
- Database integration for context packages
- Token usage tracking and summarization
- Agent handoff management
- Task context preservation

Usage:
    python relay_enhanced.py --loop    # Run autonomous system
    python relay_enhanced.py --status  # Show system status
    python relay_enhanced.py --summarize  # Trigger summarization
"""

import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import tiktoken
try:
    from relays.protocol import append_text_line, tail_text_lines, utc_now_iso
except ModuleNotFoundError:
    from protocol import append_text_line, tail_text_lines, utc_now_iso


class KortanaEnhancedRelay:
    """Enhanced autonomous relay with context management and DB integration"""

    def __init__(self, project_root: str | None = None):
        """Initialize the enhanced relay system"""
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent
        )
        self.logs_dir = self.project_root / "logs"
        self.queues_dir = self.project_root / "queues"
        self.data_dir = self.project_root / "data"
        self.db_path = self.project_root / "kortana.db"
        self.relay_state_file = self.data_dir / "relay_state.json"

        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        self.queues_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

        # Initialize database
        self._init_database()

        # Track what we've already relayed to prevent duplicates
        self.relay_state = self._load_relay_state()

        # Agent configuration
        self.agents = self._discover_agents()

        # Token tracking
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.context_window = 128000  # Default context window
        self.summarization_threshold = 0.4  # 40% of context window

        print("🔄 Enhanced Kor'tana Relay initialized")
        print(f"📁 Logs: {self.logs_dir}")
        print(f"📥 Queues: {self.queues_dir}")
        print(f"💾 Database: {self.db_path}")
        print(f"🤖 Agents: {list(self.agents.keys())}")

    def _init_database(self):
        """Initialize the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Context table for task context packages
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
                agent_name TEXT,
                message TEXT,
                tokens INTEGER,
                timestamp TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def _discover_agents(self) -> dict[str, dict[str, Any]]:
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

    def _load_relay_state(self) -> dict[str, dict[str, Any]]:
        """Load relay state to track what's been processed"""
        if self.relay_state_file.exists():
            try:
                with open(self.relay_state_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        return {}

    def _save_relay_state(self):
        """Save relay state to prevent duplicate processing"""
        self.relay_state_file.parent.mkdir(exist_ok=True)
        tmp = self.relay_state_file.with_suffix(self.relay_state_file.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.relay_state, f, indent=2)
            f.write("\n")
        os.replace(tmp, self.relay_state_file)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        return len(self.encoding.encode(text))

    def _get_new_messages(self, agent_name: str) -> list[str]:
        """Get new messages from agent log since last relay"""
        log_file = self.agents[agent_name]["log"]

        if not log_file.exists():
            return []

        # Get current state for this agent
        agent_state = self.relay_state.get(agent_name, {})
        last_offset = int(agent_state.get("last_offset", 0) or 0)
        remainder = str(agent_state.get("remainder", "") or "")

        # Backward-compatible migration from line-count cursor.
        if "last_offset" not in agent_state and "last_line_count" in agent_state:
            last_line_count = int(agent_state.get("last_line_count", 0) or 0)
            try:
                with open(log_file, encoding="utf-8") as f:
                    lines = f.readlines()
                capped = max(0, min(last_line_count, len(lines)))
                last_offset = len("".join(lines[:capped]).encode("utf-8"))
            except Exception:
                last_offset = 0

        try:
            new_lines, next_offset, next_remainder = tail_text_lines(
                log_file,
                offset=last_offset,
                remainder=remainder,
            )
        except Exception as e:
            print(f"⚠️  Error reading {log_file}: {e}")
            return []

        # Filter out empty lines and clean up
        new_messages = []
        for line in new_lines:
            line = line.strip()
            if line and not line.startswith("//"):  # Skip comments
                new_messages.append(line)

        # Update state and track tokens
        next_state = {
            "last_offset": next_offset,
            "remainder": next_remainder,
            "messages_processed": agent_state.get("messages_processed", 0),
            "total_tokens": agent_state.get("total_tokens", 0),
            "last_processed_time": agent_state.get("last_processed_time", ""),
        }
        if new_messages:
            total_tokens = sum(self.count_tokens(msg) for msg in new_messages)

            next_state["last_processed_time"] = utc_now_iso()
            next_state["messages_processed"] = (
                int(agent_state.get("messages_processed", 0) or 0) + len(new_messages)
            )
            next_state["total_tokens"] = (
                int(agent_state.get("total_tokens", 0) or 0) + total_tokens
            )

            # Log to database
            self._log_agent_activity(agent_name, new_messages, total_tokens)

        self.relay_state[agent_name] = next_state

        return new_messages

    def _log_agent_activity(self, agent_name: str, messages: list[str], tokens: int):
        """Log agent activity to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for message in messages:
            cursor.execute(
                """
                INSERT INTO agent_activity (agent_name, message, tokens, timestamp)
                VALUES (?, ?, ?, ?)
            """,
                (
                    agent_name,
                    message,
                    self.count_tokens(message),
                    datetime.now().isoformat(),
                ),
            )

        conn.commit()
        conn.close()

    def _relay_to_all_other_agents(self, source_agent: str, messages: list[str]) -> int:
        """Relay messages to all other agents' queues"""
        if not messages:
            return 0

        timestamp = datetime.now().strftime("%H:%M:%S")
        relayed_count = 0

        for target_agent, agent_info in self.agents.items():
            if target_agent == source_agent:
                continue  # Don't relay to self

            queue_file = agent_info["queue"]

            try:
                for message in messages:
                    # Format: [timestamp] source_agent: message
                    relay_message = f"[{timestamp}] {source_agent}: {message}"
                    append_text_line(queue_file, relay_message)
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
        except Exception:
            return "unknown"

    def save_context_package(
        self,
        task_id: str,
        summary: str,
        code: str = "",
        issues: list[str] | None = None,
        commit_ref: str = "",
    ):
        """Save context package to database"""
        if issues is None:
            issues = []

        context_data = {"summary": summary, "code": code, "issues": issues}

        tokens = self.count_tokens(json.dumps(context_data))

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO context (task_id, summary, code, issues, commit_ref, timestamp, tokens)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                task_id,
                summary,
                code,
                json.dumps(issues),
                commit_ref,
                datetime.now().isoformat(),
                tokens,
            ),
        )

        conn.commit()
        conn.close()

        print(f"💾 Saved context package '{task_id}' ({tokens} tokens)")
        return tokens

    def summarize_agent_history(
        self, agent_name: str, max_tokens: int = 1000
    ) -> str | None:
        """Summarize agent history when approaching token limits"""
        # Get recent messages from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT message, timestamp FROM agent_activity
            WHERE agent_name = ?
            ORDER BY timestamp DESC
            LIMIT 50
        """,
            (agent_name,),
        )

        messages = cursor.fetchall()
        conn.close()

        if not messages:
            return None

        # Combine messages into history
        history = "\n".join([f"{ts}: {msg}" for msg, ts in reversed(messages)])
        history_tokens = self.count_tokens(history)

        # Check if summarization is needed
        if history_tokens > self.summarization_threshold * self.context_window:
            print(
                f"📊 {agent_name} history: {history_tokens} tokens (threshold: {int(self.summarization_threshold * self.context_window)})"
            )

            # Simple summarization (you can replace with Gemini API call)
            summary = self._create_simple_summary(agent_name, history, max_tokens)

            # Save as context package
            task_id = f"{agent_name}_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.save_context_package(task_id, summary, "", [], "")

            return summary

        return None

    def _create_simple_summary(
        self, agent_name: str, history: str, max_tokens: int
    ) -> str:
        """Create a simple summary (placeholder for Gemini API integration)"""
        lines = history.split("\n")

        # Extract key themes and recent activity
        recent_activity = lines[-10:] if len(lines) > 10 else lines

        summary = f"Agent {agent_name} Summary:\n"
        summary += f"- Total messages: {len(lines)}\n"
        summary += f"- Recent activity: {len(recent_activity)} messages\n"
        summary += f"- Time span: {lines[0][:19] if lines else 'N/A'} to {lines[-1][:19] if lines else 'N/A'}\n"
        summary += "\nRecent key messages:\n"

        for msg in recent_activity[-5:]:
            if len(msg) > 100:
                msg = msg[:97] + "..."
            summary += f"- {msg}\n"

        return summary

    def relay_cycle(self) -> dict[str, int]:
        """Single relay cycle - check all agents and relay new messages"""
        cycle_stats = {
            "agents_checked": 0,
            "messages_found": 0,
            "messages_relayed": 0,
            "active_agents": 0,
            "summaries_created": 0,
        }

        print(
            f"🔄 Enhanced relay cycle started at {datetime.now().strftime('%H:%M:%S')}"
        )

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

                # Check if summarization is needed
                summary = self.summarize_agent_history(agent_name)
                if summary:
                    cycle_stats["summaries_created"] += 1

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
        print("\n" + "=" * 60)
        print("📊 ENHANCED KOR'TANA RELAY STATUS")
        print("=" * 60)

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
            total_tokens = agent_state.get("total_tokens", 0)
            last_time = agent_state.get("last_processed_time", "never")

            print(
                f"{emoji} {agent_name:8} | {status:8} | {msg_count:3} msgs | {total_tokens:6} tokens | last: {last_time}"
            )

        # Database stats
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM context")
        context_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM agent_activity")
        activity_count = cursor.fetchone()[0]

        conn.close()

        print("=" * 60)
        print(
            f"💾 Database: {context_count} context packages, {activity_count} activity records"
        )
        print("=" * 60)

    def run_loop(self, interval: int = 2):
        """Run continuous relay loop"""
        print(f"🚀 Starting enhanced autonomous relay loop (interval: {interval}s)")
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
                        f"✅ Cycle {cycle_count}: {stats['messages_found']} found, {stats['messages_relayed']} relayed, {stats['summaries_created']} summaries"
                    )
                elif cycle_count % 30 == 0:  # Show heartbeat every minute
                    print(
                        f"💓 Cycle {cycle_count}: Monitoring {stats['agents_checked']} agents, {stats['active_agents']} active"
                    )

                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n🛑 Enhanced relay loop stopped after {cycle_count} cycles")
            self.print_status()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced Kor'tana Autonomous Relay System"
    )
    parser.add_argument("--loop", action="store_true", help="Run continuous relay loop")
    parser.add_argument(
        "--interval", type=int, default=2, help="Loop interval in seconds"
    )
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument(
        "--summarize", action="store_true", help="Trigger summarization for all agents"
    )

    args = parser.parse_args()

    # Initialize enhanced relay system
    relay = KortanaEnhancedRelay()

    if args.status:
        relay.print_status()
    elif args.summarize:
        print("📝 Triggering summarization for all agents...")
        for agent_name in relay.agents.keys():
            summary = relay.summarize_agent_history(agent_name)
            if summary:
                print(f"✅ Created summary for {agent_name}")
            else:
                print(f"ℹ️  No summarization needed for {agent_name}")
    elif args.loop:
        relay.run_loop(args.interval)
    else:
        # Single cycle
        print("🔄 Running single enhanced relay cycle...")
        stats = relay.relay_cycle()
        print(
            f"✅ Complete: {stats['messages_found']} found, {stats['messages_relayed']} relayed, {stats['summaries_created']} summaries"
        )
        relay.print_status()


if __name__ == "__main__":
    main()
