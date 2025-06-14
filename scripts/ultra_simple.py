"""
Ultra Simple Kor'tana

A minimal implementation that works around permission issues.
"""

import asyncio
import random


def ritual_announce(message):
    """Display a ritual announcement."""
    print("\n" + "=" * 80)
    print(message.lower())
    print("=" * 80 + "\n")


async def simulate_response(message):
    """Simulate a response from Kor'tana."""
    # Simple responses for common greetings
    greetings = {
        "hello": "greetings, warchief. how may i assist you today?",
        "hi": "hello there. what's on your mind?",
        "hey": "hey warchief, i'm here for you.",
        "bye": "farewell, until we meet again.",
        "goodbye": "may your path be clear. until next time.",
    }

    questions = {
        "help": "i can assist with many things - conversation, research, coding, planning. what do you need?",
        "who": "i am kor'tana, your companion and advisor. i'm here to support you on your journey.",
        "what": "i'm kor'tana, built to provide insights, assistance and companionship.",
        "how": "i process information and generate responses based on my training and our conversations.",
        "warchief": "the warchief leads with vision and strength. my purpose is to serve as companion and advisor.",
    }

    # Check for direct matches
    message_lower = message.lower()

    # First check for exact matches to common phrases
    for key, response in greetings.items():
        if key == message_lower:
            return response

    # Then check for questions
    for key, response in questions.items():
        if key in message_lower:
            return response

    # Default responses
    default_responses = [
        "i hear you, warchief. tell me more about your thoughts on this.",
        "interesting perspective. what led you to this conclusion?",
        "i'm processing what you've shared. how can i best support you with this?",
        "i'm here to listen and assist you, warchief. what more would you like to explore?",
        "your words are important to me. how would you like to proceed?",
        "i'm considering what you've said. what matters most to you about this?",
    ]

    # Simulate thinking
    await asyncio.sleep(1)

    return random.choice(default_responses)


async def main():
    """Run the ultra simple Kor'tana."""
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

            # Generate response
            response = await simulate_response(user_input)

            # Print response (lowercase for "kortana")
            print(f"kortana: {response}")

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        # Farewell message
        ritual_announce("until we meet again, warchief.")


if __name__ == "__main__":
    asyncio.run(main())
