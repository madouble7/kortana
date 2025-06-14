#!/usr/bin/env python3
"""
Hands-Off Autonomous Runner
==========================

Full autonomous operation with self-monitoring and context management.
"""

import subprocess
import sys
import threading
import time
from datetime import datetime


class HandsOffRunner:
    def __init__(self):
        self.running = True

    def run_relay_system(self):
        """Run the enhanced relay system"""
        while self.running:
            try:
                subprocess.run([
                    sys.executable,
                    "enhanced_relay.py",
                    "--loop",
                    "--interval", "2"
                ], timeout=300)  # 5 minute timeout, then restart
            except subprocess.TimeoutExpired:
                print("🔄 Restarting relay system...")
            except KeyboardInterrupt:
                break

    def monitor_system(self):
        """Monitor system health and performance"""
        while self.running:
            try:
                # Check system status every 2 minutes
                time.sleep(120)
                subprocess.run([
                    sys.executable,
                    "enhanced_relay.py",
                    "--status"
                ], timeout=30)
            except KeyboardInterrupt:
                break

    def run(self):
        """Start hands-off operation"""
        print("🚀 Starting hands-off autonomous operation...")

        # Start relay system in separate thread
        relay_thread = threading.Thread(target=self.run_relay_system)
        relay_thread.daemon = True
        relay_thread.start()

        # Start monitoring in separate thread
        monitor_thread = threading.Thread(target=self.monitor_system)
        monitor_thread.daemon = True
        monitor_thread.start()

        try:
            # Main loop - just keep system alive
            while self.running:
                print(f"💓 Hands-off system heartbeat: {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(600)  # 10 minute heartbeat
        except KeyboardInterrupt:
            print("\n🛑 Shutting down hands-off operation...")
            self.running = False

if __name__ == "__main__":
    runner = HandsOffRunner()
    runner.run()
