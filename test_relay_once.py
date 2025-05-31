#!/usr/bin/env python3
"""
One-shot Relay Test
==================

Tests the relay functionality once without looping.
"""

import os
import sys

# Add the parent directory to the path so we can import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOGS_DIR = "logs"
QUEUES_DIR = "queues"
SEEN_DIR = "relays/.seen"


def test_relay_once():
    """Run relay processing once"""
    print("🔄 Testing relay system...")

    # Ensure directories exist
    os.makedirs(SEEN_DIR, exist_ok=True)
    os.makedirs(QUEUES_DIR, exist_ok=True)

    # Check logs directory
    if not os.path.exists(LOGS_DIR):
        print(f"❌ Logs directory {LOGS_DIR} not found!")
        return

    log_files = [f for f in os.listdir(LOGS_DIR) if f.endswith(".log")]
    print(f"📂 Found {len(log_files)} log files: {log_files}")

    for log_file in log_files:
        log_path = os.path.join(LOGS_DIR, log_file)
        agent_name = log_file.replace(".log", "")
        queue_path = os.path.join(QUEUES_DIR, f"{agent_name}_in.txt")
        seen_path = os.path.join(SEEN_DIR, f"{log_file}.seen")

        print(f"\n📋 Processing {log_file}...")

        # Get last processed count
        last_count = 0
        if os.path.exists(seen_path):
            with open(seen_path, "r", encoding="utf-8") as f:
                try:
                    last_count = int(f.read().strip())
                except ValueError:
                    last_count = 0

        # Read log file
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Get new lines
        new_lines = lines[last_count:]
        clean_lines = [line.strip() for line in new_lines if line.strip()]

        if clean_lines:
            print(f"   📝 Found {len(clean_lines)} new lines")

            # Write to queue
            with open(queue_path, "a", encoding="utf-8") as f:
                for line in clean_lines:
                    f.write(line + "\n")

            # Update seen count
            with open(seen_path, "w") as f:
                f.write(str(len(lines)))

            print(f"   ✅ Relayed to {queue_path}")
        else:
            print("   ℹ️  No new lines to process")


if __name__ == "__main__":
    test_relay_once()
    print("\n🎯 Relay test complete!")

    # Show results
    print("\n📊 Queue Results:")
    if os.path.exists(QUEUES_DIR):
        for queue_file in os.listdir(QUEUES_DIR):
            if queue_file.endswith("_in.txt"):
                queue_path = os.path.join(QUEUES_DIR, queue_file)
                with open(queue_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                print(
                    f"   {queue_file}: {len(content.splitlines()) if content else 0} lines"
                )
