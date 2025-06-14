#!/usr/bin/env python3
"""Simple test to verify Phase 5 script can start"""

import os
import sys

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)

print("Starting simple Phase 5 test...")

try:
    from phase5_advanced_autonomous import AdvancedAutonomousKortana

    print("✅ Phase 5 import successful")

    kortana = AdvancedAutonomousKortana()
    print("✅ Phase 5 instance created successfully")

    print("Phase 5 initialization complete!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
