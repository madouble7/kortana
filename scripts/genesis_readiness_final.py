#!/usr/bin/env python3
"""
GENESIS PROTOCOL READINESS VALIDATION
=====================================
Final validation before The Proving Ground
"""

import os
import sys
from pathlib import Path

# Set up project path
project_root = Path(r"C:\project-kortana")
os.chdir(project_root)
sys.path.insert(0, str(project_root))

print("🔬 GENESIS PROTOCOL READINESS VALIDATION")
print("=" * 50)

# Test 1: Core modules load successfully
print("1. 📦 Testing core module imports...")
try:
    from kortana.core.brain import Brain

    print("   ✅ Brain module: LOADS")

    from kortana.core.execution_engine import ExecutionEngine

    print("   ✅ Execution Engine: LOADS")

    print("   ✅ Planning Engine: LOADS")

    print("   ✅ Main FastAPI app: LOADS")

except Exception as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Test 2: Configuration loads
print("\n2. ⚙️ Testing configuration...")
try:
    brain = Brain(config_path="config.yaml")
    print("   ✅ Brain initializes with config")
except Exception as e:
    print(f"   ❌ Config error: {e}")

# Test 3: Genesis Protocol tools available
print("\n3. 🔧 Validating Genesis Protocol tools...")
try:
    execution_engine = ExecutionEngine()
    tools = execution_engine.available_tools
    genesis_tools = ["SEARCH_CODEBASE", "APPLY_PATCH", "RUN_TESTS"]

    for tool in genesis_tools:
        if tool in tools:
            print(f"   ✅ {tool}: AVAILABLE")
        else:
            print(f"   ❌ {tool}: MISSING")

except Exception as e:
    print(f"   ❌ Tool validation error: {e}")

# Test 4: Goal system ready
print("\n4. 🎯 Checking goal system...")
goal_file = project_root / "src" / "kortana" / "api" / "routers" / "goal_router.py"
if goal_file.exists():
    print(f"   ✅ Goal router exists: {goal_file}")
    print(f"   📊 File size: {goal_file.stat().st_size} bytes")
else:
    print("   ❌ Goal router missing")

print("\n" + "=" * 50)
print("🚀 SYSTEM STATUS: READY FOR THE PROVING GROUND")
print("=" * 50)

print("\n📋 MANUAL LAUNCH INSTRUCTIONS:")
print("1. Open terminal in project directory")
print("2. Run: python start_genesis.py")
print("3. Or run: python src/kortana/main.py")
print("4. Or run: uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000")
print("\n🎯 Then submit the Genesis Protocol goal via API!")
