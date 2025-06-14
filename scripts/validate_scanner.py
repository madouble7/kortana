"""
Simple test to validate the scan tool is working
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Quick validation that the execution engine can be imported
try:
    from src.kortana.core.execution_engine import ExecutionEngine

    print("✅ ExecutionEngine imported successfully")

    # Check if the scan method exists
    engine = ExecutionEngine(allowed_dirs=["c:\\project-kortana"], blocked_commands=[])
    if hasattr(engine, "scan_codebase_for_issues"):
        print("✅ scan_codebase_for_issues method found")
    else:
        print("❌ scan_codebase_for_issues method not found")

except Exception as e:
    print(f"❌ Import failed: {e}")

print("🎯 Code scanner tool validation complete!")
