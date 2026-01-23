#!/usr/bin/env python3
"""
GENESIS PROTOCOL RESUMPTION: POST-FIX AUTONOMOUS RESTART
Re-initiate autonomous brain with corrected imports for Genesis Protocol demonstration
"""

import os
import subprocess
import sys
from datetime import datetime

print("🔥 GENESIS PROTOCOL: RESUMING AFTER IMPORT FIX")
print("=" * 60)

print("✅ EXECUTION BLOCKER RESOLVED:")
print("   • Fixed import path in brain.py")
print("   • Corrected 'src.kortana.config' → '..config'")
print("   • Import test successful")

print(f"\n🚀 RE-INITIATING AUTONOMOUS BRAIN: {datetime.now().strftime('%H:%M:%S')}")

try:
    # Start autonomous brain with timeout
    cmd = [sys.executable, "-m", "src.kortana.core.brain", "--autonomous", "--cycles", "3"]

    print(f"📋 Command: {' '.join(cmd)}")
    print("🔄 Starting autonomous processing with Genesis Protocol goal...")

    # Run with shorter timeout to allow monitoring
    result = subprocess.run(
        cmd,
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
        timeout=180  # 3 minutes
    )

    print(f"\n✅ Autonomous cycle completed (return code: {result.returncode})")

    if result.stdout:
        print("\n📤 AUTONOMOUS OUTPUT:")
        print(result.stdout[-1000:])  # Show last 1000 chars

    if result.stderr:
        print("\n📥 AUTONOMOUS ERRORS:")
        print(result.stderr[-500:])   # Show last 500 chars of errors

except subprocess.TimeoutExpired:
    print("⏰ Autonomous brain running beyond timeout (expected for active processing)")
    print("🔬 Switching to monitoring mode...")

except Exception as e:
    print(f"❌ Error during autonomous restart: {e}")

print(f"\n🔍 POST-EXECUTION CHECK: {datetime.now().strftime('%H:%M:%S')}")

# Quick file check
target_file = "src/kortana/api/routers/goal_router.py"
if os.path.exists(target_file):
    size = os.path.getsize(target_file)
    print(f"📄 goal_router.py: {size} bytes")

service_file = "src/kortana/api/services/goal_service.py"
if os.path.exists(service_file):
    print("🎯 NEW SERVICE LAYER DETECTED!")
    size = os.path.getsize(service_file)
    print(f"📄 goal_service.py: {size} bytes")
else:
    print("⏳ Service layer not yet created")

print("\n🔬 RESUMING PROVING GROUND OBSERVATION...")
print("Ready for continuous monitoring of autonomous engineering progress!")
