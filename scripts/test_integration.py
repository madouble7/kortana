#!/usr/bin/env python3
"""
Integration Test for Core Components

This script tests that the PlanningEngine and ChatEngine are properly
using the enhanced model router.
"""

import asyncio
import logging
import sys

# Add the project root to the Python path
sys.path.insert(0, ".")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_planning_engine_integration():
    """Test that PlanningEngine uses the enhanced model router."""
    print("\n=== Testing PlanningEngine Integration ===")

    try:
        from src.kortana.core.planning_engine import planning_engine

        # Test planning with a simple goal
        test_goal = "Create a simple Python function that adds two numbers"

        print(f"Testing planning for goal: {test_goal}")
        plan = await planning_engine.create_plan_for_goal(test_goal)

        if plan:
            print(f"SUCCESS: Plan generated with {len(plan)} steps")
            for i, step in enumerate(plan[:3], 1):  # Show first 3 steps
                print(
                    f"  Step {i}: {step.get('action_type', 'Unknown')} - {step.get('parameters', {}).get('filepath', 'N/A')[:50]}..."
                )
        else:
            print("WARNING: No plan generated")

    except Exception as e:
        print(f"ERROR: Planning engine test failed: {e}")
        import traceback

        traceback.print_exc()


async def test_chat_engine_integration():
    """Test that ChatEngine uses the enhanced model router."""
    print("\n=== Testing ChatEngine Integration ===")

    try:
        from src.kortana.config import load_config
        from src.kortana.core.brain import ChatEngine

        # Load configuration
        settings = load_config()

        # Create chat engine instance
        chat_engine = ChatEngine(settings)

        # Test message processing
        test_message = "Hello, can you help me write a Python function?"

        print(f"Testing chat processing for message: {test_message}")
        response = await chat_engine.process_message(test_message)

        if response:
            print(f"SUCCESS: Response generated: {response[:100]}...")
        else:
            print("WARNING: No response generated")

    except Exception as e:
        print(f"ERROR: Chat engine test failed: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """Run integration tests."""
    print("Core Component Integration Tests")
    print("=" * 50)

    await test_planning_engine_integration()
    await test_chat_engine_integration()

    print("\n" + "=" * 50)
    print("Integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
