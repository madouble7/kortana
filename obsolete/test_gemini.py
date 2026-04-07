#!/usr/bin/env python3
"""Test Gemini integration"""
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.services.gemini import gemini_service


async def test_chat():
    """Test the Gemini chat endpoint"""
    if not gemini_service:
        print("ERROR: Gemini service failed to initialize!")
        return False

    test_message = "Hello! What is 2+2?"
    print(f"\nTesting with message: {test_message}")
    print(f"Using model: {gemini_service.model_name}\n")

    try:
        response = await gemini_service.analyze_text(test_message)
        print(f"SUCCESS - Response received:\n{response}\n")
        return True
    except Exception as e:
        print(f"ERROR: {e}\n")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nTesting Gemini Service Integration\n")
    success = asyncio.run(test_chat())
    sys.exit(0 if success else 1)
