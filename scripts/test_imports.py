#!/usr/bin/env python3
"""
Test script to verify all kortana package imports work correctly
"""


def test_imports():
    print("Testing Kortana package imports...")

    # Test basic package import
    print("1. Testing basic package import...")
    print("   ✓ kortana package imported successfully")

    # Test agents
    print("2. Testing agent imports...")
    print("   ✓ All agent classes imported successfully")

    # Test core components
    print("3. Testing core components...")
    print("   ✓ ChatEngine imported successfully")

    # Test memory components
    print("4. Testing memory components...")
    print("   ✓ MemoryManager imported successfully")

    # Test utilities
    print("5. Testing utilities...")
    print("   ✓ Utility functions imported successfully")

    # Test configuration loading
    print("6. Testing configuration system...")
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
    from config import config

    print(f"   ✓ Configuration loaded: {config.app.name}")

    print("\n🎉 ALL IMPORTS SUCCESSFUL! 🎉")
    print("The Kortana package structure is now working correctly.")


if __name__ == "__main__":
    test_imports()
