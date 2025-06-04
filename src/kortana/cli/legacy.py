#!/usr/bin/env python3
"""
Legacy CLI Entry Points
Backwards compatibility for existing scripts
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from kortana.config import load_config
from kortana.core.autonomous_development_engine import AutonomousDevelopmentEngine


def start_autonomy():
    """Legacy entry point for start_autonomy.py"""
    try:
        config = load_config()
        engine = AutonomousDevelopmentEngine(config=config)

        print("Starting Project Kor'tana Autonomous Development Engine...")
        print("(Legacy mode - consider using 'kortana start' instead)")

        engine.start()
        return 0
    except Exception as e:
        print(f"Error starting autonomy: {e}", file=sys.stderr)
        return 1


def main_app():
    """Legacy entry point for main.py"""
    try:
        config = load_config()

        print("Starting Project Kor'tana Main Application...")
        print("(Legacy mode - consider using 'kortana interactive' instead)")

        # Import and run the main app logic
        from kortana.core.brain import Brain

        brain = Brain(config=config)

        # Simple interactive loop
        while True:
            user_input = input("kor'tana> ").strip()
            if user_input.lower() in ["exit", "quit"]:
                break
            response = brain.think(user_input)
            print(f"Response: {response}")

        return 0
    except Exception as e:
        print(f"Error in main app: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if "start_autonomy" in sys.argv[0]:
        sys.exit(start_autonomy())
    else:
        sys.exit(main_app())
