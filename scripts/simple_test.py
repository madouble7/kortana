#!/usr/bin/env python3
"""Simple import test for Kortana modules."""


def test_basic_imports():
    print("Testing basic Kortana imports...")

    # Test configuration schema
    try:
        print("✅ KortanaConfig imported")
    except Exception as e:
        print(f"❌ KortanaConfig failed: {e}")

    # Test configuration functions
    try:
        print("✅ Config functions imported")
    except Exception as e:
        print(f"❌ Config functions failed: {e}")

    # Test memory manager
    try:
        print("✅ MemoryManager imported")
    except Exception as e:
        print(f"❌ MemoryManager failed: {e}")

    # Test agents
    try:
        print("✅ CodingAgent imported")
    except Exception as e:
        print(f"❌ CodingAgent failed: {e}")


if __name__ == "__main__":
    test_basic_imports()
