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
    python relay_torch_integrated.py --status        # System status
    python relay_torch_integrated.py --route         # Test chain routing
    python relay_torch_integrated.py --torch         # Create torch package
    python relay_torch_integrated.py --dashboard     # Monitoring dashboard
    python relay_torch_integrated.py --demo          # Demo chain handoff
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

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


class EnhancedKortanaRelay:
    """Enhanced relay with chain routing capabilities and torch protocol integration"""

    def __init__(self, project_root: str | None = None):
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
        self.torch_protocol = TorchProtocol(str(self.project_root))  # Set up Gemini
        self.gemini_api_key = GEMINI_API_KEY
        self.model: Any | None = None
        if self.gemini_api_key and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
                print("[INIT] Gemini 2.0 Flash configured successfully")
            except Exception as e:
                print(f"[WARNING] Failed to configure Gemini: {e}")
                self.model = None
        else:
            self.model = None

        # Agent configurations for the chain
        self.agents = {
            "init": "gemini-2.0-flash",
            "summarize": "gemini-2.0-flash",
            "test": "github-models",
            "production": "openrouter",
        }

    def _init_database(self):
        """Initialize database for logging"""
        self.logs_dir.mkdir(exist_ok=True)

        if not self.db_path.exists():
            print(f"[INIT] Creating database at {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()  # Create token usage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                task_id TEXT,
                stage TEXT,
                tokens INTEGER,
                agent TEXT
            )
        """)

        # Add missing columns if they don't exist
        try:
            cursor.execute("ALTER TABLE token_usage ADD COLUMN stage TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("ALTER TABLE token_usage ADD COLUMN agent TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Create context packages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                timestamp TEXT,
                history TEXT,
                code TEXT,
                issues TEXT,
                commit_ref TEXT,
                tokens INTEGER
            )
        """)

        conn.commit()
        conn.close()

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            # Fallback to word count approximation
            return int(len(text.split()) * 1.3)  # Rough estimate

    def log_token_usage(self, task_id: str, stage: str, tokens: int, agent: str = ""):
        """Log token usage to database"""
        timestamp = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO token_usage (timestamp, task_id, stage, tokens, agent)
            VALUES (?, ?, ?, ?, ?)
        """,
            (timestamp, task_id, stage, tokens, agent),
        )

        conn.commit()
        conn.close()

    def call_gemini_flash(self, task: dict[str, Any], history: str) -> str:
        """Call Gemini 2.0 Flash for task processing"""
        if not self.model:
            return f"[MOCK] Gemini processing for task: {task.get('description', 'Unknown task')}"

        prompt = f"""
        TASK: {task.get("description", "")}
        CURRENT CODE: {task.get("code", "None")}
        ISSUES: {", ".join(task.get("issues", []))}
        HISTORY: {history[-2000:]}  # Last 2000 chars

        Please provide implementation or improvements for this task.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[ERROR] Gemini call failed: {e}"

    def summarize_with_gemini(self, text: str) -> str:
        """Summarize text using Gemini"""
        if not self.model:
            return f"[MOCK SUMMARY] Key points from {len(text)} characters of history"

        prompt = f"""
        Please summarize the following development history, focusing on:
        - Key decisions made
        - Current progress status
        - Important technical details
        - Next steps needed

        HISTORY:
        {text[-4000:]}  # Last 4000 chars
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[ERROR] Summarization failed: {e}"

    def call_github_models(self, model: str, task: dict[str, Any], history: str) -> str:
        """Call GitHub Models API"""
        if not GITHUB_API_KEY:
            return f"[MOCK] GitHub Models {model} processing for task: {task.get('description', '')}"

        # GitHub Models integration would go here
        return f"[MOCK] {model} analysis: Task validation completed"

    def save_context_package(
        self,
        task_id: str,
        history: str,
        code: str,
        issues: list[str] | None = None,
        commit_ref: str = "",
    ) -> int:
        """Save context package to database"""
        if issues is None:
            issues = []

        timestamp = datetime.now().isoformat()
        tokens = self.count_tokens(f"{history} {code}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO context_packages
            (task_id, timestamp, history, code, issues, commit_ref, tokens)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                task_id,
                timestamp,
                history,
                code,
                json.dumps(issues),
                commit_ref,
                tokens,
            ),
        )

        conn.commit()
        conn.close()

        print(f"[SAVED] Context package '{task_id}' ({tokens} tokens)")
        return tokens

    def route_task(
        self, task: dict[str, Any], history: str, context_window: int | None = None
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
            return output, history

        # Step 2: Summarization & Handoff with Torch Protocol
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
                print(f"[TORCH] ✅ Torch package created: {torch_id}")
            except Exception as e:
                print(f"[TORCH] ⚠️ Warning: Failed to create torch package: {e}")

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

        # Step 3: Testing & Validation (GitHub Models) with Torch Protocol
        if task.get("stage") == "test":
            print("[STAGE] Testing with GitHub Models...")
            model = (
                "claude-3-haiku"
                if "dialogue" in task.get("description", "").lower()
                else "gpt-4o-mini"
            )
            output = self.call_github_models(model, task, history)

            # TORCH PROTOCOL: Create torch for testing phase
            print("[TORCH] Creating torch package for testing handoff...")
            try:
                torch_data = self.torch_protocol.prompt_torch_filler(
                    agent_name=model,
                    context=f"{history}\n\nTest Results: {output}",
                    handoff_reason="Testing phase completed, moving to production",
                    task_id=task.get("id", "unknown"),
                    auto_mode=True,
                )
                torch_id = self.torch_protocol.save_torch_package(
                    torch_data, from_agent=model, to_agent="production-system"
                )
                print(f"[TORCH] ✅ Torch package created: {torch_id}")
            except Exception as e:
                print(f"[TORCH] ⚠️ Warning: Failed to create torch package: {e}")

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

    def create_interactive_torch(self, task_id: str = "manual_torch"):
        """Create an interactive torch package"""
        print("[TORCH] Creating interactive torch package...")
        torch_data = self.torch_protocol.prompt_torch_filler(
            agent_name="relay-user",
            context="Interactive torch creation from enhanced relay system",
            handoff_reason="Manual torch creation requested",
            task_id=task_id,
        )
        torch_id = self.torch_protocol.save_torch_package(
            torch_data, from_agent="relay-user", to_agent="next-agent"
        )
        print(f"[TORCH] ✅ Torch package created with ID: {torch_id}")
        return torch_id

    def show_torch_status(self):
        """Show torch protocol status and recent torches"""
        print("\n🔥 TORCH PROTOCOL STATUS")
        print("=" * 50)

        try:
            recent_torches = self.torch_protocol.get_recent_torches(limit=5)
            print(f"Recent Torches: {len(recent_torches)}")

            for torch in recent_torches:
                print(
                    f"  🔥 {torch['torch_id'][:8]}... | {torch['from_agent']} → {torch['to_agent']}"
                )
                print(f"     Task: {torch['task_title']}")
                print(f"     Reason: {torch['handoff_reason']}")
                print()

        except Exception as e:
            print(f"❌ Error retrieving torch status: {e}")


def print_dashboard():
    """Print monitoring dashboard if available"""
    try:
        sys.path.append(str(Path(__file__).parent.parent))
        from monitoring_dashboard import KortanaMonitor

        monitor = KortanaMonitor()
        monitor.print_dashboard()
    except ImportError:
        print("[INFO] Monitoring dashboard not available")
        print("Run: pip install matplotlib seaborn")
    except Exception as e:
        print(f"[WARNING] Dashboard error: {e}")


def main():
    """Main function for testing chain routing with torch protocol"""
    parser = argparse.ArgumentParser(
        description="Enhanced Kor'tana Relay with Chain Routing & Torch Protocol"
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
    parser.add_argument("--demo", action="store_true", help="Demo torch integration")

    args = parser.parse_args()

    # Initialize relay
    relay = EnhancedKortanaRelay()

    if args.dashboard:
        print_dashboard()
        return

    if args.torch:
        relay.create_interactive_torch(args.task_id)
        return

    if args.demo:
        print("[DEMO] Torch Protocol Integration Demo")
        print("=" * 50)

        # Demo task
        task = {
            "id": "torch_demo_001",
            "description": "Demo torch protocol integration with multi-agent handoffs",
            "code": "",
            "issues": ["Implement torch handoffs", "Test agent detection"],
            "commit_ref": "github.com/kortana/torch-demo",
            "stage": "init",
        }

        history = "Starting torch protocol demo. Testing seamless agent handoffs with living memory."

        print(f"[DEMO] Processing: {task['description']}")

        # Route through the chain with torch protocol
        output, new_history = relay.route_task(task, history)

        print("\n[DEMO] ✅ Task completed!")
        print(f"[DEMO] Final stage: {task['stage']}")

        # Show torch status
        relay.show_torch_status()
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
        print("[STATUS] Enhanced Kor'tana Relay System with Torch Protocol")
        print("=" * 60)
        print(f"Database: {relay.db_path}")
        print(f"Agents: {len(relay.agents)}")
        print(f"Context Window: {relay.context_window:,} tokens")
        print(f"Gemini API: {'✅ Configured' if relay.model else '❌ Not available'}")
        print(
            f"GitHub API: {'✅ Configured' if GITHUB_API_KEY else '❌ Not configured'}"
        )
        print(
            f"Torch Protocol: {'✅ Active' if relay.torch_protocol else '❌ Not available'}"
        )

        # Show torch status
        relay.show_torch_status()
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

    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
