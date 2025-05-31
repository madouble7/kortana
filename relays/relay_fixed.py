#!/usr/bin/env python3
"""
Enhanced Kor'tana Relay with Chain Routing and Dashboard Integration
====================================================================

Integrated multi-stage AI chain with:
- Gemini 2.0 Flash for initialization and summarization
- GitHub Models for testing and validation
- OpenRouter for production scaling
- Dashboard logging and token monitoring
- Context package management

Usage:
    python relay.py --status        # System status
    python relay.py --route         # Test chain routing
    python relay.py --dashboard     # Monitoring dashboard
    python relay.py --summarize     # Force summarization
    python relay.py --loop          # Continuous monitoring
    python relay.py --handoff AGENT # Trigger agent handoff
"""

import argparse
import json
import os
import sqlite3
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests
import tiktoken

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Try to import Gemini
try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("[WARNING] google-generativeai not installed. Using mock summarization.")

# Load API keys
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
GITHUB_API_KEY = os.getenv("GITHUB_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# API Configuration
XAI_API_BASE = "https://api.x.ai/v1"
GITHUB_MODELS_BASE = "https://models.inference.ai.azure.com"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"


class EnhancedKortanaRelay:
    """Enhanced relay with multi-stage AI chain routing and monitoring integration"""

    def __init__(self, project_root: str = None):
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent
        )
        self.logs_dir = self.project_root / "logs"
        self.queues_dir = self.project_root / "queues"
        self.db_path = self.project_root / "kortana.db"
        self.data_dir = self.project_root / "data"

        # Create directories
        for directory in [self.logs_dir, self.queues_dir, self.data_dir]:
            directory.mkdir(exist_ok=True)

        # API Configuration
        self.gemini_api_key = GEMINI_API_KEY
        self.github_api_key = GITHUB_API_KEY
        self.openrouter_api_key = OPENROUTER_API_KEY

        # Initialize Gemini if available
        self.model = None
        if GENAI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
                print("[GEMINI] Initialized Gemini 2.0 Flash")
            except Exception as e:
                print(f"[GEMINI] Failed to initialize: {e}")
                self.model = None

        # Discover agents
        self.agents = self._discover_agents()

        # Initialize database
        self._init_database()

        # Initialize monitoring
        self.monitor = None
        try:
            from monitor import KortanaEnhancedMonitor

            self.monitor = KortanaEnhancedMonitor(str(self.project_root))
            print("[MONITOR] Enhanced monitoring initialized")
        except ImportError:
            try:
                # Try relative import from relays directory
                sys.path.append(str(self.project_root / "relays"))
                from monitor import KortanaEnhancedMonitor

                self.monitor = KortanaEnhancedMonitor(str(self.project_root))
                print("[MONITOR] Enhanced monitoring initialized")
            except ImportError:
                print("[MONITOR] Enhanced monitoring not available")

        print("[RELAY] Enhanced Kor'tana Relay initialized")
        print(f"[LOGS] {self.logs_dir}")
        print(f"[QUEUES] {self.queues_dir}")
        print(f"[DATABASE] {self.db_path}")
        print(f"[AGENTS] {list(self.agents.keys())}")

    def _init_database(self):
        """Initialize SQLite database for context packages and monitoring"""
        self.db_path.parent.mkdir(exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Context packages table
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

        # Token usage logging
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS token_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                stage TEXT,
                tokens INTEGER,
                timestamp TEXT,
                agent_name TEXT
            )
        """
        )

        # Chain routing logs
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chain_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                stage TEXT,
                tokens INTEGER,
                timestamp TEXT,
                agent_from TEXT,
                agent_to TEXT,
                status TEXT
            )
        """
        )

        # Rate limiting tracking
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT,
                requests_used INTEGER,
                tokens_used INTEGER,
                reset_time TEXT,
                timestamp TEXT
            )
        """
        )

        # Log processing state
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS log_processing_state (
                log_file_path TEXT PRIMARY KEY,
                last_processed_line_count INTEGER DEFAULT 0
            )
        """
        )

        conn.commit()
        conn.close()

    def _discover_agents(self) -> Dict[str, Dict]:
        """Discover agent log files and queues"""
        agents = {}

        if self.logs_dir.exists():
            for log_file in self.logs_dir.glob("*.log"):
                agent_name = log_file.stem
                queue_file = self.queues_dir / f"{agent_name}_queue.txt"

                agents[agent_name] = {
                    "log": log_file,
                    "queue": queue_file,
                    "messages_processed": 0,
                    "last_activity": None,
                }

        return agents

    def count_tokens(self, text: str, encoding_name: str = "cl100k_base") -> int:
        """Count tokens in text using tiktoken"""
        try:
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(text))
        except Exception:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

    def log_token_usage(
        self, task_id: str, stage: str, tokens: int, agent_name: str = "system"
    ):
        """Log token usage to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO token_log (task_id, stage, tokens, timestamp, agent_name)
                VALUES (?, ?, ?, ?, ?)
                """,
                (task_id, stage, tokens, datetime.now().isoformat(), agent_name),
            )
            conn.commit()
            conn.close()
            print(f"[TOKEN] Logged {tokens} tokens for {stage} stage")
        except Exception as e:
            print(f"[TOKEN] Error logging usage: {e}")

    def log_chain_routing(
        self,
        task_id: str,
        stage: str,
        agent_from: str,
        agent_to: str,
        tokens: int,
        status: str,
    ):
        """Log chain routing activity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chain_log (task_id, stage, tokens, timestamp, agent_from, agent_to, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    stage,
                    tokens,
                    datetime.now().isoformat(),
                    agent_from,
                    agent_to,
                    status,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[CHAIN] Error logging routing: {e}")

    def call_gemini_flash(self, prompt: str, max_tokens: int = 2000) -> str:
        """Call Gemini 2.0 Flash for initialization and summarization"""
        if not self.model:
            return f"[MOCK GEMINI] {prompt[:100]}... (mock response for {max_tokens} tokens)"

        try:
            response = self.model.generate_content(prompt)
            result = response.text if hasattr(response, "text") else str(response)

            # Log token usage
            tokens_used = self.count_tokens(prompt + result)
            self.log_token_usage(
                str(uuid.uuid4()), "gemini_flash", tokens_used, "gemini"
            )

            return result
        except Exception as e:
            print(f"[GEMINI] Error: {e}")
            return f"[GEMINI ERROR] {str(e)}"

    def call_github_models(self, prompt: str, model: str = "gpt-4o-mini") -> str:
        """Call GitHub Models API for testing and validation"""
        if not self.github_api_key:
            return "[FALLBACK] GitHub Models unavailable, using local processing"

        try:
            headers = {
                "Authorization": f"Bearer {self.github_api_key}",
                "Content-Type": "application/json",
            }

            data = {
                "messages": [{"role": "user", "content": prompt}],
                "model": model,
                "max_tokens": 1000,
            }

            response = requests.post(
                f"{GITHUB_MODELS_BASE}/chat/completions",
                headers=headers,
                json=data,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # Log token usage
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                self.log_token_usage(
                    str(uuid.uuid4()), "github_models", tokens_used, "github"
                )

                return content
            else:
                return f"[GITHUB ERROR] {response.status_code}: {response.text}"

        except Exception as e:
            print(f"[GITHUB] Error: {e}")
            return f"[GITHUB ERROR] {str(e)}"

    def call_openrouter(self, prompt: str, model: str = "openai/gpt-4") -> str:
        """Call OpenRouter for production scaling"""
        if not self.openrouter_api_key:
            return "[FALLBACK] OpenRouter unavailable, using local processing"

        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
            }

            data = {"model": model, "messages": [{"role": "user", "content": prompt}]}

            response = requests.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers=headers,
                json=data,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # Log token usage
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                self.log_token_usage(
                    str(uuid.uuid4()), "openrouter", tokens_used, "openrouter"
                )

                return content
            else:
                return f"[OPENROUTER ERROR] {response.status_code}: {response.text}"

        except Exception as e:
            print(f"[OPENROUTER] Error: {e}")
            return f"[OPENROUTER ERROR] {str(e)}"

    def route_task(self, task_description: str) -> Dict[str, Any]:
        """Route task through multi-stage AI chain"""
        task_id = str(uuid.uuid4())
        print(f"\n[CHAIN] Starting task routing: {task_id[:8]}")
        print(f"[TASK] {task_description}")

        results = {
            "task_id": task_id,
            "task_description": task_description,
            "stages": {},
            "total_tokens": 0,
        }

        # Stage 1: Initialization with Gemini 2.0 Flash
        print("\n[STAGE 1] Initialization with Gemini 2.0 Flash")
        init_prompt = f"""
        Task Analysis and Initialization:
        {task_description}

        Please provide:
        1. Task breakdown and approach
        2. Key considerations and requirements
        3. Recommended next steps
        4. Potential challenges to address
        """

        init_result = self.call_gemini_flash(init_prompt, 1500)
        init_tokens = self.count_tokens(init_prompt + init_result)
        results["stages"]["init"] = {
            "result": init_result,
            "tokens": init_tokens,
            "status": "completed",
        }
        results["total_tokens"] += init_tokens
        self.log_chain_routing(
            task_id, "init", "system", "gemini", init_tokens, "completed"
        )

        # Stage 2: Summarization with Gemini 2.0 Flash
        print("\n[STAGE 2] Summarization with Gemini 2.0 Flash")
        summary_prompt = f"""
        Summarize the following analysis into actionable insights:
        {init_result}

        Provide:
        1. Executive summary (2-3 sentences)
        2. Key action items
        3. Priority level assessment
        4. Resource requirements
        """

        summary_result = self.call_gemini_flash(summary_prompt, 1000)
        summary_tokens = self.count_tokens(summary_prompt + summary_result)
        results["stages"]["summarize"] = {
            "result": summary_result,
            "tokens": summary_tokens,
            "status": "completed",
        }
        results["total_tokens"] += summary_tokens
        self.log_chain_routing(
            task_id, "summarize", "gemini", "gemini", summary_tokens, "completed"
        )

        # Stage 3: Testing with GitHub Models
        print("\n[STAGE 3] Testing and validation with GitHub Models")
        test_prompt = f"""
        Review and validate this analysis:

        Original Task: {task_description}
        Analysis: {summary_result}

        Please:
        1. Identify any gaps or issues
        2. Suggest improvements
        3. Validate the approach
        4. Rate feasibility (1-10)
        """

        test_result = self.call_github_models(test_prompt)
        test_tokens = self.count_tokens(test_prompt + test_result)
        results["stages"]["test"] = {
            "result": test_result,
            "tokens": test_tokens,
            "status": "completed",
        }
        results["total_tokens"] += test_tokens
        self.log_chain_routing(
            task_id, "test", "gemini", "github", test_tokens, "completed"
        )

        # Stage 4: Production scaling (if needed)
        if results["total_tokens"] > 5000:  # High complexity task
            print("\n[STAGE 4] Production scaling with OpenRouter")
            production_prompt = f"""
            Scale this solution for production:

            Task: {task_description}
            Analysis: {summary_result}
            Validation: {test_result}

            Provide production-ready recommendations:
            1. Implementation plan
            2. Risk mitigation
            3. Performance considerations
            4. Monitoring strategy
            """

            production_result = self.call_openrouter(production_prompt)
            production_tokens = self.count_tokens(production_prompt + production_result)
            results["stages"]["production"] = {
                "result": production_result,
                "tokens": production_tokens,
                "status": "completed",
            }
            results["total_tokens"] += production_tokens
            self.log_chain_routing(
                task_id,
                "production",
                "github",
                "openrouter",
                production_tokens,
                "completed",
            )

        print("\n[CHAIN] Task routing completed")
        print(f"[TOKENS] Total used: {results['total_tokens']}")

        return results

    def _get_agent_new_messages(self, agent_name: str) -> tuple[int, List[str]]:
        """Get new messages from agent log and the current total line count."""
        log_file = self.agents[agent_name]["log"]
        new_messages = []
        current_total_lines = 0

        if not log_file.exists():
            return 0, []

        # Get last processed line count from DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT last_processed_line_count FROM log_processing_state WHERE log_file_path = ?",
            (str(log_file),),
        )
        result = cursor.fetchone()
        last_processed_line_count = result[0] if result else 0
        conn.close()

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            current_total_lines = len(lines)

            if current_total_lines > last_processed_line_count:
                for line_content in lines[last_processed_line_count:]:
                    stripped_line = line_content.strip()
                    if stripped_line and not stripped_line.startswith("//"):
                        new_messages.append(stripped_line)
        except Exception as e:
            print(f"⚠️  Error reading {log_file}: {e}")
            return (
                last_processed_line_count,
                [],
            )  # Return old count on error to avoid skipping lines

        return current_total_lines, new_messages

    def _update_log_processing_state(self, log_file_path: Path, new_line_count: int):
        """Update the last processed line count for a log file in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO log_processing_state (log_file_path, last_processed_line_count) VALUES (?, ?)",
            (str(log_file_path), new_line_count),
        )
        conn.commit()
        conn.close()

    def _relay_messages(self, source_agent: str, messages: List[str]) -> int:
        """Relay messages to other agents and log activity"""
        relayed_count = 0

        for message in messages:
            # Simple round-robin relay (can be enhanced with smart routing)
            for target_agent in self.agents.keys():
                if target_agent != source_agent:
                    queue_file = self.agents[target_agent]["queue"]

                    try:
                        with open(queue_file, "a", encoding="utf-8") as f:
                            f.write(
                                f"[{datetime.now().isoformat()}] From {source_agent}: {message}\n"
                            )
                        relayed_count += 1
                    except Exception as e:
                        print(f"⚠️  Error writing to {queue_file}: {e}")

        return relayed_count

    def summarize_with_gemini(self, history: str, max_tokens: int = 1000) -> str:
        """Summarize text using Gemini 2.0 Flash"""
        if not self.model:
            # Mock summarization for testing
            return f"[MOCK SUMMARY] {history[:200]}... (original: {len(history)} chars, target: {max_tokens} tokens)"

        prompt = f"""Summarize the following agent conversation history to approximately {max_tokens} tokens.
        Focus on:
        - Key decisions and actions taken
        - Current task status and progress
        - Important context needed for handoff
        - Unresolved issues or blockers

        History to summarize:
        {history}

        Provide a concise but comprehensive summary that maintains context continuity."""

        try:
            response = self.model.generate_content(prompt)
            summary = response.text if hasattr(response, "text") else str(response)

            # Log token usage
            tokens_used = self.count_tokens(prompt + summary)
            self.log_token_usage(str(uuid.uuid4()), "summarize", tokens_used, "gemini")

            return summary
        except Exception as e:
            print(f"[GEMINI] Summarization error: {e}")
            return f"[SUMMARIZATION ERROR] {str(e)}"

    def create_context_package(
        self,
        summary: str,
        code: str = "",
        issues: List[str] = None,
        commit_ref: str = "",
    ) -> str:
        """Create a context package and store in database"""
        if issues is None:
            issues = []

        task_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Calculate total tokens
        total_text = f"{summary} {code} {' '.join(issues)}"
        total_tokens = self.count_tokens(total_text)

        # Store in database
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
                code,
                json.dumps(issues),
                commit_ref,
                timestamp,
                total_tokens,
            ),
        )
        conn.commit()
        conn.close()

        print(f"[CONTEXT] Created package {task_id[:8]} ({total_tokens} tokens)")
        return task_id

    def relay_cycle(self) -> Dict[str, Any]:
        """Execute one relay cycle"""
        cycle_start = datetime.now()
        cycle_stats = {
            "cycle_start": cycle_start.isoformat(),
            "agents_checked": 0,
            "messages_found": 0,
            "messages_relayed": 0,
            "errors": 0,
        }

        print(f"\n🔄 [RELAY CYCLE] {cycle_start.strftime('%H:%M:%S')}")

        # Check each agent for new messages
        for agent_name in self.agents.keys():
            cycle_stats["agents_checked"] += 1

            # Get new messages
            current_total_lines, new_messages = self._get_agent_new_messages(agent_name)

            if new_messages:
                cycle_stats["messages_found"] += len(new_messages)
                print(f"📨 {agent_name}: {len(new_messages)} new messages")

                try:
                    # Relay messages
                    relayed = self._relay_messages(agent_name, new_messages)
                    cycle_stats["messages_relayed"] += relayed

                    # Update processed line count in DB only after successful relay
                    self._update_log_processing_state(
                        self.agents[agent_name]["log"], current_total_lines
                    )

                    # Update agent stats
                    self.agents[agent_name]["messages_processed"] += len(new_messages)
                    self.agents[agent_name]["last_activity"] = (
                        datetime.now().isoformat()
                    )

                except Exception as e:
                    print(
                        f"⚠️ Error relaying messages for {agent_name} or updating state: {e}"
                    )
                    cycle_stats["errors"] += 1

        # Save relay state
        state_file = self.data_dir / "relay_state.json"
        try:
            with open(state_file, "w") as f:
                json.dump(self.agents, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️  Error saving relay state: {e}")

        cycle_stats["cycle_duration"] = (datetime.now() - cycle_start).total_seconds()

        if cycle_stats["messages_found"] > 0:
            print(
                f"✅ Cycle complete: {cycle_stats['messages_relayed']} messages relayed"
            )

        return cycle_stats

    def print_status(self):
        """Print current relay status"""
        print("\n" + "=" * 60)
        print("🤖 ENHANCED KOR'TANA RELAY STATUS")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # API Status
        status_indicators = {"available": "🟢", "unavailable": "🔴", "unknown": "⚪"}

        print("\n🔗 API CONNECTIONS:")
        gemini_status = "available" if self.model else "unavailable"
        github_status = "available" if self.github_api_key else "unavailable"
        openrouter_status = "available" if self.openrouter_api_key else "unavailable"

        print(
            f"   {status_indicators[gemini_status]} Gemini 2.0 Flash: {gemini_status}"
        )
        print(f"   {status_indicators[github_status]} GitHub Models: {github_status}")
        print(
            f"   {status_indicators[openrouter_status]} OpenRouter: {openrouter_status}"
        )

        # Agent Status
        print(f"\n🤖 AGENT NETWORK ({len(self.agents)} agents):")
        for agent_name, info in self.agents.items():
            messages = info.get("messages_processed", 0)
            last_activity = info.get("last_activity", "never")
            if last_activity != "never":
                last_activity = last_activity[:19]  # Trim timestamp
            print(f"   📋 {agent_name:15} | {messages:4} msgs | Last: {last_activity}")

        # Database Status
        if self.db_path.exists():
            db_size = self.db_path.stat().st_size
            print(f"\n💾 DATABASE: {db_size} bytes")

            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM context")
                context_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM token_log")
                token_logs = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM chain_log")
                chain_logs = cursor.fetchone()[0]

                print(f"   📦 Context Packages: {context_count}")
                print(f"   🪙 Token Log Entries: {token_logs}")
                print(f"   🔗 Chain Log Entries: {chain_logs}")

                conn.close()
            except Exception as e:
                print(f"   ⚠️ Database error: {e}")

        print("\n" + "=" * 60)

    def run_loop(self, interval: int = 30):
        """Run continuous relay loop"""
        print(f"🔄 Starting relay loop (interval: {interval}s)")
        print("🛑 Press Ctrl+C to stop")

        try:
            while True:
                cycle_stats = self.relay_cycle()

                # Optional: Print cycle summary
                if cycle_stats["messages_found"] > 0:
                    print(
                        f"📊 Cycle: {cycle_stats['messages_found']} found, {cycle_stats['messages_relayed']} relayed"
                    )

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n🛑 Relay loop stopped by user")


def main():
    """Main relay interface with enhanced argument parsing"""
    parser = argparse.ArgumentParser(
        description="Enhanced Kor'tana Relay with Chain Routing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python relay.py --status        # Show system status
  python relay.py --route         # Test chain routing
  python relay.py --dashboard     # Open monitoring dashboard
  python relay.py --loop          # Run continuous relay
  python relay.py --handoff claude # Trigger handoff to claude
        """,
    )

    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--route", action="store_true", help="Test chain routing")
    parser.add_argument(
        "--dashboard", action="store_true", help="Open monitoring dashboard"
    )
    parser.add_argument("--summarize", action="store_true", help="Force summarization")
    parser.add_argument("--loop", action="store_true", help="Run continuous relay")
    parser.add_argument("--handoff", type=str, help="Trigger handoff to specific agent")
    parser.add_argument(
        "--interval", type=int, default=30, help="Loop interval in seconds"
    )

    args = parser.parse_args()

    # Initialize relay
    relay = EnhancedKortanaRelay()

    if args.status:
        relay.print_status()
    elif args.route:
        task = input("Enter task description for routing: ").strip()
        if task:
            results = relay.route_task(task)
            print("\n📋 ROUTING RESULTS:")
            print(f"Task ID: {results['task_id']}")
            print(f"Total Tokens: {results['total_tokens']}")
            for stage, data in results["stages"].items():
                print(f"\n{stage.upper()}:")
                print(f"  Status: {data['status']}")
                print(f"  Tokens: {data['tokens']}")
                print(f"  Result: {data['result'][:200]}...")
        else:
            print("No task provided")
    elif args.dashboard:
        if relay.monitor:
            relay.monitor.print_dashboard()
        else:
            print("[ERROR] Enhanced monitoring not available")
    elif args.summarize:
        print("Force summarization not implemented in this version")
    elif args.handoff:
        agent_name = args.handoff
        if agent_name in relay.agents:
            print(f"Triggering handoff to {agent_name}")
            # Implementation would go here
        else:
            print(f"Agent '{agent_name}' not found")
            print(f"Available agents: {list(relay.agents.keys())}")
    elif args.loop:
        relay.run_loop(args.interval)
    else:
        # Interactive mode
        relay.print_status()
        print("\nEntering single relay cycle...")
        cycle_stats = relay.relay_cycle()
        print(f"Cycle completed: {cycle_stats}")


if __name__ == "__main__":
    main()
