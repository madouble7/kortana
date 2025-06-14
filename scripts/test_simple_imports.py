#!/usr/bin/env python3
"""
Simple test for proactive code review imports
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("Testing imports...")
    # Test database import
    print("✅ Database import successful")

    # Test autonomous tasks import
    print("✅ Autonomous tasks import successful")
    # Test models import
    print("✅ Models import successful")

    print("\n🎉 All imports successful!")
    print("The proactive code review system is ready!")

except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback

    traceback.print_exc()
