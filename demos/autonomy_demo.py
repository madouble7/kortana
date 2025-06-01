#!/usr/bin/env python3
"""
Kor'tana Autonomy Test & Demo
============================

Quick demonstration of the autonomous relay system.
"""

import os
import time
from datetime import datetime


def add_message_to_log(agent, message):
    """Add a message to an agent's log file"""
    log_file = f"logs/{agent}.log"
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_message = f"[{timestamp}] {message}"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")

    print(f"📝 Added to {agent}.log: {full_message}")


def read_queue(agent):
    """Read messages from an agent's queue"""
    queue_file = f"queues/{agent}_in.txt"

    if not os.path.exists(queue_file):
        return []

    with open(queue_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return [line.strip() for line in lines if line.strip()]


def demo_autonomous_relay():
    """Demonstrate the autonomous relay system"""
    print("🚀 KOR'TANA AUTONOMY DEMO")
    print("=" * 40)
    print()

    print("1. Starting relay orchestrator in background...")
    # Note: In a real scenario, you'd start this in a separate terminal
    # For demo purposes, we'll simulate the workflow

    print("2. Adding messages to agent logs...")

    # Add some test messages
    add_message_to_log("flash", "Rapid response system online")
    add_message_to_log("claude", "Deep reasoning capabilities active")
    add_message_to_log("weaver", "Memory integration protocols ready")

    print("\n3. Simulating relay processing...")
    print("   (In real usage, the relay_agent_orchestrator.py would handle this)")

    # Simulate what the relay would do
    time.sleep(1)

    print("\n4. Checking agent queues after relay...")

    agents = ["flash", "claude", "weaver"]
    for agent in agents:
        messages = read_queue(agent)
        print(f"📥 {agent}_in.txt: {len(messages)} messages")
        if messages:
            for msg in messages[-2:]:  # Show last 2 messages
                print(f"   → {msg}")

    print("\n✅ Demo complete!")
    print("\nTo run the actual autonomous system:")
    print("1. Terminal 1: cd relays && python relay_agent_orchestrator.py")
    print("2. Terminal 2: echo 'Hello from agent' >> logs/flash.log")
    print("3. Watch messages appear in queues/*_in.txt files!")


def show_current_status():
    """Show current system status"""
    print("📊 CURRENT SYSTEM STATUS")
    print("=" * 30)

    # Check logs
    log_dir = "logs"
    if os.path.exists(log_dir):
        log_files = [f for f in os.listdir(log_dir) if f.endswith(".log")]
        print(f"📋 Log files: {len(log_files)}")
        for log_file in log_files:
            agent = log_file.replace(".log", "")
            log_path = os.path.join(log_dir, log_file)

            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                print(f"   📝 {agent}: {len(lines)} lines")

    # Check queues
    queue_dir = "queues"
    if os.path.exists(queue_dir):
        queue_files = [f for f in os.listdir(queue_dir) if f.endswith("_in.txt")]
        print(f"📥 Queue files: {len(queue_files)}")
        for queue_file in queue_files:
            agent = queue_file.replace("_in.txt", "")
            queue_path = os.path.join(queue_dir, queue_file)

            if os.path.exists(queue_path):
                with open(queue_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                print(f"   📥 {agent}_in: {len(lines)} messages")

    # Check relay state
    seen_dir = "relays/.seen"
    if os.path.exists(seen_dir):
        seen_files = os.listdir(seen_dir)
        print(f"🔍 Relay tracking: {len(seen_files)} files")


def main():
    """Main demo function"""
    import argparse

    parser = argparse.ArgumentParser(description="Kor'tana Autonomy Demo")
    parser.add_argument("--demo", action="store_true", help="Run full demo")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument(
        "--add", nargs=2, metavar=("AGENT", "MESSAGE"), help="Add message to agent log"
    )

    args = parser.parse_args()

    if args.demo:
        demo_autonomous_relay()
    elif args.status:
        show_current_status()
    elif args.add:
        agent, message = args.add
        add_message_to_log(agent, message)
    else:
        print("🤖 Kor'tana Autonomy System")
        print("Options:")
        print("  --demo     Run demonstration")
        print("  --status   Show system status")
        print("  --add AGENT MESSAGE  Add message to agent log")
        print()
        print("Quick start:")
        print("  python autonomy_demo.py --demo")


if __name__ == "__main__":
    main()
