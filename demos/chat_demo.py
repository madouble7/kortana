#!/usr/bin/env python
"""
Kor'tana Chat Demo

This script demonstrates how to use the Kor'tana chat engine for a simple conversation.
"""

import logging
import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from src.kortana.core.brain import ChatEngine


def main():
    """Run a simple chat demo using Kor'tana's ChatEngine."""
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger("chat_demo")

    logger.info("\n🔥 Welcome to Kor'tana Chat Demo 🔥\n")

    try:
        # Load configuration
        settings = load_config()

        # Initialize chat engine
        chat_engine = ChatEngine(settings=settings)

        logger.info(
            "Chat started. Type 'exit', 'quit', or press Ctrl+C to end the conversation.\n"
        )

        # Main chat loop
        while True:
            # Get user input
            user_input = input("👤 You: ")

            if user_input.lower() in ["exit", "quit"]:
                logger.info("\n👋 Goodbye!")
                break

            # Process message through ChatEngine
            response = chat_engine.process_message(user_input)

            # Display response
            print(f"\n🤖 Kor'tana: {response}\n")

    except KeyboardInterrupt:
        logger.info("\n\n👋 Chat ended by user.")
    except Exception as e:
        logger.error(f"Error in chat demo: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
