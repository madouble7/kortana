#!/usr/bin/env python3
"""
Minimal test script to isolate import issues
"""


def test_minimal_import():
    print("Testing minimal imports...")

    # Test 1: Basic Python imports
    print("1. Testing standard library...")
    import sys

    print("   ✓ Standard library OK")

    # Test 2: Config system
    print("2. Testing config...")
    try:
        from src.kortana.config import load_config

        settings = load_config()
        print(f"   ✓ Config OK: {settings.app.name}")
    except Exception as e:
        print(f"   ❌ Config failed: {e}")
        return

    # Test 3: Direct module import (bypass package __init__)
    print("3. Testing direct module imports...")
    try:
        import sys

        sys.path.insert(0, r"c:\kortana\src")

        # Direct import without package
        from kortana.core.brain import ChatEngine

        print("   ✓ Direct ChatEngine import OK")

        print("   ✓ Direct CodingAgent import OK")

    except Exception as e:
        print(f"   ❌ Direct imports failed: {e}")
        import traceback

        traceback.print_exc()
        return

    # Test 4: ChatEngine instantiation
    print("4. Testing ChatEngine...")
    try:
        engine = ChatEngine(settings)
        print(f"   ✓ ChatEngine created: {engine.session_id}")
    except Exception as e:
        print(f"   ❌ ChatEngine failed: {e}")
        import traceback

        traceback.print_exc()
        return

    print("\n🎉 All minimal tests passed!")


if __name__ == "__main__":
    test_minimal_import()
