#!/usr/bin/env python3
"""Master autonomous agent orchestrator with coordinator integration."""

import os
import subprocess
import sys
import time


def run_component(script_name, component_name):
    """Run a component script in a subprocess"""
    try:
        print(f"Starting {component_name}...")
        process = subprocess.Popen(
            [sys.executable, script_name],
            cwd=os.getcwd(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        return process
    except Exception as e:
        print(f"Error starting {component_name}: {e}")
        return None


def main():
    """Start all autonomous agent components"""
    print("🤖 AUTONOMOUS KOR'TANA ORCHESTRATOR")
    print("=" * 50)
    print("Starting autonomous agent system...")
    print()

    # Ensure directories exist
    os.makedirs("../logs", exist_ok=True)
    os.makedirs("../queues", exist_ok=True)
    os.makedirs(".seen", exist_ok=True)

    components = [
        ("relay_agent_orchestrator.py", "Relay Orchestrator"),
        ("multi_agent_coordinator.py", "Multi-Agent Coordinator"),
        ("run_claude_task.py", "Claude Agent"),
        ("run_flash_task.py", "Flash Agent"),
        ("run_weaver_task.py", "Weaver Agent"),
    ]

    processes = []

    try:
        # Start all components
        for script, name in components:
            proc = run_component(script, name)
            if proc:
                processes.append((proc, name))
                time.sleep(1)  # Stagger startup

        print(f"\n✅ {len(processes)} components started successfully!")
        print("\nSystem Status:")
        print("- Relay Orchestrator: Scanning logs → relaying to queues")
        print("- Multi-Agent Coordinator: task leases, directives, real-time state")
        print("- Claude Agent: Processing claude_in.txt → claude.log")
        print("- Flash Agent: Processing flash_in.txt → flash.log")
        print("- Weaver Agent: Processing weaver_in.txt → weaver.log")
        print("\n🚀 AUTONOMOUS AGENT CHAINING ACTIVE")
        print("Press Ctrl+C to stop all components\n")

        # Monitor processes
        while True:
            time.sleep(5)

            # Check if any process died
            for proc, name in processes:
                if proc.poll() is not None:
                    print(f"⚠️  {name} stopped unexpectedly!")
                    print(
                        f"Component '{name}' exited with return code {proc.returncode}"
                    )

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping autonomous agent system...")

        # Terminate all processes
        for proc, name in processes:
            try:
                proc.terminate()
                print(f"Stopped {name}")
            except Exception:
                pass

        # Wait for cleanup
        time.sleep(2)

        print("✅ All components stopped")
        print("Autonomous agent system shutdown complete.")


if __name__ == "__main__":
    main()
