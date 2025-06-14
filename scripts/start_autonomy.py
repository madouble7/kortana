#!/usr/bin/env python3
"""
Kor'tana Proto-Autonomy Launcher
===============================

Quick launcher for the minimal autonomous orchestration system.
Gets you out of "manual relay hell" with simple agent coordination.

Usage:
    python start_autonomy.py                    # Start relay + demo
    python start_autonomy.py --relay-only       # Just start the relay
    python start_autonomy.py --demo-agents      # Demo all agents
"""

import sys
import threading
import time
from pathlib import Path

# Add project root to path first, then import project modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from relays.agent_interface import AgentInterface
from relays.autonomous_relay import KortanaRelay


def start_relay_daemon():
    """Start the autonomous relay in the background"""
    print("🚀 Starting Kor'tana Autonomous Relay...")

    relay = KortanaRelay()

    # Run in daemon mode
    def relay_loop():
        try:
            relay.run_loop(interval=2)
        except KeyboardInterrupt:
            print("🛑 Relay daemon stopped")

    relay_thread = threading.Thread(target=relay_loop, daemon=True)
    relay_thread.start()

    return relay_thread


def demo_agent_activity():
    """Demonstrate agents communicating through the relay"""
    print("🎭 Starting agent activity demo...")

    # Create interfaces for different agents
    agents = {
        "claude": AgentInterface("claude"),
        "flash": AgentInterface("flash"),
        "weaver": AgentInterface("weaver"),
    }

    # Clear any existing queues
    for agent in agents.values():
        agent.clear_queue()

    print("📢 Agents initialized. Starting demonstration...")
    time.sleep(2)

    # Claude sends initial status
    agents["claude"].send_status("active", "Ready for coordination")
    agents["claude"].send_output("System initialized. Awaiting tasks.")
    time.sleep(1)

    # Flash responds
    agents["flash"].send_output("Flash agent online. Ready for rapid responses.")
    agents["flash"].send_intent("Request status update from all agents")
    time.sleep(1)

    # Weaver joins
    agents["weaver"].send_status("active", "Memory weaver ready")
    agents["weaver"].send_output("Processing memory patterns and connections.")
    time.sleep(1)

    # Show agents reading each other's messages
    print("\n📨 Checking message relay...")
    time.sleep(2)  # Wait for relay to process

    for agent_name, agent in agents.items():
        messages = agent.get_new_messages()
        if messages:
            print(f"🤖 {agent_name} received {len(messages)} messages")
        else:
            print(f"🤖 {agent_name} queue empty")

    # Claude coordinates a task
    agents["claude"].send_intent(
        "Task: Analyze user query and distribute subtasks", "all"
    )
    agents["claude"].send_output("Breaking down complex request into manageable parts")
    time.sleep(1)

    # Flash takes fast action
    agents["flash"].send_output("Executing quick analysis on user intent")
    agents["flash"].send_status("busy", "Processing user query")
    time.sleep(1)

    # Weaver provides context
    agents["weaver"].send_output("Retrieving relevant memory context for task")
    agents["weaver"].send_intent("Memory context available for analysis")
    time.sleep(2)

    # Final status check
    print("\n📊 Final message check after relay processing...")
    time.sleep(1)

    for agent_name, agent in agents.items():
        status = agent.get_queue_status()
        new_messages = agent.get_new_messages()
        print(
            f"🤖 {agent_name}: {status['unread_messages']} unread, {len(new_messages)} new"
        )

    print("✅ Agent demonstration complete!")


def show_system_status():
    """Show current system status"""
    print("📊 Kor'tana System Status")
    print("=" * 40)

    relay = KortanaRelay()
    relay.print_status()

    print("\n📁 File Status:")
    logs_dir = Path("logs")
    queues_dir = Path("queues")

    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        print(f"📝 Log files: {len(log_files)}")
        for log_file in log_files:
            size = log_file.stat().st_size if log_file.exists() else 0
            print(f"   {log_file.name}: {size} bytes")

    if queues_dir.exists():
        queue_files = list(queues_dir.glob("*_in.txt"))
        print(f"📥 Queue files: {len(queue_files)}")
        for queue_file in queue_files:
            try:
                with open(queue_file) as f:
                    lines = len(f.readlines())
                print(f"   {queue_file.name}: {lines} messages")
            except Exception:  # Changed bare except to except Exception
                print(f"   {queue_file.name}: error reading")


def main():
    """Main launcher"""
    import argparse

    parser = argparse.ArgumentParser(description="Kor'tana Proto-Autonomy Launcher")
    parser.add_argument(
        "--relay-only", action="store_true", help="Start only the relay system"
    )
    parser.add_argument(
        "--demo-agents", action="store_true", help="Run agent demonstration"
    )
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument(
        "--duration", type=int, default=60, help="Demo duration in seconds"
    )

    args = parser.parse_args()

    if args.status:
        show_system_status()
        return

    print("🎯 KOR'TANA PROTO-AUTONOMY SYSTEM")
    print("=" * 40)
    print("Getting you out of manual relay hell!")
    print()

    if args.relay_only:
        # Just start the relay
        relay = KortanaRelay()
        relay.run_loop()

    elif args.demo_agents:
        # Just run agent demo
        demo_agent_activity()

    else:
        # Full demonstration
        print("🚀 Starting full autonomous demonstration...")
        print(f"⏱️  Duration: {args.duration} seconds")
        print("📢 Press Ctrl+C to stop early")
        print()

        # Start relay in background
        start_relay_daemon()  # Removed assignment to unused relay_thread
        time.sleep(3)  # Give relay time to start

        # Run agent demonstration
        demo_agent_activity()

        # Keep running for specified duration
        print(f"\n⏱️  Continuing autonomous operation for {args.duration} seconds...")
        print("🔄 Relay is running, agents can communicate")
        print("💡 You can now test by manually adding messages to log files!")
        print()

        try:
            start_time = time.time()
            while time.time() - start_time < args.duration:
                time.sleep(5)
                elapsed = int(time.time() - start_time)
                remaining = args.duration - elapsed
                print(f"⏰ Running... {elapsed}s elapsed, {remaining}s remaining")

        except KeyboardInterrupt:
            print("\n🛑 Demo stopped by user")

        print("\n✅ Proto-autonomy demonstration complete!")
        print("💡 Next steps:")
        print(
            "   1. Run 'python relays/autonomous_relay.py --loop' for continuous relay"
        )
        print("   2. Use agent_interface.py to connect your actual agents")
        print("   3. Add messages to logs/ directory to see them relay automatically")


if __name__ == "__main__":
    main()
