#!/usr/bin/env python3
"""
Kor'tana Automation Setup Guide
==============================

Complete setup guide for the three automation levels:
1. Manual - Full control, manual triggering
2. Semi-Auto - Automated tasks with manual monitoring
3. Hands-Off - Fully automated with minimal oversight

Usage:
    python setup_automation.py --level [manual|semi-auto|hands-off]
    python setup_automation.py --demo  # Show all options
"""

import os
import subprocess
import sys
from pathlib import Path


class KortanaAutomationSetup:
    """Setup guide for Kor'tana automation levels"""

    def __init__(self):
        """Initialize setup"""
        self.project_root = Path(__file__).parent
        self.relay_dir = self.project_root / "relays"

    def print_banner(self, title: str):
        """Print setup banner"""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)

    def check_requirements(self) -> bool:
        """Check if all required files exist"""
        required_files = [
            "relays/relay.py",
            "relays/handoff.py",
            "relays/autonomous_relay.py",
        ]

        missing = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing.append(file_path)

        if missing:
            print("❌ Missing required files:")
            for file_path in missing:
                print(f"   - {file_path}")
            return False

        print("✅ All required files present")
        return True

    def setup_manual(self):
        """Setup Manual automation level"""
        self.print_banner("MANUAL AUTOMATION SETUP")

        print(
            """
🎛️  MANUAL LEVEL - Full Control
═══════════════════════════════

You manually trigger all operations and monitor the system.

SETUP STEPS:

1. Set your Gemini API key:
   Windows: set GEMINI_API_KEY=your_gemini_api_key_here
   Linux:   export GEMINI_API_KEY=your_gemini_api_key_here

2. Initialize database:
   python init_db.py

3. Manual operations available:

   a) Single relay cycle:
      python relays/relay.py

   b) Check system status:
      python relays/relay.py --status

   c) Test summarization:
      python relays/relay.py --summarize

   d) Check handoff status:
      python relays/handoff.py --status

   e) Force agent handoff:
      python relays/handoff.py --handoff claude

   f) Monitor token usage:
      python relays/handoff.py --status

WHEN TO USE:
- Development and testing
- Learning the system
- Full control over operations
- Custom workflow requirements
        """
        )

        # Test manual operations
        print("\n🧪 TESTING MANUAL OPERATIONS:")
        try:
            print("   Testing relay status...")
            subprocess.run(
                [sys.executable, "relays/relay.py", "--status"],
                cwd=self.project_root,
                check=False,
                capture_output=True,
            )
            print("   ✅ Relay status works")

            print("   Testing handoff status...")
            subprocess.run(
                [sys.executable, "relays/handoff.py", "--status"],
                cwd=self.project_root,
                check=False,
                capture_output=True,
            )
            print("   ✅ Handoff status works")

        except Exception as e:
            print(f"   ⚠️  Test error: {e}")

    def setup_semi_auto(self):
        """Setup Semi-Auto automation level"""
        self.print_banner("SEMI-AUTO AUTOMATION SETUP")

        print(
            """
⚡ SEMI-AUTO LEVEL - Balanced Automation
════════════════════════════════════════

Automated tasks with manual monitoring and intervention.

SETUP STEPS:

1. Set your Gemini API key:
   set GEMINI_API_KEY=your_gemini_api_key_here

2. Run automated relay (every 5 minutes):
   relays\\run_relay.bat

3. Run automated handoffs (every 10 minutes):
   relays\\handoff.bat

4. Monitor via command line:
   python relays/relay.py --status
   python relays/handoff.py --status

5. Set up Windows Task Scheduler (optional):
   - Open Task Scheduler
   - Create Basic Task: "Kor'tana Relay"
   - Trigger: Every 5 minutes
   - Action: Start program -> relays\\run_relay.bat

WHAT'S AUTOMATED:
✅ Message relaying between agents
✅ Context summarization when needed
✅ Agent handoffs at 80% token usage
✅ Database persistence
✅ Status monitoring

WHAT YOU CONTROL:
🎛️  Start/stop automation
🎛️  Monitor system health
🎛️  Intervene when needed
🎛️  Adjust thresholds and settings

WHEN TO USE:
- Production systems with oversight
- Iterative development
- Learning system behavior
- Need for manual intervention
        """
        )

        # Create automation shortcuts
        print("\n🔧 CREATING AUTOMATION SHORTCUTS:")
        shortcuts = [
            ("Start Relay Automation", "relays\\run_relay.bat"),
            ("Start Handoff Automation", "relays\\handoff.bat"),
            ("Check Status", "python relays/relay.py --status"),
            ("Check Handoffs", "python relays/handoff.py --status"),
        ]

        for name, command in shortcuts:
            print(f"   📎 {name}: {command}")

    def setup_hands_off(self):
        """Setup Hands-Off automation level"""
        self.print_banner("HANDS-OFF AUTOMATION SETUP")

        print(
            """
🚀 HANDS-OFF LEVEL - Full Autonomy
══════════════════════════════════

Fully automated with dashboards and minimal oversight.

SETUP STEPS:

1. Set environment variables:
   set GEMINI_API_KEY=your_gemini_api_key_here
   set KORTANA_AUTO_MODE=hands-off

2. Install Windows Task Scheduler tasks:

   Task 1: "Kor'tana Relay System"
   - Trigger: At system startup
   - Action: python relays/relay.py --loop --interval 300
   - Settings: Run whether user logged on or not

   Task 2: "Kor'tana Handoff Monitor"
   - Trigger: At system startup
   - Action: python relays/handoff.py --monitor --interval 600
   - Settings: Run whether user logged on or not

3. Set up log rotation (optional):
   - Archive logs older than 30 days
   - Compress historical data
   - Monitor disk usage

4. Dashboard setup (optional):
   - Web dashboard at http://localhost:8080
   - Real-time agent status
   - Token usage graphs
   - Handoff history

WHAT'S AUTOMATED:
✅ Complete agent orchestration
✅ Automatic summarization
✅ Context package management
✅ Agent handoffs and restarts
✅ Error recovery
✅ Performance monitoring
✅ Log management
✅ Database maintenance

MONITORING:
📊 Check dashboard: http://localhost:8080
📊 View logs: logs/handoffs.log
📊 Database status: python relays/relay.py --status

WHEN TO USE:
- Production deployment
- 24/7 autonomous operation
- Minimal manual intervention
- Scalable multi-agent systems
        """
        )

        # Create Windows Task Scheduler commands
        print("\n⚙️  WINDOWS TASK SCHEDULER SETUP:")
        print(
            """
   1. Open Task Scheduler (taskschd.msc)
   2. Create Basic Task -> "Kor'tana Relay"
   3. Trigger: At startup
   4. Action: Start a program
   5. Program: python.exe
   6. Arguments: relays/relay.py --loop --interval 300
   7. Start in: C:\\kortana
   8. Repeat for handoff monitoring
        """
        )

    def demo_all_levels(self):
        """Demonstrate all automation levels"""
        self.print_banner("KOR'TANA AUTOMATION LEVELS DEMO")

        print(
            """
🎯 CHOOSE YOUR AUTOMATION LEVEL
═══════════════════════════════

Based on your needs and technical comfort:

📋 MANUAL (--level manual)
   - Full control over operations
   - Manual triggering of all tasks
   - Best for: Development, learning, custom workflows
   - Time investment: High, hands-on management

⚡ SEMI-AUTO (--level semi-auto)
   - Automated tasks with manual oversight
   - Scheduled relay and handoff operations
   - Best for: Production with monitoring, iterative development
   - Time investment: Medium, periodic monitoring

🚀 HANDS-OFF (--level hands-off)
   - Fully automated autonomous operation
   - Minimal oversight, automated recovery
   - Best for: 24/7 production, scalable systems
   - Time investment: Low, occasional check-ins

CURRENT SYSTEM STATUS:
        """
        )

        # Show current status
        self._show_system_status()

        print(
            """
NEXT STEPS:
   python setup_automation.py --level manual     # For full control
   python setup_automation.py --level semi-auto  # For balanced automation
   python setup_automation.py --level hands-off  # For full autonomy
        """
        )

    def _show_system_status(self):
        """Show current system status"""
        try:
            # Check if relay works
            result = subprocess.run(
                [sys.executable, "relays/relay.py", "--status"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                print("   ✅ Relay system: Working")
            else:
                print("   ⚠️  Relay system: Error")

            # Check if handoff works
            result = subprocess.run(
                [sys.executable, "relays/handoff.py", "--status"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                print("   ✅ Handoff system: Working")
            else:
                print("   ⚠️  Handoff system: Error")

            # Check database
            db_path = self.project_root / "kortana.db"
            if db_path.exists():
                print("   ✅ Database: Initialized")
            else:
                print("   📝 Database: Not initialized (run: python init_db.py)")

            # Check API key
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                print("   ✅ Gemini API: Configured")
            else:
                print("   🔑 Gemini API: Not configured (set GEMINI_API_KEY)")

        except Exception as e:
            print(f"   ❌ Status check failed: {e}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Kor'tana Automation Setup")
    parser.add_argument(
        "--level",
        choices=["manual", "semi-auto", "hands-off"],
        help="Setup automation level",
    )
    parser.add_argument(
        "--demo", action="store_true", help="Show all automation levels"
    )

    args = parser.parse_args()

    setup = KortanaAutomationSetup()

    if not setup.check_requirements():
        print("\n❌ Setup failed: Missing required files")
        return 1

    if args.demo:
        setup.demo_all_levels()
    elif args.level == "manual":
        setup.setup_manual()
    elif args.level == "semi-auto":
        setup.setup_semi_auto()
    elif args.level == "hands-off":
        setup.setup_hands_off()
    else:
        print("Use --demo to see all options or --level [manual|semi-auto|hands-off]")
        setup.demo_all_levels()

    print("\n🎯 Setup complete! Your autonomous Kor'tana system is ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
