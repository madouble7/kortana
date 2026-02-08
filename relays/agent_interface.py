#!/usr/bin/env python3
"""Agent interface for structured + legacy Kor'tana relay communication."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any

from relays.protocol import AgentEvent, append_text_line, parse_event_line, utc_now_iso


class AgentInterface:
    """Interface for agent communication in Kor'tana system.

    Supports both:
    - legacy plain-text log/queue lines
    - structured JSON event envelopes via relays.protocol.AgentEvent
    """

    def __init__(self, agent_name: str, project_root: str | None = None):
        self.agent_name = agent_name
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent
        )

        self.log_file = self.project_root / "logs" / f"{agent_name}.log"
        self.queue_file = self.project_root / "queues" / f"{agent_name}_in.txt"
        self.coordinator_inbox = self.project_root / "queues" / "coordinator_in.txt"
        self.status_file = self.project_root / "data" / f"{agent_name}_status.json"

        self.log_file.parent.mkdir(exist_ok=True)
        self.queue_file.parent.mkdir(exist_ok=True)
        self.coordinator_inbox.parent.mkdir(exist_ok=True)
        self.status_file.parent.mkdir(exist_ok=True)

        self.log_file.touch(exist_ok=True)
        self.queue_file.touch(exist_ok=True)
        self.coordinator_inbox.touch(exist_ok=True)

        # Byte offset cursor for efficient queue tails.
        self._last_queue_offset = 0
        self._queue_remainder = ""

        print(f"Agent '{agent_name}' interface initialized")

    def send_output(self, message: str, message_type: str = "output") -> bool:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message_type.upper()}: {message}"

        try:
            append_text_line(self.log_file, formatted_message)
            return True
        except Exception as e:
            print(f"Error writing to log: {e}")
            return False

    def send_event(
        self,
        event_type: str,
        target: str = "all",
        task_id: str | None = None,
        payload: dict[str, Any] | None = None,
        requires_ack: bool = False,
        priority: str = "normal",
    ) -> bool:
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
            event_line = event.to_json_line()
            append_text_line(self.log_file, event_line)
            # Structured events are sent to the coordinator inbox for real-time routing.
            append_text_line(self.coordinator_inbox, event_line)
            return True
        except Exception as e:
            print(f"Error writing structured event to log: {e}")
            return False

    def heartbeat(self, task_id: str | None = None, details: str = "") -> bool:
        return self.send_event(
            event_type="HEARTBEAT",
            target="coordinator",
            task_id=task_id,
            payload={"details": details},
        )

    def claim_task(self, task_id: str, details: str = "") -> bool:
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
        payload: dict[str, Any] = {"status": status, "details": details}
        if progress is not None:
            payload["progress"] = progress
        return self.send_event(
            event_type="TASK_UPDATE",
            target="coordinator",
            task_id=task_id,
            payload=payload,
        )

    def send_status(self, status: str, details: str = "") -> bool:
        status_message = f"STATUS: {status}"
        if details:
            status_message += f" - {details}"
        ok = self.send_output(status_message, "status")
        self._write_status_snapshot(status=status, details=details)
        return ok

    def send_intent(self, intent: str, target_agent: str = "all") -> bool:
        intent_message = f"INTENT: {intent}"
        if target_agent != "all":
            intent_message += f" @{target_agent}"
        return self.send_output(intent_message, "intent")

    def _write_status_snapshot(self, status: str, details: str = "") -> None:
        snapshot = {
            "agent": self.agent_name,
            "status": status,
            "details": details,
            "updated_at": utc_now_iso(),
        }
        try:
            import json
            import os

            tmp = self.status_file.with_suffix(self.status_file.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
                f.write("\n")
            os.replace(tmp, self.status_file)
        except Exception as e:
            print(f"Error writing status snapshot: {e}")

    def get_new_messages(self) -> list[str]:
        if not self.queue_file.exists():
            return []

        try:
            with open(self.queue_file, encoding="utf-8") as f:
                # If file was truncated, reset cursor.
                size = self.queue_file.stat().st_size
                if self._last_queue_offset > size:
                    self._last_queue_offset = 0
                    self._queue_remainder = ""
                f.seek(self._last_queue_offset)
                chunk = f.read()
                self._last_queue_offset = f.tell()

            if not chunk and not self._queue_remainder:
                return []

            merged = f"{self._queue_remainder}{chunk}"
            lines = merged.splitlines()
            if merged and not merged.endswith(("\n", "\r")):
                self._queue_remainder = lines.pop() if lines else merged
            else:
                self._queue_remainder = ""

            return [line.strip() for line in lines if line.strip()]

        except Exception as e:
            print(f"Error reading queue: {e}")
            return []

    def get_new_events(self) -> list[AgentEvent]:
        messages = self.get_new_messages()
        events: list[AgentEvent] = []
        for message in messages:
            event = parse_event_line(message)
            if event:
                events.append(event)
        return events

    def check_for_directives(self, messages: list[str] | None = None) -> list[str]:
        """Check for specific directive messages (INTENT, REQUEST, etc.)"""
        source_messages = messages if messages is not None else self.get_new_messages()
        directives = []

        for message in source_messages:
            event = parse_event_line(message)
            if event and event.event_type == "DIRECTIVE":
                instruction = ""
                if event.payload:
                    instruction = str(event.payload.get("instruction") or "").strip()
                if instruction:
                    directives.append(instruction)
                else:
                    directives.append(message)
                continue
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
            self._last_queue_offset = self.queue_file.stat().st_size
            self._queue_remainder = ""
            print(
                f"🧹 {self.agent_name}: Queue cleared (offset={self._last_queue_offset})"
            )
        except Exception as e:
            print(f"⚠️  Error clearing queue: {e}")

    def get_queue_status(self) -> dict:
        """Get current queue status"""
        try:
            with open(self.queue_file, encoding="utf-8") as f:
                all_lines = f.readlines()
            total_messages = len(all_lines)
            unread_messages = 0
            with open(self.queue_file, encoding="utf-8") as f:
                size = self.queue_file.stat().st_size
                offset = min(self._last_queue_offset, size)
                f.seek(offset)
                unread_messages = len([ln for ln in f.readlines() if ln.strip()])
            return {
                "total_messages": total_messages,
                "unread_messages": unread_messages,
                "last_position": self._last_queue_offset,
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
            directives = agent.check_for_directives(messages=messages)
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
