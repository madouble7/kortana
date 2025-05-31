#!/usr/bin/env python3
"""
Autonomous Agent Test
====================

Quick test to verify the autonomous agent chaining system works.
Sends test messages to logs and verifies they get processed.

Usage:
    python relays/test_autonomy.py
"""

import os
import time
from datetime import datetime


def send_test_message(agent, message):
    """Send a test message to an agent's log"""
    log_path = f"../logs/{agent}.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"{timestamp} | [TEST] {message}"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")

    print(f"📝 Sent to {agent}.log: {message}")


def check_queue(agent):
    """Check if message appeared in agent's queue"""
    queue_path = f"../queues/{agent}_in.txt"
    if os.path.exists(queue_path):
        with open(queue_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return len(lines), lines[-1].strip() if lines else ""
    return 0, ""


def main():
    """Run autonomy test"""
    print("🧪 AUTONOMOUS AGENT CHAINING TEST")
    print("=" * 40)
    print()

    # Test messages for each agent
    test_cases = [
        ("claude", "analyze this complex system architecture"),
        ("flash", "status check on system performance"),
        ("weaver", "coordinate multi-agent workflow integration"),
    ]

    print("Sending test messages...")
    for agent, message in test_cases:
        send_test_message(agent, message)
        time.sleep(0.5)

    print("\nWaiting for relay processing...")
    time.sleep(3)

    print("\nChecking relay results:")
    for agent, original_msg in test_cases:
        count, last_msg = check_queue(agent)
        if count > 0:
            print(f"✅ {agent}_in.txt: {count} messages, latest: {last_msg[:60]}...")
        else:
            print(f"❌ {agent}_in.txt: No messages found")

    print("\n" + "=" * 40)
    print("Test complete! If you see ✅ for all agents,")
    print("the autonomous relay system is working.")
    print("\nNext: Start master_orchestrator.py to see")
    print("full autonomous agent chaining in action!")


if __name__ == "__main__":
    main()
