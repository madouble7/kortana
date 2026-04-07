#!/usr/bin/env python3
"""
Kor'tana Simple Chat - Doesn't require server
Local chat simulation with mock API responses
"""

import json
import random
from datetime import datetime
from pathlib import Path


class SimpleKorTanaChat:
    """Simple local chat with Kor'tana (mock responses)"""

    def __init__(self):
        self.conversation = []
        self.system_state = {
            "running": random.choice([True, False]),
            "tasks_total": random.randint(5, 20),
            "tasks_completed": random.randint(0, 15),
            "tasks_failed": random.randint(0, 3),
            "tasks_pending": random.randint(1, 5),
            "human_interventions": random.randint(0, 2),
            "uptime_hours": random.randint(10, 100),
            "last_check": datetime.now().isoformat(),
        }

    def print_banner(self):
        """Print welcome banner"""
        print("\n" + "=" * 70)
        print("🤖  KOR'TANA CHAT (Local Mode)")
        print("=" * 70)
        print("\nChatting with Kor'tana, your autonomous development assistant.")
        print("Type 'help' for available commands, 'exit' to quit.\n")
        print("-" * 70)

    def format_response(self, text: str) -> str:
        """Format response"""
        return f"\n🤖 Kor'tana: {text}\n"

    def handle_status(self) -> str:
        """Handle status query"""
        running = self.system_state["running"]
        tasks = self.system_state["tasks_total"]
        completed = self.system_state["tasks_completed"]
        failed = self.system_state["tasks_failed"]
        last_check = self.system_state["last_check"]

        return f"""Current Status:
  • Monitoring: {'🟢 Active' if running else '🔴 Paused'}
  • Total Tasks: {tasks}
  • Completed: {completed}
  • Failed: {failed}
  • Last Check: {last_check}
"""

    def handle_dashboard(self) -> str:
        """Display dashboard"""
        return f"""Dashboard Overview:
  • Status: {'🟢 Active' if self.system_state['running'] else '🔴 Paused'}
  • Total Tasks: {self.system_state['tasks_total']}
  • Completed: {self.system_state['tasks_completed']}
  • Failed: {self.system_state['tasks_failed']}
  • Pending: {self.system_state['tasks_pending']}
  • Human Interventions: {self.system_state['human_interventions']}
  • Uptime: {self.system_state['uptime_hours']} hours
"""

    def handle_tasks(self) -> str:
        """Display recent tasks"""
        tasks = [
            {"title": "Process GitHub Issues", "status": "completed", "id": "task-001"},
            {"title": "Fix failing tests", "status": "in_progress", "id": "task-002"},
            {
                "title": "Create documentation",
                "status": "pending",
                "id": "task-003",
            },
            {"title": "Review pull requests", "status": "completed", "id": "task-004"},
            {
                "title": "Optimize database queries",
                "status": "failed",
                "id": "task-005",
            },
        ]

        response = f"Recent Tasks ({len(tasks)}):\n"
        for i, task in enumerate(tasks, 1):
            response += f"\n  {i}. {task['title']}\n"
            response += f"     Status: {task['status']}\n"
            response += f"     ID: {task['id']}\n"

        return response

    def handle_metrics(self) -> str:
        """Display metrics"""
        return """Performance Metrics:
  • Tasks per Hour: 8-12
  • Average Task Duration: 4-6 minutes
  • Success Rate: 94%
  • Memory Usage: 256-512MB
  • CPU Usage: 15-25%
"""

    def handle_health(self) -> str:
        """Check system health"""
        return """System Health: HEALTHY
  ✅ Database: Connected
  ✅ Queue: Operational
  ✅ API: Responsive
  ✅ Memory: Normal
  ✅ Disk: Sufficient
"""

    def handle_start(self) -> str:
        """Start monitoring"""
        self.system_state["running"] = True
        return "✅ Autonomous monitoring activated. I'm now working on tasks."

    def handle_stop(self) -> str:
        """Stop monitoring"""
        self.system_state["running"] = False
        return "⏹️  Monitoring paused. I'm standing by."

    def handle_force_check(self) -> str:
        """Force immediate check"""
        return "⚡ Running immediate check for new tasks..."

    def show_help(self) -> str:
        """Show help"""
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

  Other:
    • help        - Show this help message
    • clear       - Clear conversation history
    • save        - Save conversation to file
    • exit        - Exit chat
"""

    def process_input(self, user_input: str) -> str:
        """Process user input"""
        user_input = user_input.strip().lower()

        if not user_input:
            return None

        # Command handlers
        commands = {
            "status": self.handle_status,
            "dashboard": self.handle_dashboard,
            "tasks": self.handle_tasks,
            "metrics": self.handle_metrics,
            "health": self.handle_health,
            "start": self.handle_start,
            "stop": self.handle_stop,
            "check": self.handle_force_check,
            "force check": self.handle_force_check,
            "help": self.show_help,
            "clear": lambda: "Conversation history cleared.",
            "exit": None,
            "quit": None,
        }

        # Find matching command
        for cmd, handler in commands.items():
            if cmd in user_input:
                if handler is None:
                    return "👋 Goodbye! See you next time."
                return handler()

        return f"Unknown command: '{user_input}'. Type 'help' for available commands."

    def save_conversation(self) -> str:
        """Save conversation"""
        try:
            log_file = Path("kor_tana_chat_log.json")
            with open(log_file, "w") as f:
                json.dump(self.conversation, f, indent=2)
            return f"✅ Conversation saved to {log_file.absolute()}"
        except Exception as e:
            return f"Error saving: {e}"

    def add_to_history(self, role: str, message: str):
        """Add to conversation history"""
        self.conversation.append(
            {
                "timestamp": datetime.now().isoformat(),
                "role": role,
                "message": message,
            }
        )

    def run(self):
        """Main chat loop"""
        self.print_banner()
        running = True

        try:
            while running:
                try:
                    user_input = input("💬 You: ").strip()

                    if not user_input:
                        continue

                    # Add to history
                    self.add_to_history("user", user_input)

                    # Process and respond
                    response = self.process_input(user_input)

                    if response is None:
                        running = False
                        response = "👋 Goodbye! See you next time."

                    if response:
                        print(self.format_response(response))
                        self.add_to_history("kor_tana", response)

                except KeyboardInterrupt:
                    print(self.format_response("Chat ended."))
                    running = False
                except Exception as e:
                    print(f"\n❌ Error: {e}\n")

        finally:
            self.save_conversation()
            print("\n✅ Chat session ended.\n")


def main():
    """Entry point"""
    try:
        chat = SimpleKorTanaChat()
        chat.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import sys

        sys.exit(1)


if __name__ == "__main__":
    main()
