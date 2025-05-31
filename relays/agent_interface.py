#!/usr/bin/env python3
"""
Agent Interface for Kor'tana Orchestration
==========================================

Simple interface for agents to read/write messages in the relay system.
Each agent can use this to check for new directives and send outputs.

Usage:
    from relays.agent_interface import AgentInterface

    agent = AgentInterface("claude")
    messages = agent.get_new_messages()
    agent.send_output("Task completed successfully")
    agent.send_status("active", "Processing user request")
"""

import time
from datetime import datetime
from pathlib import Path
from typing import List


class AgentInterface:
    """Simple interface for agent communication in Kor'tana system"""

    def __init__(self, agent_name: str, project_root: str = None):
        """Initialize agent interface"""
        self.agent_name = agent_name
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent
        )

        # File paths
        self.log_file = self.project_root / "logs" / f"{agent_name}.log"
        self.queue_file = self.project_root / "queues" / f"{agent_name}_in.txt"
        self.status_file = self.project_root / "data" / f"{agent_name}_status.json"

        # Ensure directories exist
        self.log_file.parent.mkdir(exist_ok=True)
        self.queue_file.parent.mkdir(exist_ok=True)
        self.status_file.parent.mkdir(exist_ok=True)

        # Touch files to ensure they exist
        self.log_file.touch(exist_ok=True)
        self.queue_file.touch(exist_ok=True)

        # Track last read position to avoid re-reading messages
        self._last_queue_position = 0

        print(f"🤖 Agent '{agent_name}' interface initialized")

    def send_output(self, message: str, message_type: str = "output"):
        """Send output message to log (will be relayed to other agents)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message_type.upper()}: {message}"

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(formatted_message + "\n")
            print(f"📤 {self.agent_name}: {message}")
            return True
        except Exception as e:
            print(f"⚠️  Error writing to log: {e}")
            return False

    def send_status(self, status: str, details: str = ""):
        """Send status update"""
        status_message = f"STATUS: {status}"
        if details:
            status_message += f" - {details}"
        return self.send_output(status_message, "status")

    def send_intent(self, intent: str, target_agent: str = "all"):
        """Send intent/request message"""
        intent_message = f"INTENT: {intent}"
        if target_agent != "all":
            intent_message += f" @{target_agent}"
        return self.send_output(intent_message, "intent")

    def get_new_messages(self) -> List[str]:
        """Get new messages from queue since last check"""
        if not self.queue_file.exists():
            return []

        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                # Read all lines
                all_lines = f.readlines()

            # Get only new lines since last read
            new_lines = all_lines[self._last_queue_position :]
            self._last_queue_position = len(all_lines)

            # Clean and filter messages
            new_messages = []
            for line in new_lines:
                line = line.strip()
                if line:
                    new_messages.append(line)

            if new_messages:
                print(f"📨 {self.agent_name}: {len(new_messages)} new messages")
                for msg in new_messages:
                    print(f"   📝 {msg}")

            return new_messages

        except Exception as e:
            print(f"⚠️  Error reading queue: {e}")
            return []

    def check_for_directives(self) -> List[str]:
        """Check for specific directive messages (INTENT, REQUEST, etc.)"""
        messages = self.get_new_messages()
        directives = []

        for message in messages:
            # Look for directive keywords
            if any(
                keyword in message.upper()
                for keyword in ["INTENT:", "REQUEST:", "TASK:", "DIRECTIVE:"]
            ):
                directives.append(message)

        return directives

    def clear_queue(self):
        """Clear the agent's queue (mark all as read)"""
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                line_count = len(f.readlines())
            self._last_queue_position = line_count
            print(
                f"🧹 {self.agent_name}: Queue cleared ({line_count} messages marked as read)"
            )
        except Exception as e:
            print(f"⚠️  Error clearing queue: {e}")

    def get_queue_status(self) -> dict:
        """Get current queue status"""
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                all_lines = f.readlines()

            total_messages = len(all_lines)
            unread_messages = total_messages - self._last_queue_position

            return {
                "total_messages": total_messages,
                "unread_messages": unread_messages,
                "last_position": self._last_queue_position,
            }
        except:
            return {"total_messages": 0, "unread_messages": 0, "last_position": 0}


# Convenience functions for quick testing
def quick_test_agent(agent_name: str):
    """Quick test function for agent interface"""
    print(f"🧪 Testing agent interface for '{agent_name}'")

    agent = AgentInterface(agent_name)

    # Send test message
    agent.send_output(
        f"Hello from {agent_name} at {datetime.now().strftime('%H:%M:%S')}"
    )
    agent.send_status("testing", "Running interface test")

    # Check queue
    messages = agent.get_new_messages()
    status = agent.get_queue_status()

    print(f"📊 Queue status: {status}")
    print(f"✅ Test complete for {agent_name}")


def agent_demo_loop(agent_name: str, duration: int = 30):
    """Demo loop showing agent reading and responding"""
    print(f"🔄 Starting demo loop for '{agent_name}' ({duration}s)")

    agent = AgentInterface(agent_name)
    agent.send_status("active", "Starting demo loop")

    start_time = time.time()

    try:
        while time.time() - start_time < duration:
            # Check for new messages
            messages = agent.get_new_messages()

            # Respond to directives
            directives = agent.check_for_directives()
            for directive in directives:
                response = f"Received directive: {directive}"
                agent.send_output(response)

            # Send periodic heartbeat
            if int(time.time()) % 10 == 0:
                agent.send_status("active", "Demo loop running")

            time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n🛑 Demo loop stopped for {agent_name}")

    agent.send_status("idle", "Demo loop completed")
    print(f"✅ Demo complete for {agent_name}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python agent_interface.py test <agent_name>")
        print("  python agent_interface.py demo <agent_name> [duration]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "test" and len(sys.argv) >= 3:
        quick_test_agent(sys.argv[2])
    elif command == "demo" and len(sys.argv) >= 3:
        agent_name = sys.argv[2]
        duration = int(sys.argv[3]) if len(sys.argv) >= 4 else 30
        agent_demo_loop(agent_name, duration)
    else:
        print("Invalid command or missing agent name")
