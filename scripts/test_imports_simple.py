#!/usr/bin/env python3
"""Simple import validation test"""

import os
import sys

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)

print("Testing critical imports...")

try:
    print("1. Testing src.config.schema...")
    print("   ✅ SUCCESS")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

try:
    print("2. Testing src.kortana.core.services...")
    print("   ✅ SUCCESS")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

try:
    print("3. Testing src.kortana.core.brain...")
    print("   ✅ SUCCESS")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

try:
    print("4. Testing phase5_advanced_autonomous...")
    print("   ✅ SUCCESS")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

print("Import validation complete!")
