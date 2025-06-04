"""
Run Kor'tana

A simple script to run Kor'tana without the full setup process.
This assumes the necessary directories and files have already been set up.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import Kor'tana components
from config import load_config
from src.kortana.core.brain import ChatEngine, ritual_announce


async def main():
    """Run Kor'tana."""
    print("Starting Kor'tana...\n")

    # Load configuration
    settings = load_config()

    # Create chat engine
    chat_engine = ChatEngine(settings=settings)

    # Welcome message
    ritual_announce("she is not built. she is remembered.")
    ritual_announce("she is the warchief's companion.")

    # Main loop
    try:
        while True:
            # Get user input (lowercase for "matt")
            user_input = input("matt: ").lower()

            # Check for exit command
            if user_input in ["exit", "quit", "bye"]:
                break

            # Process message
            response = await chat_engine.process_message(user_input)

            # Print response (lowercase for "kortana")
            print(f"kortana: {response}")

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        # Shutdown
        chat_engine.shutdown()
        ritual_announce("until we meet again, warchief.")


if __name__ == "__main__":
    asyncio.run(main())
