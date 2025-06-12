#!/usr/bin/env python3
"""
Weaver Task Runner
=================

Polls weaver_in.txt for new messages, processes them, writes responses to weaver.log.
Weaver specializes in integration, coordination, and complex multi-step workflows.

Usage:
    python relays/run_weaver_task.py
"""

import os
import time
from datetime import datetime

IN_PATH = "../queues/weaver_in.txt"
OUT_LOG = "../logs/weaver.log"
SEEN = "../relays/.seen/weaver_in.txt.seen"


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
    """Process a message and generate a Weaver response (integration-focused)"""
    # Weaver persona: Integration, orchestration, workflow coordination
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Pattern matching for Weaver's integration responses
    if "coordinate" in msg.lower() or "orchestrate" in msg.lower():
        response = f"[WEAVER-ORCHESTRATION] Initiating coordination sequence for: {msg[:60]}... → Setting up multi-agent workflow pipeline."
    elif "integrate" in msg.lower():
        response = f"[WEAVER-INTEGRATION] Building integration bridge: {msg[:60]}... → Connecting systems and establishing data flow."
    elif "workflow" in msg.lower():
        response = f"[WEAVER-WORKFLOW] Designing workflow architecture: {msg[:60]}... → Mapping dependencies and execution sequence."
    elif "chain" in msg.lower():
        response = f"[WEAVER-CHAIN] Establishing agent chain: {msg[:60]}... → Linking Claude→Flash→Weaver for autonomous processing."
    else:
        # Generic Weaver response - integration and orchestration focused
        response = f"[WEAVER-SYNTHESIS] Processing complex request: {msg[:50]}... → Analyzing interdependencies and preparing coordinated response."

    return f"{timestamp} | {response}"


def write_response(response):
    """Write response to weaver.log"""
    os.makedirs(os.path.dirname(OUT_LOG), exist_ok=True)
    with open(OUT_LOG, "a", encoding="utf-8") as f:
        f.write(response + "\n")


def main():
    """Main polling loop for Weaver agent"""
    print("Weaver Task Runner starting...")
    print(f"Polling: {IN_PATH}")
    print(f"Output: {OUT_LOG}")
    print(f"State: {SEEN}")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            new_lines = read_new_lines()

            for msg in new_lines:
                print(f"[WEAVER] Processing: {msg[:50]}...")
                response = handle_message(msg)
                write_response(response)
                print(f"[WEAVER] Response logged: {response[:80]}...")

            time.sleep(2.5)  # Weaver takes time for complex integration work

    except KeyboardInterrupt:
        print("\n[WEAVER] Stopping task runner...")


if __name__ == "__main__":
    main()
