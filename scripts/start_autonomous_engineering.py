#!/usr/bin/env python3
"""
AUTONOMOUS ENGINEERING INITIATOR
Start Kor'tana's brain and begin Genesis Protocol Phase 3 observation
"""

import os
import subprocess
import sys

print("🚀 GENESIS PROTOCOL PHASE 3: AUTONOMOUS ENGINEERING INITIATION")
print("=" * 70)

# 1. Baseline check
print("📋 BASELINE STATE:")
print(
    f"   📄 goal_router.py: {os.path.getsize('src/kortana/api/routers/goal_router.py')} bytes"
)
print(
    f"   📁 services directory: {'EXISTS' if os.path.exists('src/kortana/api/services') else 'NOT EXISTS'}"
)

# 2. Start autonomous brain
print("\n🧠 STARTING AUTONOMOUS BRAIN...")
try:
    # Use a simple direct execution approach
    cmd = [
        sys.executable,
        "-m",
        "src.kortana.core.brain",
        "--autonomous",
        "--cycles",
        "3",
    ]

    print(f"   💻 Command: {' '.join(cmd)}")
    print("   🔄 Starting autonomous processing...")

    # Run with timeout and capture output
    result = subprocess.run(
        cmd,
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
        timeout=300,  # 5 minute timeout
    )

    print(f"   ✅ Process completed with return code: {result.returncode}")

    if result.stdout:
        print("\n📤 STDOUT:")
        print(result.stdout)

    if result.stderr:
        print("\n📥 STDERR:")
        print(result.stderr)

except subprocess.TimeoutExpired:
    print("   ⏰ Process timed out (expected for continuous operation)")
except Exception as e:
    print(f"   ❌ Error starting brain: {e}")

# 3. Post-execution check
print("\n🔍 POST-EXECUTION CHECK:")
print(
    f"   📄 goal_router.py: {os.path.getsize('src/kortana/api/routers/goal_router.py')} bytes"
)
print(
    f"   📁 services directory: {'EXISTS' if os.path.exists('src/kortana/api/services') else 'NOT EXISTS'}"
)

if os.path.exists("src/kortana/api/services/goal_service.py"):
    print("   🎯 NEW SERVICE LAYER DETECTED!")
    with open("src/kortana/api/services/goal_service.py") as f:
        content = f.read()
        print(f"   📝 goal_service.py: {len(content.split(chr(10)))} lines")

print("\n🔬 PROVING GROUND: OBSERVATION PHASE COMPLETE")
print("Ready for manual code review and validation phase.")
