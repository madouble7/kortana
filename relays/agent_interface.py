#!/usr/bin/env python3
"""Agent interface for structured + legacy Kor'tana relay communication."""

import time
from datetime import datetime
from pathlib import Path

from relays.protocol import AgentEvent, parse_event_line


class AgentInterface:
    """Interface for agent communication in Kor'tana system.

    Supports both:
    - legacy plain-text log/queue lines
    - structured JSON event envelopes via relays.protocol.AgentEvent
    """

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

    def send_event(
        self,
        event_type: str,
        target: str = "all",
        task_id: str | None = None,
        payload: dict | None = None,
        requires_ack: bool = False,
        priority: str = "normal",
    ) -> bool:
        """Send a structured AgentEvent to this agent log."""
        event = AgentEvent.new(
            source=self.agent_name,
            target=target,
            event_type=event_type,
            task_id=task_id,
            payload=payload or {},
            requires_ack=requires_ack,
            priority=priority,
        )
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(event.to_json_line() + "\n")
            return True
        except Exception as e:
            print(f"⚠️  Error writing structured event to log: {e}")
            return False

    def heartbeat(self, task_id: str | None = None, details: str = "") -> bool:
        """Emit heartbeat event for coordinator live status updates."""
        return self.send_event(
            event_type="HEARTBEAT",
            target="coordinator",
            task_id=task_id,
            payload={"details": details},
        )

    def claim_task(self, task_id: str, details: str = "") -> bool:
        """Attempt task lease/claim through coordinator."""
        return self.send_event(
            event_type="TASK_CLAIM",
            target="coordinator",
            task_id=task_id,
            payload={"details": details},
            requires_ack=True,
        )

    def update_task_status(
        self, task_id: str, status: str, details: str = "", progress: int | None = None
    ) -> bool:
        """Send task update event for coordinator task graph updates."""
        payload = {"status": status, "details": details}
        if progress is not None:
            payload["progress"] = progress
        return self.send_event(
            event_type="TASK_UPDATE",
            target="coordinator",
            task_id=task_id,
            payload=payload,
        )

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

    def get_new_messages(self) -> list[str]:
        """Get new messages from queue since last check"""
        if not self.queue_file.exists():
            return []

    def get_new_events(self) -> list[AgentEvent]:
        """Get new structured events parsed from queue lines."""
        messages = self.get_new_messages()
        events: list[AgentEvent] = []
        for message in messages:
            event = parse_event_line(message)
            if event:
                events.append(event)
        return events

        try:
            with open(self.queue_file, encoding="utf-8") as f:
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

    def check_for_directives(self) -> list[str]:
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
            with open(self.queue_file, encoding="utf-8") as f:
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
            with open(self.queue_file, encoding="utf-8") as f:
                all_lines = f.readlines()
            total_messages = len(all_lines)
            unread_messages = total_messages - self._last_queue_position
            return {
                "total_messages": total_messages,
                "unread_messages": unread_messages,
                "last_position": self._last_queue_position,
            }
        except Exception:
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
