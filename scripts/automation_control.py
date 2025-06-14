#!/usr/bin/env python3
"""
Kor'tana Automation Control Center
=================================

Choose your automation level and run the appropriate system:

MANUAL: Basic tools, you control everything
SEMI-AUTO: Automated relay + monitoring, manual oversight
HANDS-OFF: Full autonomous operation with minimal intervention

Usage:
    python automation_control.py
    python automation_control.py --level manual|semi-auto|hands-off
"""

import subprocess
import sys
import time
from pathlib import Path


class AutomationController:
    """Control center for different automation levels"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.available_levels = ["manual", "semi-auto", "hands-off"]

    def show_menu(self):
        """Display automation level selection menu"""
        print("🤖 KOR'TANA AUTOMATION CONTROL CENTER")
        print("=" * 50)
        print()
        print("Choose your automation level:")
        print()
        print("1. 🔧 MANUAL")
        print("   - You control all operations")
        print("   - Use individual scripts as needed")
        print("   - Full control, maximum flexibility")
        print()
        print("2. ⚡ SEMI-AUTO")
        print("   - Automated relay + agent coordination")
        print("   - Manual monitoring and intervention")
        print("   - Best for development and testing")
        print()
        print("3. 🚀 HANDS-OFF")
        print("   - Full autonomous operation")
        print("   - Self-monitoring and context management")
        print("   - Minimal human oversight required")
        print()
        print("4. 📊 Show Current Status")
        print("5. ❌ Exit")
        print()

    def run_manual_mode(self):
        """Manual mode - provide tools and instructions"""
        print("🔧 MANUAL MODE ACTIVATED")
        print("=" * 40)
        print()
        print("Available tools:")
        print("• python enhanced_relay.py          - Single relay cycle")
        print("• python enhanced_relay.py --status - System status")
        print("• python relays/autonomous_relay.py - Basic relay system")
        print("• python test_relay_once.py        - Test relay function")
        print()
        print("Manual workflow:")
        print("1. Add messages to logs/*.log files")
        print("2. Run relay to process to queues/*.txt")
        print("3. Check agent responses in logs")
        print("4. Repeat as needed")
        print()
        print("Database tools:")
        print("• python init_db.py --stats        - Show DB statistics")
        print("• python init_db.py --reset        - Reset database")

    def run_semi_auto_mode(self):
        """Semi-automatic mode - automated relay with manual oversight"""
        print("⚡ SEMI-AUTO MODE ACTIVATED")
        print("=" * 40)
        print()
        print("Starting automated relay system...")
        print("You can monitor and intervene as needed.")
        print("Press Ctrl+C to stop and return to manual control.")
        print()

        try:
            # Run enhanced relay in loop mode
            subprocess.run(
                [sys.executable, "enhanced_relay.py", "--loop", "--interval", "3"],
                cwd=self.project_root,
            )

        except KeyboardInterrupt:
            print("\n⚡ Semi-auto mode stopped. Returning to manual control.")
        except Exception as e:
            print(f"❌ Error in semi-auto mode: {e}")

    def run_hands_off_mode(self):
        """Hands-off mode - full autonomous operation"""
        print("🚀 HANDS-OFF MODE ACTIVATED")
        print("=" * 40)
        print()
        print("Initializing full autonomous operation...")
        print("System will run independently with minimal oversight.")
        print("Check status periodically or press Ctrl+C for emergency stop.")
        print()

        # Create a comprehensive autonomous runner
        hands_off_script = self.project_root / "hands_off_runner.py"

        if not hands_off_script.exists():
            self.create_hands_off_runner()

        try:
            subprocess.run(
                [sys.executable, str(hands_off_script)], cwd=self.project_root
            )
        except KeyboardInterrupt:
            print("\n🚀 Hands-off mode stopped. System returning to standby.")
        except Exception as e:
            print(f"❌ Error in hands-off mode: {e}")

    def create_hands_off_runner(self):
        """Create the hands-off autonomous runner script"""
        script_content = '''#!/usr/bin/env python3
"""
Hands-Off Autonomous Runner
==========================

Full autonomous operation with self-monitoring and context management.
"""

import time
import threading
import subprocess
import sys
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
            print("\\n🛑 Shutting down hands-off operation...")
            self.running = False

if __name__ == "__main__":
    runner = HandsOffRunner()
    runner.run()
'''

        hands_off_path = self.project_root / "hands_off_runner.py"
        with open(hands_off_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        print(f"✅ Created hands-off runner: {hands_off_path}")

    def show_status(self):
        """Show current system status"""
        print("📊 CURRENT SYSTEM STATUS")
        print("=" * 40)

        # Check if database exists
        db_path = self.project_root / "kortana.db"
        if db_path.exists():
            print("✅ Database: kortana.db exists")
        else:
            print("❌ Database: kortana.db not found")

        # Check logs directory
        logs_dir = self.project_root / "logs"
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            print(f"✅ Logs: {len(log_files)} agent log files")
        else:
            print("❌ Logs: logs directory not found")  # Check queues directory
        queues_dir = self.project_root / "queues"
        if queues_dir.exists():
            queue_files = list(queues_dir.glob("*_in.txt"))
            print(f"✅ Queues: {len(queue_files)} agent queue files")
        else:
            print("❌ Queues: queues directory not found")

        # Try to get enhanced status
        try:
            subprocess.run(
                [sys.executable, "enhanced_relay.py", "--status"],
                cwd=self.project_root,
                timeout=10,
            )
        except Exception:
            print("⚠️  Could not get enhanced relay status")

    def run(self):
        """Main control loop"""
        while True:
            self.show_menu()

            try:
                choice = input("Enter choice (1-5): ").strip()
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break

            if choice == "1":
                self.run_manual_mode()
                input("\nPress Enter to return to menu...")
            elif choice == "2":
                self.run_semi_auto_mode()
            elif choice == "3":
                self.run_hands_off_mode()
            elif choice == "4":
                self.show_status()
                input("\nPress Enter to return to menu...")
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                time.sleep(1)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Kor'tana Automation Control")
    parser.add_argument(
        "--level",
        choices=["manual", "semi-auto", "hands-off"],
        help="Run specific automation level",
    )

    args = parser.parse_args()

    controller = AutomationController()

    if args.level:
        if args.level == "manual":
            controller.run_manual_mode()
        elif args.level == "semi-auto":
            controller.run_semi_auto_mode()
        elif args.level == "hands-off":
            controller.run_hands_off_mode()
    else:
        controller.run()


if __name__ == "__main__":
    main()
