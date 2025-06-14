#!/usr/bin/env python3
"""Debug script to test phase5_advanced_autonomous.py"""

import sys
import traceback

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)

print("Starting debug test...")

try:
    print("Importing modules...")
    print("asyncio imported")

    print("ChatEngine imported")

    print("SacredCovenant imported")

    print("Importing main script...")
    from phase5_advanced_autonomous import AdvancedAutonomousKortana
    print("AdvancedAutonomousKortana imported successfully")

    print("Creating instance...")
    kortana = AdvancedAutonomousKortana()
    print("Instance created successfully")

except Exception as e:
    print(f"Error occurred: {e}")
    traceback.print_exc()
