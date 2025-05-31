#!/usr/bin/env python3
"""
Claude Task Runner
=================

Polls claude_in.txt for new messages, processes them, writes responses to claude.log.
This is the "consumption" side of the autonomous agent loop.

Usage:
    python relays/run_claude_task.py
"""

import os
import time
from datetime import datetime

IN_PATH = "../queues/claude_in.txt"
OUT_LOG = "../logs/claude.log"
SEEN = "../relays/.seen/claude_in.txt.seen"


def read_new_lines():
    """Read new lines since last processing"""
    if not os.path.exists(IN_PATH):
        return []

    # Get last processed count
    if not os.path.exists(SEEN):
        os.makedirs(os.path.dirname(SEEN), exist_ok=True)
        last_count = 0
    else:
        with open(SEEN, "r") as f:
            try:
                last_count = int(f.read().strip())
            except ValueError:
                last_count = 0

    # Read all lines
    with open(IN_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Get new lines
    new_lines = lines[last_count:]

    # Update seen count
    with open(SEEN, "w") as f:
        f.write(str(len(lines)))

    return [l.strip() for l in new_lines if l.strip()]


def handle_message(msg):
    """Process a message and generate a response"""
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Simulate Claude's deep reasoning capabilities
    if "code" in msg.lower() or "implement" in msg.lower():
        response = f"[{timestamp}] CLAUDE: Analyzing code requirements... I can help implement this with proper error handling and documentation."
    elif "reasoning" in msg.lower() or "analyze" in msg.lower():
        response = f"[{timestamp}] CLAUDE: Deep analysis mode engaged. Let me break this down systematically..."
    elif "research" in msg.lower() or "investigate" in msg.lower():
        response = f"[{timestamp}] CLAUDE: Research protocol activated. I'll gather comprehensive information on this topic."
    else:
        response = f"[{timestamp}] CLAUDE: Understood. Processing request with careful consideration of implications."

    # Write to log
    with open(OUT_LOG, "a", encoding="utf-8") as f:
        f.write(response + "\n")

    print(f"🧠 CLAUDE PROCESSED: {msg}")
    print(f"📝 CLAUDE RESPONSE: {response}")


def main():
    """Main polling loop"""
    print("🧠 Claude Task Runner started (polling for input)...")
    print(f"📥 Watching: {IN_PATH}")
    print(f"📝 Output: {OUT_LOG}")
    print("💡 Press Ctrl+C to stop")
    print()

    # Ensure directories exist
    os.makedirs(os.path.dirname(OUT_LOG), exist_ok=True)
    os.makedirs(os.path.dirname(SEEN), exist_ok=True)

    cycle_count = 0

    try:
        while True:
            cycle_count += 1
            new_messages = read_new_lines()

            if new_messages:
                print(f"🔔 Cycle {cycle_count}: {len(new_messages)} new messages")
                for msg in new_messages:
                    handle_message(msg)
            elif cycle_count % 30 == 0:  # Heartbeat every minute
                print(f"💓 Cycle {cycle_count}: Claude standing by...")

            time.sleep(2)

    except KeyboardInterrupt:
        print(f"\n🛑 Claude Task Runner stopped after {cycle_count} cycles")


if __name__ == "__main__":
    main()
