#!/usr/bin/env python3
"""
Flash Task Runner
================

Polls flash_in.txt for new messages, processes them, writes responses to flash.log.
Flash specializes in fast, concise responses and quick analysis.

Usage:
    python relays/run_flash_task.py
"""

import os
import time
from datetime import datetime

IN_PATH = "../queues/flash_in.txt"
OUT_LOG = "../logs/flash.log"
SEEN = "../relays/.seen/flash_in.txt.seen"


def read_new_lines():
    """Read new lines since last processing"""
    if not os.path.exists(IN_PATH):
        return []

    # Get last processed count
    if not os.path.exists(SEEN):
        os.makedirs(os.path.dirname(SEEN), exist_ok=True)
        last_count = 0
    else:
        with open(SEEN) as f:
            try:
                last_count = int(f.read().strip())
            except ValueError:
                last_count = 0

    # Read all lines
    with open(IN_PATH, encoding="utf-8") as f:
        lines = f.readlines()

    # Get new lines
    new_lines = lines[last_count:]

    # Update seen count
    with open(SEEN, "w") as f:
        f.write(str(len(lines)))

    return [line.strip() for line in new_lines if line.strip()]


def handle_message(msg):
    """Process a message and generate a Flash response (fast, concise)"""
    # Flash persona: Quick, efficient, direct responses
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Basic pattern matching for Flash's quick responses
    if "analyze" in msg.lower():
        response = f"[FLASH-ANALYSIS] Quick scan: {msg[:50]}... → Key insight: Pattern detected, proceeding with rapid assessment."
    elif "status" in msg.lower():
        response = "[FLASH-STATUS] System operational. Ready for next task."
    elif "error" in msg.lower():
        response = f"[FLASH-ERROR] Issue identified: {msg[:100]}... → Suggested fix: Check configuration."
    else:
        # Generic Flash response - fast and focused
        response = f"[FLASH-RESPONSE] Processed: {msg[:80]}... → Action: Quick evaluation complete, standing by."

    return f"{timestamp} | {response}"


def write_response(response):
    """Write response to flash.log"""
    os.makedirs(os.path.dirname(OUT_LOG), exist_ok=True)
    with open(OUT_LOG, "a", encoding="utf-8") as f:
        f.write(response + "\n")


def main():
    """Main polling loop for Flash agent"""
    print("Flash Task Runner starting...")
    print(f"Polling: {IN_PATH}")
    print(f"Output: {OUT_LOG}")
    print(f"State: {SEEN}")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            new_lines = read_new_lines()

            for msg in new_lines:
                print(f"[FLASH] Processing: {msg[:50]}...")
                response = handle_message(msg)
                write_response(response)
                print(f"[FLASH] Response logged: {response[:80]}...")

            time.sleep(1.5)  # Flash is fast - shorter polling interval

    except KeyboardInterrupt:
        print("\n[FLASH] Stopping task runner...")


if __name__ == "__main__":
    main()
