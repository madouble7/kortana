#!/usr/bin/env python3
"""
Agent Handoff Manager
====================

Monitors token usage and triggers agent handoffs when context window fills up.
Implements the complete handoff procedure with context package creation.

Usage:
    python handoff.py --monitor          # Monitor and trigger handoffs
    python handoff.py --handoff AGENT    # Force handoff for specific agent
    python handoff.py --status           # Show handoff status
"""

import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

try:
    from relays.protocol import append_text_line
except ModuleNotFoundError:
    from protocol import append_text_line


class AgentHandoffManager:
    """Manages agent handoffs and context package transfers"""

    def __init__(self, project_root: str | None = None):
        """Initialize handoff manager"""
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent
        )
        self.db_path = self.project_root / "kortana.db"
        self.logs_dir = self.project_root / "logs"
        self.queues_dir = self.project_root / "queues"
        self.handoff_log = self.project_root / "logs" / "handoffs.log"

        # Handoff settings
        self.context_window = 128000
        self.handoff_threshold = 0.8  # 80% = 102,400 tokens

        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        for dir_path in [self.logs_dir, self.queues_dir]:
            dir_path.mkdir(exist_ok=True)

    def _log_handoff(self, message: str):
        """Log handoff events"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} | {message}"
        append_text_line(self.handoff_log, log_entry)

        print(f"📝 {message}")

    def get_agent_token_usage(self, agent_name: str) -> dict[str, int]:
        """Calculate total token usage for an agent (S + T + H + O)"""
        # S = System/Summary tokens from context packages
        # T = Task tokens from current queue
        # H = History tokens from recent messages
        # O = Output tokens from responses

        tokens = {"system": 0, "task": 0, "history": 0, "output": 0, "total": 0}

        try:
            # Get system tokens from context packages
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(tokens) FROM context WHERE task_id LIKE ?",
                (f"{agent_name}_%",),
            )
            result = cursor.fetchone()
            tokens["system"] = result[0] if result[0] else 0
            conn.close()

            # Get task tokens from queue
            queue_file = self.queues_dir / f"{agent_name}_in.txt"
            if queue_file.exists():
                with open(queue_file, encoding="utf-8") as f:
                    queue_content = f.read()
                tokens["task"] = len(queue_content) // 4  # Rough estimate

            # Get history tokens from log
            log_file = self.logs_dir / f"{agent_name}.log"
            if log_file.exists():
                with open(log_file, encoding="utf-8") as f:
                    log_content = f.read()
                tokens["history"] = len(log_content) // 4  # Rough estimate

            # Output tokens (approximated from recent activity)
            tokens["output"] = tokens["history"] // 2  # Assume 50% output ratio

            tokens["total"] = sum(
                [tokens["system"], tokens["task"], tokens["history"], tokens["output"]]
            )

        except Exception as e:
            print(f"⚠️  Error calculating tokens for {agent_name}: {e}")

        return tokens

    def check_handoff_needed(self, agent_name: str) -> bool:
        """Check if agent needs handoff based on token usage"""
        tokens = self.get_agent_token_usage(agent_name)
        threshold = int(self.context_window * self.handoff_threshold)

        if tokens["total"] > threshold:
            self._log_handoff(
                f"🚨 Handoff needed for {agent_name}: {tokens['total']}/{self.context_window} tokens ({tokens['total'] / self.context_window * 100:.1f}%)"
            )
            return True

        return False

    def create_context_package(self, agent_name: str) -> str | None:
        """Create context package for agent handoff"""
        try:
            # Read agent history
            log_file = self.logs_dir / f"{agent_name}.log"
            if not log_file.exists():
                return None

            with open(log_file, encoding="utf-8") as f:
                history = f.read()

            # Create task ID
            task_id = f"{agent_name}_handoff_{int(time.time())}"

            # For now, use simple truncation (in production, use Gemini summarization)
            if len(history) > 4000:  # ~1000 tokens
                summary = history[-4000:]  # Keep recent history
                summary = (
                    f"[HANDOFF SUMMARY]\nRecent activity for {agent_name}:\n{summary}"
                )
            else:
                summary = history

            # Save context package
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO context (task_id, summary, code, issues, commit_ref, timestamp, tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task_id,
                    summary,
                    "",  # code
                    "[]",  # issues
                    "",  # commit_ref
                    datetime.utcnow().isoformat(),
                    len(summary) // 4,  # rough token count
                ),
            )
            conn.commit()
            conn.close()

            self._log_handoff(f"💾 Created context package: {task_id}")
            return task_id

        except Exception as e:
            print(f"⚠️  Error creating context package for {agent_name}: {e}")
            return None

    def spin_up_new_agent(self, agent_name: str, context_package_id: str) -> bool:
        """Spin up new agent with context package"""
        try:
            # Get context package
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM context WHERE task_id = ?", (context_package_id,)
            )
            context = cursor.fetchone()
            conn.close()

            if not context:
                print(f"⚠️  Context package {context_package_id} not found")
                return False

            # Create initialization prompt
            task_id, summary, code, issues, commit_ref, timestamp, tokens = context
            prompt = f"""Task Handoff for {agent_name}
Timestamp: {timestamp}
Context: {summary}
Code: {code}
Issues: {issues}
Commit: {commit_ref}

Continue from where the previous agent left off."""

            # Write to agent queue
            queue_file = self.queues_dir / f"{agent_name}_in.txt"
            with open(queue_file, "w", encoding="utf-8") as f:
                f.write(f"[HANDOFF] {prompt}\n")

            # Clear agent log (fresh start)
            log_file = self.logs_dir / f"{agent_name}.log"
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | [HANDOFF] Agent restarted with context package {context_package_id}\n"
                )

            self._log_handoff(
                f"🚀 New {agent_name} agent started with context {context_package_id}"
            )
            return True

        except Exception as e:
            print(f"⚠️  Error spinning up new agent for {agent_name}: {e}")
            return False

    def perform_handoff(self, agent_name: str) -> bool:
        """Complete handoff procedure for an agent"""
        self._log_handoff(f"🔄 Starting handoff procedure for {agent_name}")

        # Step 1: Create context package
        context_package_id = self.create_context_package(agent_name)
        if not context_package_id:
            self._log_handoff(f"❌ Failed to create context package for {agent_name}")
            return False

        # Step 2: Spin up new agent
        if not self.spin_up_new_agent(agent_name, context_package_id):
            self._log_handoff(f"❌ Failed to start new agent for {agent_name}")
            return False

        # Step 3: Update task queue (placeholder - would integrate with Redis in production)
        self._update_task_queue(agent_name, context_package_id)

        self._log_handoff(f"✅ Handoff completed for {agent_name}")
        return True

    def _update_task_queue(self, agent_name: str, context_package_id: str):
        """Update task queue (placeholder for Redis integration)"""
        # In production, this would push to Redis:
        # redis-cli LPUSH tasks f"{agent_name}:{context_package_id}"

        task_file = self.project_root / "data" / "task_queue.json"
        task_file.parent.mkdir(exist_ok=True)

        try:
            if task_file.exists():
                with open(task_file, encoding="utf-8") as f:
                    tasks = json.load(f)
            else:
                tasks = []

            tasks.append(
                {
                    "agent": agent_name,
                    "context_package": context_package_id,
                    "timestamp": datetime.now().isoformat(),
                    "status": "pending",
                }
            )

            tmp = task_file.with_suffix(task_file.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=2)
                f.write("\n")
            os.replace(tmp, task_file)

        except Exception as e:
            print(f"⚠️  Error updating task queue: {e}")

    def monitor_agents(self) -> list[str]:
        """Monitor all agents and return list of agents needing handoff"""
        agents_needing_handoff = []

        # Discover agents
        log_files = list(self.logs_dir.glob("*.log"))
        agent_names = [f.stem for f in log_files if f.stem != "handoffs"]

        print(f"🔍 Monitoring {len(agent_names)} agents for handoff triggers...")

        for agent_name in agent_names:
            if self.check_handoff_needed(agent_name):
                agents_needing_handoff.append(agent_name)

        return agents_needing_handoff

    def print_status(self):
        """Print handoff status for all agents"""
        print("\n" + "=" * 60)
        print("🔄 AGENT HANDOFF STATUS")
        print("=" * 60)

        log_files = list(self.logs_dir.glob("*.log"))
        agent_names = [f.stem for f in log_files if f.stem != "handoffs"]

        for agent_name in agent_names:
            tokens = self.get_agent_token_usage(agent_name)
            threshold = int(self.context_window * self.handoff_threshold)
            percentage = (tokens["total"] / self.context_window) * 100

            status = "🟢 OK"
            if tokens["total"] > threshold:
                status = "🚨 HANDOFF NEEDED"
            elif tokens["total"] > threshold * 0.7:
                status = "🟡 APPROACHING"

            print(
                f"{status:15} | {agent_name:10} | {tokens['total']:6}/{self.context_window} tokens ({percentage:5.1f}%)"
            )

        # Show recent handoffs
        if self.handoff_log.exists():
            print("\n📝 Recent handoffs:")
            try:
                with open(self.handoff_log, encoding="utf-8") as f:
                    lines = f.readlines()
                for line in lines[-5:]:  # Last 5 handoff events
                    print(f"   {line.strip()}")
            except Exception:
                pass

        print("=" * 60)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Agent Handoff Manager")
    parser.add_argument(
        "--monitor", action="store_true", help="Monitor agents and trigger handoffs"
    )
    parser.add_argument("--handoff", type=str, help="Force handoff for specific agent")
    parser.add_argument("--status", action="store_true", help="Show handoff status")
    parser.add_argument(
        "--interval", type=int, default=60, help="Monitoring interval in seconds"
    )

    args = parser.parse_args()

    manager = AgentHandoffManager()

    if args.status:
        manager.print_status()
    elif args.handoff:
        success = manager.perform_handoff(args.handoff)
        if success:
            print(f"✅ Handoff completed for {args.handoff}")
        else:
            print(f"❌ Handoff failed for {args.handoff}")
    elif args.monitor:
        print(f"🚀 Starting agent handoff monitoring (interval: {args.interval}s)")
        print("📢 Press Ctrl+C to stop")

        try:
            while True:
                agents_to_handoff = manager.monitor_agents()

                for agent_name in agents_to_handoff:
                    print(f"🔄 Triggering handoff for {agent_name}")
                    manager.perform_handoff(agent_name)

                if not agents_to_handoff:
                    print(
                        f"💓 All agents within limits ({datetime.now().strftime('%H:%M:%S')})"
                    )

                time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\n🛑 Handoff monitoring stopped")
            manager.print_status()
    else:
        print("Use --monitor, --handoff AGENT, or --status")


if __name__ == "__main__":
    main()
