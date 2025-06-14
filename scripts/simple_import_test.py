#!/usr/bin/env python3
"""
Simple import test for Kor'tana autonomous components
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("🔍 Testing Kor'tana imports...")
print(f"📁 Project root: {project_root}")
print(f"🐍 Python path: {sys.path[:3]}...")  # Show first 3 entries

try:
    print("\n1. Testing execution engine import...")
    sys.path.insert(0, os.path.join(project_root, "src"))
    from kortana.core.execution_engine import execution_engine

    print("✅ Execution engine imported successfully!")
    print(f"   Type: {type(execution_engine)}")
    print(f"   Allowed dirs: {len(execution_engine.allowed_dirs)}")
except Exception as e:
    print(f"❌ Failed to import execution engine: {e}")
    print(f"   Error type: {type(e)}")

try:
    print("\n2. Testing autonomous tasks import...")
    from kortana.core.autonomous_tasks import run_health_check_task

    print("✅ Autonomous tasks imported successfully!")
    print(f"   Function: {run_health_check_task}")
except Exception as e:
    print(f"❌ Failed to import autonomous tasks: {e}")
    print(f"   Error type: {type(e)}")

try:
    print("\n3. Testing basic execution...")
    result = execution_engine.execute_shell_command("echo Hello Kortana", project_root)
    print(f"✅ Basic execution test: {result}")
except Exception as e:
    print(f"❌ Basic execution failed: {e}")

print("\n🎯 Import test complete!")
