#!/usr/bin/env python3
"""
Enhanced Kor'tana Relay with Chain Routing & Pass the Torch Protocol
====================================================================

Integrated multi-stage AI chain with:
- Gemini 2.0 Flash for initialization and summarization
- Multiple AI providers (OpenAI, Anthropic, XAI, OpenRouter)
- Pass the Torch protocol for living memory handoffs
- Dashboard logging and token monitoring
- Context package management

Usage:
    python relay.py --status        # System status
    python relay.py --route         # Test chain routing
    python relay.py --torch         # Create torch package
    python relay.py --dashboard     # Monitoring dashboard
    python relay.py --demo          # Demo chain handoff
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import tiktoken

# Import torch protocol
sys.path.append(str(Path(__file__).parent.parent))
from torch_protocol import TorchProtocol

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Try to import google.genai components
try:
    from google.genai import Client, GenerativeModel, types

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("[WARNING] google-genai components not available. Using mock summarization.")

# Load API keys
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
GITHUB_API_KEY = os.getenv("GITHUB_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


class EnhancedKortanaRelay:
    """Enhanced relay with chain routing capabilities"""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize enhanced relay"""
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent
        )
        self.logs_dir = self.project_root / "logs"
        self.db_path = self.project_root / "kortana.db"

        # Context window settings
        self.context_window = 128000  # Conservative 128K limit
        self.handoff_threshold = 0.8  # 80% of context window

        # Initialize database
        self._init_database()

        # Initialize torch protocol
        self.torch_protocol = TorchProtocol(str(self.project_root))

        # Set up Gemini using the new client approach
        self.gemini_api_key = GEMINI_API_KEY
        if self.gemini_api_key and GENAI_AVAILABLE:
            try:
                # Use the new client-based initialization
                self.client = Client(api_key=self.gemini_api_key)
                # Create the GenerativeModel instance using the client
                self.model = self.client.models.GenerativeModel("gemini-2.0-flash-exp")
                print(
                    f"[AI] Gemini 2.0 Flash configured (key: {self.gemini_api_key[:10]}...)"
                )
            except Exception as e:
                print(f"[ERROR] Failed to configure Gemini client or model: {e}")
                self.client = None  # Set client to None if setup fails
                self.model = None
        else:
            self.client = None  # Ensure client is None if not available
            self.model = None
            print("[WARNING] Gemini not available - using mock responses")

        # Discover agents
        self.agents = self._discover_agents()

        print("[RELAY] Enhanced Kor'tana Relay initialized")
        print(f"[DATABASE] {self.db_path}")
        print(f"[AGENTS] {list(self.agents.keys())}")

    def _init_database(self):
        """Initialize database tables"""
        self.db_path.parent.mkdir(exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Context packages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context (
                task_id TEXT PRIMARY KEY,
                summary TEXT,
                code TEXT,
                issues TEXT,
                commit_ref TEXT,
                timestamp TEXT,
                tokens INTEGER
            )
        """)

        # Token logging table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                stage TEXT,
                tokens INTEGER,
                timestamp TEXT,
                agent_name TEXT
            )
        """)

        # Chain communication table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chain_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                stage TEXT,
                tokens INTEGER,
                timestamp TEXT,
                agent_from TEXT,
                agent_to TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _discover_agents(self) -> Dict[str, Any]:
        """Discover available agents"""
        agents = {}
        if self.logs_dir.exists():
            for log_file in self.logs_dir.glob("*.log"):
                agents[log_file.stem] = {
                    "log_file": log_file,
                    "last_modified": log_file.stat().st_mtime
                    if log_file.exists()
                    else 0,
                }
        return agents

    def count_tokens(self, text: str, encoding_name: str = "cl100k_base") -> int:
        """Count tokens in text using tiktoken"""
        try:
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(text))
        except Exception:
            return len(text) // 4

    def log_token_usage(
        self, task_id: str, stage: str, tokens: int, agent_name: str = "relay"
    ):
        """Log token usage to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO token_log (task_id, stage, tokens, timestamp, agent_name) VALUES (?, ?, ?, ?, ?)",
                (task_id, stage, tokens, datetime.utcnow().isoformat(), agent_name),
            )
            conn.commit()
            conn.close()
            print(f"[TOKENS] {task_id}/{stage}: {tokens} tokens")
        except Exception as e:
            print(f"[WARNING] Token logging failed: {e}")

    def log_chain_communication(
        self, task_id: str, stage: str, tokens: int, agent_from: str, agent_to: str
    ):
        """Log agent-to-agent communication"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chain_log (task_id, stage, tokens, timestamp, agent_from, agent_to) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    task_id,
                    stage,
                    tokens,
                    datetime.utcnow().isoformat(),
                    agent_from,
                    agent_to,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[WARNING] Chain logging failed: {e}")

    def call_gemini_flash(
        self, task: Dict[str, Any], history: str, max_tokens: int = 2000
    ) -> str:
        """Call Gemini 2.0 Flash for task processing"""
        if not self.model:
            return f"[MOCK GEMINI] Processing task: {task.get('description', 'Unknown task')[:100]}..."

        try:
            prompt = f"""Task: {task.get("description", "")}

Context History:
{history}

Instructions:
- Analyze the task requirements
- Consider the conversation history
- Provide a focused response
- Focus on actionable insights and next steps

Response:"""

            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            print(f"[WARNING] Gemini Flash call failed: {e}")
            return f"[ERROR] Failed to process with Gemini: {e}"

    def call_github_models(
        self, model: str, task: Dict[str, Any], history: str, max_tokens: int = 1000
    ) -> str:
        """Call GitHub Models API for testing and validation"""
        if not GITHUB_API_KEY:
            return f"[MOCK GITHUB] {model} processing: {task.get('description', '')[:100]}..."

        try:
            prompt = f"Task: {task.get('description', '')}\nHistory: {history}"

            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an AI assistant helping with software development tasks.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "model": model,
                "max_tokens": max_tokens,
                "temperature": 0.7,
            }

            response = requests.post(
                "https://models.inference.ai.azure.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {GITHUB_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                return (
                    result.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
            else:
                return f"[FALLBACK] GitHub Models API error: {response.status_code}"

        except Exception as e:
            return f"[FALLBACK] GitHub Models error: {e}"

    def summarize_with_gemini(self, history: str, max_tokens: int = 1000) -> str:
        """Summarize text using Gemini 2.0 Flash"""
        if not self.model:
            return f"[MOCK SUMMARY] {history[:200]}... (target: {max_tokens} tokens)"

        try:
            prompt = f"""Summarize the following conversation history to approximately {max_tokens} tokens.
Focus on key decisions, current status, and important context for handoff.

History:
{history}

Provide a concise summary:"""

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
        issues: Optional[List[str]] = None,
        commit_ref: str = "",
    ) -> int:
        """Save context package to database"""
        issues = issues or []
        package_data = {"summary": summary, "code": code, "issues": issues}
        tokens = self.count_tokens(json.dumps(package_data))

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO context
            (task_id, summary, code, issues, commit_ref, timestamp, tokens)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
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

    def route_task(
        self, task: Dict[str, Any], history: str, context_window: Optional[int] = None
    ) -> tuple[str, str]:
        """Route task through the AI chain based on stage and context"""
        context_window = context_window or self.context_window
        history_tokens = self.count_tokens(history)
        task_tokens = self.count_tokens(task.get("description", ""))

        print(
            f"[ROUTE] Task {task.get('id', 'unknown')} stage: {task.get('stage', 'init')}"
        )
        print(f"[TOKENS] History: {history_tokens}, Task: {task_tokens}")

        self.log_token_usage(
            task.get("id", "unknown"),
            task.get("stage", "unknown"),
            history_tokens + task_tokens,
        )

        # Step 1: Task Initiation (Gemini 2.0 Flash)
        if task.get("stage") == "init":
            print("[STAGE] Initializing with Gemini 2.0 Flash...")
            output = self.call_gemini_flash(task, history)
            task["code"] = output
            task["stage"] = "summarize"

            tokens = self.save_context_package(
                task.get("id", "unknown"),
                history,
                output,
                task.get("issues", []),
                task.get("commit_ref", ""),
            )
            self.log_token_usage(task.get("id", "unknown"), "init", tokens)
            return output, history  # Step 2: Summarization & Handoff
        if task.get("stage") == "summarize" and history_tokens > 0.4 * context_window:
            print("[STAGE] Summarizing with Gemini for handoff...")
            summary = self.summarize_with_gemini(history)

            # TORCH PROTOCOL: Create torch package for agent handoff
            print("[TORCH] Creating torch package for agent handoff...")
            try:
                torch_data = self.torch_protocol.prompt_torch_filler(
                    agent_name="gemini-2.0-flash",
                    context=f"{history}\n\nTask: {task.get('description', '')}",
                    handoff_reason="Context window threshold reached, handing off to testing stage",
                    task_id=task.get("id", "unknown"),
                    auto_mode=True,
                )
                torch_id = self.torch_protocol.save_torch_package(
                    torch_data, from_agent="gemini-2.0-flash", to_agent="github-models"
                )
                print(f"[TORCH] Torch package created: {torch_id}")
            except Exception as e:
                print(f"[TORCH] Warning: Failed to create torch package: {e}")

            tokens = self.save_context_package(
                task.get("id", "unknown"),
                summary,
                task.get("code", ""),
                task.get("issues", []),
                task.get("commit_ref", ""),
            )
            task["stage"] = "test"
            self.log_token_usage(task.get("id", "unknown"), "summarize", tokens)
            return task.get("code", ""), summary

        # Step 3: Testing & Validation (GitHub Models)
        if task.get("stage") == "test":
            print("[STAGE] Testing with GitHub Models...")
            model = (
                "claude-3-haiku"
                if "dialogue" in task.get("description", "").lower()
                else "gpt-4o-mini"
            )
            output = self.call_github_models(model, task, history)
            task["stage"] = "production"

            tokens = self.save_context_package(
                task.get("id", "unknown"),
                history,
                task.get("code", ""),
                task.get("issues", []),
                task.get("commit_ref", ""),
            )
            self.log_token_usage(task.get("id", "unknown"), "test", tokens)
            return output, history

        # Step 4: Production Scaling
        if task.get("stage") == "production":
            print("[STAGE] Production scaling (OpenRouter integration planned)...")
            return task.get("code", ""), history

        return task.get("code", ""), history


def print_dashboard():
    """Print monitoring dashboard if available"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from monitor import KortanaEnhancedMonitor

        monitor = KortanaEnhancedMonitor()
        monitor.print_dashboard()
    except ImportError:
        print("[INFO] Enhanced monitoring dashboard not available")
        print("[INFO] Use: python relays/monitor.py --dashboard")


def main():
    """Main function for testing chain routing"""
    parser = argparse.ArgumentParser(
        description="Enhanced Kor'tana Relay with Chain Routing"
    )
    parser.add_argument("--route", action="store_true", help="Test task routing")
    parser.add_argument(
        "--task-id", default="dialogue_parser_001", help="Task ID for routing test"
    )
    parser.add_argument(
        "--dashboard", action="store_true", help="Show monitoring dashboard"
    )
    parser.add_argument("--summarize", action="store_true", help="Force summarization")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--torch", action="store_true", help="Create torch package")

    args = parser.parse_args()

    # Initialize relay
    relay = EnhancedKortanaRelay()

    if args.dashboard:
        print_dashboard()
        return

    if args.route:
        print("[TEST] Testing chain routing functionality...")

        task = {
            "id": args.task_id,
            "description": "Implement dialogue parser with regex and NLP integration",
            "code": "",
            "issues": ["Add NLP integration", "Optimize regex patterns"],
            "commit_ref": "github.com/kortana/repo/commit/abc123",
            "stage": "init",
        }

        history = "Starting dialogue parser implementation. Need to handle complex conversation patterns."

        print(f"[TASK] Processing: {task['description']}")
        print(f"[STAGE] Initial stage: {task['stage']}")

        # Route through the chain
        output, new_history = relay.route_task(task, history)

        print(f"\n[OUTPUT] Result: {output[:200]}...")
        print(f"[HISTORY] New history length: {len(new_history)} chars")
        print(f"[STAGE] Final stage: {task['stage']}")

        print_dashboard()
        return

    if args.status:
        print("[STATUS] Enhanced Kor'tana Relay System")
        print("=" * 50)
        print(f"Database: {relay.db_path}")
        print(f"Agents: {len(relay.agents)}")
        print(f"Context Window: {relay.context_window:,} tokens")
        print(f"Gemini API: {'Configured' if relay.model else 'Not available'}")
        print(f"GitHub API: {'Configured' if GITHUB_API_KEY else 'Not configured'}")
        return

    if args.summarize:
        test_text = """
        Agent claude analyzed the dialogue parsing requirements.
        Agent weaver coordinated the workflow between parsing and NLP components.
        Agent flash provided quick insights on regex optimization.
        The current implementation handles basic conversation patterns but needs enhancement for complex dialogues.
        Token usage is at 50% of the context window.
        """

        summary = relay.summarize_with_gemini(test_text)
        print(f"[SUMMARY] {summary}")
        return

    if args.torch:
        print("[TORCH] Creating interactive torch package...")
        torch_data = relay.torch_protocol.prompt_torch_filler(
            agent_name="relay-user",
            context="Interactive torch creation from relay system",
            handoff_reason="Manual torch creation requested",
            task_id=args.task_id,
        )
        torch_id = relay.torch_protocol.save_torch_package(
            torch_data, from_agent="relay-user", to_agent="next-agent"
        )
        print(f"[TORCH] Torch package created with ID: {torch_id}")
        return

    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
