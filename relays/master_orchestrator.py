#!/usr/bin/env python3
"""
Master Autonomous Agent Orchestrator
===================================

Runs the complete autonomous agent system:
1. Relay orchestrator (scans logs → queues)
2. Claude task runner (processes claude_in.txt)
3. Flash task runner (processes flash_in.txt)
4. Weaver task runner (processes weaver_in.txt)

Usage:
    python relays/master_orchestrator.py
"""

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
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
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
                    stdout, stderr = proc.communicate()
                    if stderr:
                        print(f"Error: {stderr}")

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping autonomous agent system...")

        # Terminate all processes
        for proc, name in processes:
            try:
                proc.terminate()
                print(f"Stopped {name}")
            except:
                pass

        # Wait for cleanup
        time.sleep(2)

        print("✅ All components stopped")
        print("Autonomous agent system shutdown complete.")


if __name__ == "__main__":
    main()
