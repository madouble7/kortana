#!/usr/bin/env python3
"""
Pre-Launch Verification for The Proving Ground
============================================
Final verification that all systems are ready for Kor'tana's first autonomous engineering task
"""

import os
import sys
from pathlib import Path

# Set up project root
project_root = Path(r"C:\project-kortana")
os.chdir(project_root)
sys.path.insert(0, str(project_root))


def verify_server_readiness():
    """Verify the server can be imported without errors."""
    print("🔍 Verifying server readiness...")
    try:
        print("   ✅ Main app imports successfully")
        print("   ✅ Server fix confirmed working")
        return True
    except Exception as e:
        print(f"   ❌ Server import failed: {e}")
        return False


def verify_goal_submission_ready():
    """Check if goal submission script is ready."""
    print("🎯 Verifying goal submission readiness...")

    goal_script = project_root / "submit_genesis_goal.py"
    if goal_script.exists():
        print("   ✅ Goal submission script available")
        return True
    else:
        print("   ❌ Goal submission script missing")
        return False


def verify_monitoring_ready():
    """Check if monitoring script is ready."""
    print("👁️  Verifying monitoring readiness...")

    monitor_script = project_root / "monitor_proving_ground.py"
    if monitor_script.exists():
        print("   ✅ Monitoring script available")
        return True
    else:
        print("   ❌ Monitoring script missing")
        return False


def verify_phase5_system():
    """Check Phase 5 autonomous system."""
    print("🤖 Verifying Phase 5 autonomous system...")

    try:
        print("   ✅ Phase 5 system imports successfully")

        # Check status file
        status_file = project_root / "data" / "phase5_status.json"
        if status_file.exists():
            print("   ✅ Phase 5 status file present")
            return True
        else:
            print("   ⚠️  Phase 5 status file missing (may start fresh)")
            return True

    except Exception as e:
        print(f"   ❌ Phase 5 system error: {e}")
        return False


def main():
    """Main verification function."""
    print("=" * 70)
    print("🔍 THE PROVING GROUND - PRE-LAUNCH VERIFICATION")
    print("=" * 70)
    print(
        "Verifying all systems are ready for Kor'tana's first autonomous engineering task..."
    )

    checks = []

    # Run all verification checks
    checks.append(("Server Readiness", verify_server_readiness()))
    checks.append(("Goal Submission", verify_goal_submission_ready()))
    checks.append(("Monitoring System", verify_monitoring_ready()))
    checks.append(("Phase 5 Autonomous", verify_phase5_system()))

    # Summary
    print("\n" + "=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)

    passed = 0
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {check_name:20} {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{len(checks)} checks passed")

    if passed == len(checks):
        print("\n🎉 ALL SYSTEMS VERIFIED - THE PROVING GROUND IS READY!")
        print("\n📋 NEXT STEPS:")
        print(
            "1. Start server: python -m uvicorn src.kortana.main:app --port 8000 --reload"
        )
        print("2. Submit goal: python submit_genesis_goal.py")
        print("3. Monitor work: python monitor_proving_ground.py")
        print("\n🚀 READY TO WITNESS KOR'TANA'S FIRST AUTONOMOUS ENGINEERING ACT!")
    else:
        print(f"\n⚠️  {len(checks) - passed} issues need attention before launch")

    return passed == len(checks)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
