#!/usr/bin/env python3
"""
Quick test of the real autonomous Kor'tana
"""

import os
import sys
import traceback

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

print("🔍 Testing Real Autonomous Kor'tana...")
print("=" * 50)

try:
    print("1. Importing module...")
    import real_autonomous_kortana

    print("✅ Import successful")

    print("\n2. Testing main function...")
    real_autonomous_kortana.main()
    print("✅ Main function completed")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
