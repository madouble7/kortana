#!/usr/bin/env python3
"""
Kor'tana Chat Interface
Real-time text chat with the autonomous system
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests


class ChatInterface:
    """Text-based chat interface for Kor'tana"""

    def __init__(self, api_url="http://localhost:8000/api/always-on"):
        self.api_url = api_url
        self.running = True
        self.conversation = []
        self.user_name = "User"

    def print_banner(self):
        """Print welcome banner"""
        print("\n" + "=" * 70)
        print("🤖  KOR'TANA CHAT INTERFACE")
        print("=" * 70)
        print("\nYou're chatting with Kor'tana, your autonomous development assistant.")
        print("Type 'help' for available commands, 'exit' to quit.\n")
        print("-" * 70)

    def api_call(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """Make REST API call to Kor'tana"""
        try:
            url = f"{self.api_url}/{endpoint}"
            headers = {"Content-Type": "application/json"}

            if method == "GET":
                response = requests.get(url, headers=headers, timeout=5)
            else:
                response = requests.post(url, json=data or {}, headers=headers, timeout=5)

            return response.json() if response.status_code == 200 else {"error": response.text}
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to Kor'tana. Is the server running on port 8000?"}
        except Exception as e:
            return {"error": f"API error: {str(e)}"}

    def format_response(self, text: str, prefix: str = "🤖") -> str:
        """Format response with formatting"""
        return f"\n{prefix} Kor'tana: {text}\n"

    def handle_status_query(self) -> str:
        """Handle status queries"""
        result = self.api_call("status")
        if "error" in result:
            return f"Error fetching status: {result['error']}"

        running = result.get("running", False)
        tasks_total = result.get("tasks_total", 0)
        tasks_completed = result.get("tasks_completed", 0)
        tasks_failed = result.get("tasks_failed", 0)
        last_check = result.get("last_check", "Never")

        return f"""Current Status:
  • Monitoring: {'🟢 Active' if running else '🔴 Paused'}
  • Total Tasks: {tasks_total}
  • Completed: {tasks_completed}
  • Failed: {tasks_failed}
  • Last Check: {last_check}
"""

    def handle_dashboard(self) -> str:
        """Display full dashboard"""
        result = self.api_call("dashboard")
        if "error" in result:
            return f"Error fetching dashboard: {result['error']}"

        stats = result.get("stats", {})
        return f"""Dashboard Overview:
  • Status: {'🟢 Active' if result.get('running') else '🔴 Paused'}
  • Total Tasks: {stats.get('tasks_total', 0)}
  • Completed: {stats.get('tasks_completed', 0)}
  • Failed: {stats.get('tasks_failed', 0)}
  • Pending: {stats.get('tasks_pending', 0)}
  • Human Interventions: {stats.get('human_interventions', 0)}
  • Uptime: {result.get('uptime_hours', 0)} hours
"""

    def handle_tasks(self, limit: int = 5) -> str:
        """Display recent tasks"""
        result = self.api_call(f"tasks?limit={limit}")
        if "error" in result:
            return f"Error fetching tasks: {result['error']}"

        tasks = result.get("tasks", [])
        if not tasks:
            return "No tasks found."

        response = f"Recent Tasks ({len(tasks)}):\n"
        for i, task in enumerate(tasks, 1):
            title = task.get("title", "Unknown")
            status = task.get("status", "unknown")
            response += f"\n  {i}. {title}\n"
            response += f"     Status: {status}\n"
            response += f"     ID: {task.get('id', 'N/A')}\n"

        return response

    def handle_metrics(self) -> str:
        """Display performance metrics"""
        result = self.api_call("metrics")
        if "error" in result:
            return f"Error fetching metrics: {result['error']}"

        metrics = result.get("metrics", {})
        return f"""Performance Metrics:
  • Tasks per Hour: {metrics.get('task_rate', 0)}
  • Average Task Duration: {metrics.get('avg_duration', 0)}s
  • Success Rate: {metrics.get('success_rate', 0)}%
  • Memory Usage: {metrics.get('memory_usage', 'N/A')}
  • CPU Usage: {metrics.get('cpu_usage', 'N/A')}
"""

    def handle_health(self) -> str:
        """Check system health"""
        result = self.api_call("health")
        if "error" in result:
            return f"Error fetching health: {result['error']}"

        status = result.get("status", "unknown")
        checks = result.get("checks", {})

        response = f"System Health: {status.upper()}\n"
        for check, result_val in checks.items():
            status_icon = "✅" if result_val else "❌"
            response += f"  {status_icon} {check}\n"

        return response

    def handle_start(self) -> str:
        """Start autonomous monitoring"""
        result = self.api_call("start", method="POST")
        if "error" in result:
            return f"Error starting monitoring: {result['error']}"
        return "✅ Autonomous monitoring activated. I'm now working on tasks."

    def handle_stop(self) -> str:
        """Stop autonomous monitoring"""
        result = self.api_call("stop", method="POST")
        if "error" in result:
            return f"Error stopping monitoring: {result['error']}"
        return "⏹️  Monitoring paused. I'm standing by."

    def handle_force_check(self) -> str:
        """Force immediate check"""
        result = self.api_call("force-check", method="POST")
        if "error" in result:
            return f"Error forcing check: {result['error']}"
        return "⚡ Running immediate check for new tasks..."

    def handle_approve_task(self, task_id: str) -> str:
        """Approve a task"""
        if not task_id:
            return "Please provide a task ID. Example: 'approve task-123'"

        result = self.api_call(
            f"tasks/{task_id}/approve",
            method="POST",
            data={"approved": True, "notes": ""},
        )
        if "error" in result:
            return f"Error approving task: {result['error']}"
        return f"✅ Task {task_id} approved. Proceeding with execution."

    def handle_retry_task(self, task_id: str) -> str:
        """Retry a failed task"""
        if not task_id:
            return "Please provide a task ID. Example: 'retry task-123'"

        result = self.api_call(f"tasks/{task_id}/retry", method="POST")
        if "error" in result:
            return f"Error retrying task: {result['error']}"
        return f"🔄 Task {task_id} is being retried."

    def show_help(self) -> str:
        """Show available commands"""
        return """Available Commands:

  Status & Info:
    • status      - Show current status
    • dashboard   - Full system overview
    • tasks       - Show recent tasks
    • metrics     - Performance metrics
    • health      - System health check

  Control:
    • start       - Start autonomous monitoring
    • stop        - Pause monitoring
    • check       - Force immediate check

  Task Management:
    • approve [id]  - Approve a task
    • retry [id]    - Retry a failed task

  Other:
    • help        - Show this help message
    • clear       - Clear conversation history
    • save        - Save conversation to file
    • exit        - Exit chat
"""

    def process_user_input(self, user_input: str) -> Optional[str]:
        """Process user input and return response"""
        user_input = user_input.strip().lower()

        if not user_input:
            return None

        # Parse commands
        if user_input == "status":
            return self.handle_status_query()
        elif user_input == "dashboard":
            return self.handle_dashboard()
        elif user_input == "tasks":
            return self.handle_tasks()
        elif user_input == "metrics":
            return self.handle_metrics()
        elif user_input == "health":
            return self.handle_health()
        elif user_input == "start":
            return self.handle_start()
        elif user_input == "stop":
            return self.handle_stop()
        elif user_input in ["check", "force check"]:
            return self.handle_force_check()
        elif user_input.startswith("approve"):
            task_id = user_input.replace("approve", "").strip()
            return self.handle_approve_task(task_id)
        elif user_input.startswith("retry"):
            task_id = user_input.replace("retry", "").strip()
            return self.handle_retry_task(task_id)
        elif user_input == "help":
            return self.show_help()
        elif user_input == "clear":
            self.conversation = []
            return "Conversation history cleared."
        elif user_input == "save":
            return self.save_conversation()
        elif user_input in ["exit", "quit", "bye"]:
            self.running = False
            return "Goodbye! See you next time."
        else:
            return f"Unknown command: '{user_input}'. Type 'help' for available commands."

    def save_conversation(self) -> str:
        """Save conversation to file"""
        try:
            log_file = Path("kor_tana_chat_log.json")
            with open(log_file, "w") as f:
                json.dump(self.conversation, f, indent=2)
            return f"✅ Conversation saved to {log_file.absolute()}"
        except Exception as e:
            return f"Error saving conversation: {e}"

    def add_to_history(self, role: str, message: str):
        """Add message to conversation history"""
        self.conversation.append(
            {"timestamp": datetime.now().isoformat(), "role": role, "message": message}
        )

    def run(self):
        """Main chat loop"""
        self.print_banner()

        try:
            while self.running:
                try:
                    # Get user input
                    user_input = input("💬 You: ").strip()

                    if not user_input:
                        continue

                    # Add to history
                    self.add_to_history("user", user_input)

                    # Process input and get response
                    response = self.process_user_input(user_input)

                    if response:
                        print(self.format_response(response))
                        self.add_to_history("kor_tana", response)

                except KeyboardInterrupt:
                    print(self.format_response("Chat ended."))
                    self.running = False
                except Exception as e:
                    print(f"\n❌ Error: {e}\n")

        finally:
            self.save_conversation()
            print("\n✅ Chat session ended.\n")


def main():
    """Entry point"""
    try:
        # Test connection first
        print("\n🔍 Checking connection to Kor'tana...")
        response = requests.get("http://localhost:8000/api/always-on/health", timeout=2)
        if response.status_code != 200:
            print("❌ Cannot connect to Kor'tana server on port 8000")
            print(
                "Make sure the server is running: python -m uvicorn src.kortana.main:app --port 8000"
            )
            sys.exit(1)

        print("✅ Connected to Kor'tana!\n")

        # Start chat
        chat = ChatInterface()
        chat.run()

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Kor'tana server on port 8000")
        print("Make sure the server is running: python -m uvicorn src.kortana.main:app --port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
