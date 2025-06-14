#!/usr/bin/env python3
"""
Autonomous Kor'tana Launcher
Ensures continuous autonomous operation with monitoring
"""

import signal
import sys
from datetime import datetime


def signal_handler(sig, frame):
    print(f"\n🛑 Received signal {sig}. Shutting down autonomous Kor'tana...")
    sys.exit(0)


def main():
    print("🚀 LAUNCHING AUTONOMOUS KOR'TANA")
    print("=" * 50)
    print(f"Started at: {datetime.now()}")
    print("This will run Kor'tana as a truly autonomous agent.")
    print("Press Ctrl+C to stop.")
    print()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Import and run the real autonomous agent
        from real_autonomous_kortana import main as run_autonomous

        print("🤖 Starting autonomous operations...")
        run_autonomous()

    except KeyboardInterrupt:
        print("\n🛑 Autonomous operation stopped by user")
    except Exception as e:
        print(f"\n❌ Error in autonomous operation: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("\n👋 Autonomous Kor'tana session ended")


if __name__ == "__main__":
    main()
