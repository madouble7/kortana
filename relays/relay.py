"""
Relay Script with Gemini Integration
===================================

Adapted from your existing autonomous_relay.py to include:
- Gemini 2.0 Flash summarization
- Context package creation
- Token monitoring and handoff management
- Database persistence

Usage:
    python relay.py                    # Single cycle
    python relay.py --loop             # Continuous monitoring
    python relay.py --summarize        # Force summarization
    python relay.py --handoff AGENT    # Trigger agent handoff
"""

import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import tiktoken

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv not installed, continue without it
    pass

# Try to import Gemini (graceful fallback if not installed)
try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("[WARNING] google-generativeai not installed. Using mock summarization.")


class KortanaRelay:
    """Enhanced relay with Gemini integration and context management"""

    def __init__(
        self, project_root: Optional[str] = None, gemini_api_key: Optional[str] = None
    ):
        """Initialize relay with Gemini integration"""
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent
        )
        self.logs_dir = self.project_root / "logs"
        self.queues_dir = self.project_root / "queues"
        self.relay_state_file = self.project_root / "data" / "relay_state.json"
        self.db_path = self.project_root / "kortana.db"

        # Context window settings (Gemini 2.0 Flash has 1M+ tokens)
        self.context_window = 128000  # Conservative 128K limit
        self.handoff_threshold = 0.8  # 80% of context window

        # Initialize database
        self._init_database()  # Set up Gemini - check both GEMINI_API_KEY and GOOGLE_API_KEY
        self.gemini_api_key = (
            gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        )

        if self.gemini_api_key and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
                print(
                    f"[AI] Gemini 2.0 Flash configured (key: {self.gemini_api_key[:10]}...)"
                )
            except Exception as e:
                print(f"[ERROR] Failed to configure Gemini: {e}")
                self.model = None
        else:
            self.model = None
            if not self.gemini_api_key:
                print("[WARNING] No Gemini API key found - using mock summarization")
                print("[INFO] Set GOOGLE_API_KEY or GEMINI_API_KEY in .env file")
            else:
                print(
                    "[WARNING] google-generativeai not available - using mock summarization"
                )

        # Load state and discover agents
        self.relay_state = self._load_relay_state()
        self.agents = self._discover_agents()

        print("[RELAY] Enhanced Kor'tana Relay initialized")
        print(f"[LOGS] {self.logs_dir}")
        print(f"[QUEUES] {self.queues_dir}")
        print(f"[DATABASE] {self.db_path}")
        print(f"[AGENTS] {list(self.agents.keys())}")

    def _init_database(self):
        """Initialize SQLite database for context packages"""
        self.db_path.parent.mkdir(exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
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
        conn.commit()
        conn.close()

    def count_tokens(self, text: str, encoding_name: str = "cl100k_base") -> int:
        """Count tokens in text using tiktoken"""
        try:
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(text))
        except Exception:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

    def summarize_with_gemini(self, history: str, max_tokens: int = 1000) -> str:
        """Summarize text using Gemini 2.0 Flash"""
        if not self.model:
            # Mock summarization for testing
            return f"[MOCK SUMMARY] {history[:200]}... (original: {len(history)} chars, target: {max_tokens} tokens)"

        try:
            prompt = f"""Summarize the following agent conversation history to approximately {max_tokens} tokens.
            Focus on:
            - Key decisions and actions taken
            - Current task status and progress
            - Important context needed for handoff
            - Unresolved issues or blockers

            History:
            {history}

            Provide a concise summary suitable for agent handoff:"""

            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            print(f"[WARNING] Gemini summarization failed: {e}")
            return f"[FALLBACK SUMMARY] {history[:500]}..."

    def save_context_package(
        self,
        task_id: str,
        summary: str,
        code: str = "",
        issues: List[str] = None,
        commit_ref: str = "",
    ) -> int:
        """Save context package to database"""
        issues = issues or []
        package_data = {"summary": summary, "code": code, "issues": issues}

        tokens = self.count_tokens(json.dumps(package_data))

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO context
            (task_id, summary, code, issues, commit_ref, timestamp, tokens)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                task_id,
                summary,
                code,
                json.dumps(issues),
                commit_ref,
                datetime.utcnow().isoformat(),
                tokens,
            ),
        )
        conn.commit()
        conn.close()

        print(f"[SAVED] Context package '{task_id}' ({tokens} tokens)")
        return tokens

    def relay_context(self, task: Dict[str, Any], history: str) -> str:
        """Main context relay logic - checks if summarization needed"""
        history_tokens = self.count_tokens(history)
        threshold_tokens = int(self.context_window * self.handoff_threshold)

        print(
            f"[TOKENS] Usage: {history_tokens}/{self.context_window} ({history_tokens / self.context_window * 100:.1f}%)"
        )

        if history_tokens > threshold_tokens:
            print("[ALERT] Token threshold exceeded! Triggering summarization...")

            # Summarize history
            summary = self.summarize_with_gemini(history, max_tokens=1000)

            # Save context package
            tokens_saved = self.save_context_package(
                task_id=task.get("id", f"task_{int(time.time())}"),
                summary=summary,
                code=task.get("code", ""),
                issues=task.get("issues", []),
                commit_ref=task.get("commit_ref", ""),
            )

            print(f"[OK] Context compressed: {history_tokens} -> {tokens_saved} tokens")
            return summary

        return history

    def _discover_agents(self) -> Dict[str, Dict[str, Path]]:
        """Auto-discover agents from log and queue files"""
        agents = {}
        log_files = list(self.logs_dir.glob("*.log"))

        for log_file in log_files:
            agent_name = log_file.stem
            queue_file = self.queues_dir / f"{agent_name}_in.txt"

            agents[agent_name] = {
                "log": log_file,
                "queue": queue_file,
                "status": "discovered",
            }

            queue_file.parent.mkdir(exist_ok=True)
            queue_file.touch(exist_ok=True)

        return agents

    def _load_relay_state(self) -> Dict[str, Any]:
        """Load relay state"""
        if self.relay_state_file.exists():
            try:
                with open(self.relay_state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}

    def _save_relay_state(self):
        """Save relay state"""
        self.relay_state_file.parent.mkdir(exist_ok=True)
        with open(self.relay_state_file, "w") as f:
            json.dump(self.relay_state, f, indent=2)

    def _get_new_messages(self, agent_name: str) -> List[str]:
        """Get new messages from agent log"""
        log_file = self.agents[agent_name]["log"]
        if not log_file.exists():
            return []

        agent_state = self.relay_state.get(agent_name, {})
        last_line_count = agent_state.get("last_line_count", 0)

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"[WARNING] Error reading {log_file}: {e}")
            return []

        new_lines = lines[last_line_count:]
        new_messages = [
            line.strip()
            for line in new_lines
            if line.strip() and not line.startswith("//")
        ]

        if new_messages:
            self.relay_state[agent_name] = {
                "last_line_count": len(lines),
                "last_processed_time": datetime.now().isoformat(),
                "messages_processed": agent_state.get("messages_processed", 0)
                + len(new_messages),
            }

        return new_messages

    def _relay_to_all_other_agents(self, source_agent: str, messages: List[str]) -> int:
        """Relay messages to other agents"""
        if not messages:
            return 0

        timestamp = datetime.now().strftime("%H:%M:%S")
        relayed_count = 0

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

                print(
                    f"[RELAY] {source_agent} -> {target_agent}: {len(messages)} messages"
                )
            except Exception as e:
                print(f"[WARNING] Error writing to {queue_file}: {e}")

        return relayed_count

    def relay_cycle(self) -> Dict[str, int]:
        """Single relay cycle with context management"""
        cycle_stats = {
            "agents_checked": 0,
            "messages_found": 0,
            "messages_relayed": 0,
            "active_agents": 0,
            "context_packages_created": 0,
        }

        print(f"[CYCLE] Enhanced relay cycle at {datetime.now().strftime('%H:%M:%S')}")

        for agent_name in self.agents.keys():
            cycle_stats["agents_checked"] += 1

            # Get new messages
            new_messages = self._get_new_messages(agent_name)

            if new_messages:
                cycle_stats["messages_found"] += len(new_messages)
                print(f"[MESSAGES] {agent_name}: {len(new_messages)} new messages")

                # Check if context relay needed
                history = "\n".join(new_messages)
                task = {
                    "id": f"{agent_name}_{int(time.time())}",
                    "code": "",
                    "issues": [],
                    "commit_ref": "",
                }

                processed_history = self.relay_context(task, history)
                if processed_history != history:
                    cycle_stats["context_packages_created"] += 1

                # Relay to other agents
                relayed = self._relay_to_all_other_agents(agent_name, new_messages)
                cycle_stats["messages_relayed"] += relayed

        self._save_relay_state()
        return cycle_stats

    def print_status(self):
        """Print system status including database info"""
        print("\n" + "=" * 60)
        print("[STATUS] KOR'TANA ENHANCED RELAY STATUS")
        print("=" * 60)

        # Agent status
        for agent_name, agent_info in self.agents.items():
            status = agent_info.get("status", "unknown")
            status_indicators = {
                "active": "[ACTIVE]",
                "idle": "[IDLE]",
                "inactive": "[INACTIVE]",
                "discovered": "[DISCOVERED]",
            }
            indicator = status_indicators.get(status, "[UNKNOWN]")

            agent_state = self.relay_state.get(agent_name, {})
            msg_count = agent_state.get("messages_processed", 0)
            last_time = agent_state.get("last_processed_time", "never")

            print(
                f"{indicator} {agent_name:10} | {status:8} | {msg_count:3} msgs | {last_time}"
            )

        # Database status
        print("\n[DATABASE] DATABASE STATUS")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(tokens) FROM context")
            count, total_tokens = cursor.fetchone()
            conn.close()

            print(f"   Context packages: {count}")
            print(f"   Total tokens saved: {total_tokens or 0}")
        except Exception as e:
            print(f"   Database error: {e}")

        print("=" * 60)

    def run_loop(self, interval: int = 5):
        """Run continuous relay loop with context management"""
        print(f"[START] Enhanced relay loop starting (interval: {interval}s)")
        print("[INFO] Set GEMINI_API_KEY environment variable for AI summarization")
        print("[INFO] Press Ctrl+C to stop")

        cycle_count = 0

        try:
            while True:
                cycle_count += 1
                stats = self.relay_cycle()

                if cycle_count % 10 == 0:
                    self.print_status()

                if stats["messages_found"] > 0:
                    print(
                        f"[OK] Cycle {cycle_count}: {stats['messages_found']} found, {stats['messages_relayed']} relayed, {stats['context_packages_created']} summarized"
                    )
                elif cycle_count % 30 == 0:
                    print(
                        f"[HEARTBEAT] Cycle {cycle_count}: Monitoring {stats['agents_checked']} agents"
                    )

                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n[STOP] Enhanced relay stopped after {cycle_count} cycles")
            self.print_status()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced Kor'tana Relay with Gemini Integration"
    )
    parser.add_argument("--loop", action="store_true", help="Run continuous relay loop")
    parser.add_argument(
        "--interval", type=int, default=5, help="Loop interval in seconds"
    )
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument(
        "--summarize", action="store_true", help="Force summarization test"
    )
    parser.add_argument(
        "--api-key", type=str, help="Gemini API key (or set GEMINI_API_KEY env var)"
    )

    args = parser.parse_args()

    # Initialize enhanced relay
    relay = KortanaRelay(gemini_api_key=args.api_key)

    if args.status:
        relay.print_status()
    elif args.summarize:
        # Test summarization
        test_history = "Agent claude analyzed the system. Agent flash provided quick insights. Agent weaver coordinated the workflow."
        task = {
            "id": "test_summarization",
            "code": "def test(): pass",
            "issues": ["Add tests"],
        }
        result = relay.relay_context(task, test_history)
        print(f"[RESULT] Summarization test result:\n{result}")
    elif args.loop:
        relay.run_loop(args.interval)
    else:
        print("[INFO] Running single enhanced relay cycle...")
        stats = relay.relay_cycle()
        print(
            f"[COMPLETE] {stats['messages_found']} found, {stats['messages_relayed']} relayed, {stats['context_packages_created']} summarized"
        )
        relay.print_status()


if __name__ == "__main__":
    main()
