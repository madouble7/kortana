#!/usr/bin/env python3
"""
Kor'tana Continuous Autonomous Operation Launcher
=================================================

This launcher ensures Kor'tana runs continuously in autonomous mode
until explicitly stopped by the user.

Features:
- Continuous autonomous operation
- Auto-restart on errors (unless critical)
- Session persistence
- Graceful shutdown handling
"""

import os
import signal
import sys
import time
import traceback
from datetime import datetime

# Ensure project root is in path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n🛑 Received shutdown signal {sig}")
    print("Shutting down autonomous Kor'tana...")
    sys.exit(0)


def main():
    """Launch and maintain continuous autonomous operation."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🚀 LAUNCHING CONTINUOUS AUTONOMOUS KOR'TANA")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("This will run Kor'tana continuously until stopped.")
    print("Press Ctrl+C to stop autonomous operation.")
    print()

    restart_count = 0
    max_restarts = 5

    while restart_count < max_restarts:
        try:
            print(f"🤖 Starting autonomous Kor'tana (attempt {restart_count + 1})")

            # Import and run the brain in autonomous mode
            from kortana.config import load_config
            from kortana.config.schema import KortanaConfig
            from src.kortana.core.brain import ChatEngine

            # Load configuration
            settings = KortanaConfig(**load_config())

            # Create and start autonomous chat engine
            chat_engine = ChatEngine(settings=settings)

            print("✅ ChatEngine initialized")
            print("🔥 Activating autonomous mode...")

            # Start autonomous operation
            chat_engine.start_autonomous_mode()

            # If we get here, autonomous mode ended normally
            print("✅ Autonomous operation completed normally")
            break

        except KeyboardInterrupt:
            print("\n🛑 Autonomous operation stopped by user")
            break

        except ImportError as e:
            print(f"\n❌ Import error: {e}")
            print("Please check that all dependencies are installed.")
            break

        except Exception as e:
            restart_count += 1
            print(f"\n⚠️  Error in autonomous operation: {e}")

            if restart_count < max_restarts:
                print(
                    f"🔄 Restarting in 5 seconds... (attempt {restart_count + 1}/{max_restarts})"
                )
                time.sleep(5)
            else:
                print("❌ Max restart attempts reached. Stopping.")
                print("\nFull error details:")
                traceback.print_exc()
                break

    print("\n👋 Continuous autonomous operation ended")
    print(f"Total restart attempts: {restart_count}")


if __name__ == "__main__":
    main()
