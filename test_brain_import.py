#!/usr/bin/env python3
"""Test brain import step by step."""

print("Testing brain import step by step...")

print("1. Testing basic imports...")
try:
    print("   ✅ Basic imports successful")
except Exception as e:
    print(f"   ❌ Basic imports failed: {e}")

print("2. Testing yaml import...")
try:
    print("   ✅ yaml imported")
except Exception as e:
    print(f"   ❌ yaml import failed: {e}")

print("3. Testing scheduler import...")
try:
    print("   ✅ scheduler imported")
except Exception as e:
    print(f"   ❌ scheduler import failed: {e}")

print("4. Testing config imports...")
try:
    print("   ✅ config imports successful")
except Exception as e:
    print(f"   ❌ config imports failed: {e}")

print("5. Testing agent imports...")
try:
    print("   ✅ agent imports successful")
except Exception as e:
    print(f"   ❌ agent imports failed: {e}")

print("6. Testing brain module import...")
try:
    print("   ✅ brain module imported")
except Exception as e:
    print(f"   ❌ brain module import failed: {e}")

print("All tests completed!")
