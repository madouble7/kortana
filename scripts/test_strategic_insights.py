#!/usr/bin/env python3
"""Test the strategic insight processing capability"""

import asyncio
import os
import sys

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)

print("Testing Phase 5 strategic insight processing...")

async def test_strategic_insights():
    try:
        from phase5_advanced_autonomous import AdvancedAutonomousKortana
        print("✅ Phase 5 import successful")

        kortana = AdvancedAutonomousKortana()
        print("✅ Phase 5 instance created")

        # Test context gathering first
        print("\n🔍 Testing context gathering...")
        context = await kortana._gather_comprehensive_context()
        print(f"✅ Context gathered with {len(context)} categories")

        # Test strategic insight processing
        print("\n🎯 Testing strategic insight processing...")
        insights = []  # Empty list as per the method signature
        strategic_focus = await kortana._process_strategic_insights(insights)

        print("✅ Strategic insights processed successfully!")
        print(f"Strategic Focus: {strategic_focus.get('current_focus', 'Unknown')}")
        print(f"Priority: {strategic_focus.get('strategic_priority', 'Unknown')}")

        # Test the internal state update
        print("\n📊 Updated autonomous state:")
        print(f"Current Focus: {kortana.autonomous_state.get('current_strategic_focus', 'Not set')}")
        print(f"Priority: {kortana.autonomous_state.get('strategic_priority', 'Not set')}")

        # Test the prompt building
        print("\n📝 Testing prompt building...")
        prompt = kortana._build_strategic_analysis_prompt(context)
        print(f"✅ Prompt built successfully ({len(prompt)} characters)")

        # Test default focus derivation
        print("\n🔧 Testing default focus derivation...")
        default_focus = kortana._derive_default_strategic_focus(context)
        print(f"✅ Default focus: {default_focus}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_strategic_insights()
    if success:
        print("\n🎉 Strategic insight processing test completed successfully!")
        print("Kor'tana can now perceive her world AND form strategic conclusions!")
    else:
        print("\n💥 Test failed - needs debugging")

if __name__ == "__main__":
    asyncio.run(main())
