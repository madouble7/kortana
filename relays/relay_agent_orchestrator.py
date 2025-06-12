#!/usr/bin/env python3
"""
Kor'tana Relay Agent Orchestrator
================================

Minimal autonomous relay system:
- Scans all /logs/*.log files
- Relays new lines to matching /queues/*_in.txt
- Tracks what's been relayed (no duplicates)
- Loops every 2 seconds

Usage:
    cd relays
    python relay_agent_orchestrator.py
"""

import os
import time

LOGS_DIR = "../logs"
QUEUES_DIR = "../queues"
SEEN_DIR = "../relays/.seen"

os.makedirs(SEEN_DIR, exist_ok=True)
os.makedirs(QUEUES_DIR, exist_ok=True)


def get_seen_path(log_file):
    """Get the path to the .seen file for tracking processed lines"""
    base = os.path.basename(log_file)
    return os.path.join(SEEN_DIR, base + ".seen")


def read_new_lines(log_file):
    """Read only new lines since last processing"""
    seen_path = get_seen_path(log_file)
    last_count = 0

    # Get last processed line count
    if os.path.exists(seen_path):
        with open(seen_path, encoding="utf-8") as f:
            try:
                last_count = int(f.read().strip())
            except ValueError:
                last_count = 0

    # Check if log file exists
    if not os.path.exists(log_file):
        return [], last_count

    # Read all lines from log
    with open(log_file, encoding="utf-8") as f:
        lines = f.readlines()

    # Return only new lines
    new_lines = lines[last_count:]
    return new_lines, len(lines)


def write_to_queue(agent, lines):
    """Write new messages to agent's input queue"""
    if not lines:
        return

    queue_file = os.path.join(QUEUES_DIR, f"{agent}_in.txt")

    with open(queue_file, "a", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip("\n") + "\n")

    print(f"[relay] relayed {len(lines)} message(s) to {queue_file}")


def relay_all():
    """Process all log files and relay new messages"""
    for log_file in os.listdir(LOGS_DIR):
        if not log_file.endswith(".log"):
            continue

        agent = log_file.replace(".log", "")
        full_log_path = os.path.join(LOGS_DIR, log_file)

        # Get new lines since last check
        new_lines, total_lines = read_new_lines(full_log_path)

        # Relay to queue if there are new messages
        if new_lines:
            write_to_queue(agent, new_lines)

        # Update seen file with current line count
        seen_path = get_seen_path(full_log_path)
        with open(seen_path, "w", encoding="utf-8") as f:
            f.write(str(total_lines))


if __name__ == "__main__":
    print("🔄 kor'tana relay orchestrator started...")
    print(f"📁 Watching: {LOGS_DIR}")
    print(f"📤 Relaying to: {QUEUES_DIR}")
    print("💡 Press Ctrl+C to stop")
    print()

    try:
        while True:
            relay_all()
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n🛑 Relay orchestrator stopped")
