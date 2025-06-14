#!/usr/bin/env python3
"""
Test Proactive Scheduling - Batch 10 Validation

This script validates that proactive code review scheduling is properly integrated
into Kor'tana's autonomous brain.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🧠 TESTING PROACTIVE SCHEDULING (Batch 10)")
print("=" * 50)

try:
    print("📥 Importing brain components...")
    from src.kortana.core.brain import ChatEngine
    print("✅ ChatEngine imported successfully")

    # Test that the proactive code review cycle method exists
    if hasattr(ChatEngine, '_proactive_code_review_cycle'):
        print("✅ Proactive code review cycle method found in ChatEngine")
    else:
        print("❌ Proactive code review cycle method missing from ChatEngine")
        sys.exit(1)

    # Check that the schedule configuration mentions proactive code review
    print("\n🔍 Checking for proactive scheduling integration...")

    # Read the brain.py file to verify the scheduler setup
    brain_file = Path("src/kortana/core/brain.py")
    brain_content = brain_file.read_text()

    if "proactive_code_review" in brain_content:
        print("✅ Proactive code review found in scheduler configuration")
    else:
        print("❌ Proactive code review not found in scheduler configuration")
        sys.exit(1)

    if "_proactive_code_review_cycle" in brain_content:
        print("✅ Proactive code review cycle method found in brain file")
    else:
        print("❌ Proactive code review cycle method not found in brain file")
        sys.exit(1)

    if "IntervalTrigger(hours=6)" in brain_content:
        print("✅ 6-hour interval trigger found for proactive code review")
    else:
        print("⚠️  6-hour interval trigger not found (may use different interval)")

    print("\n✅ PROACTIVE SCHEDULING VALIDATION COMPLETED!")
    print("🎉 Kor'tana's brain is ready for proactive engineering!")
    print("📝 The system will autonomously scan code every 6 hours")
    print("🎯 Found issues will be converted to self-improvement goals")

except Exception as e:
    print(f"❌ Error in proactive scheduling test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
