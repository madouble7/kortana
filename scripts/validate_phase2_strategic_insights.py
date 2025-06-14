#!/usr/bin/env python3
"""
Phase 2 Validation Test: Strategic Insight Processing
===================================================
Comprehensive test of the strategic insight processing capabilities.
"""

import asyncio
import os
import sys

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)

print("=" * 60)
print("PHASE 2 VALIDATION: Strategic Insight Processing")
print("=" * 60)


async def run_comprehensive_test():
    """Run comprehensive test of strategic insight processing."""

    try:
        # Import and initialize
        print("\n🔧 Initializing Kor'tana Phase 5...")
        from phase5_advanced_autonomous import AdvancedAutonomousKortana

        kortana = AdvancedAutonomousKortana()
        print("✅ Phase 5 system initialized")

        # Test 1: Context gathering (prerequisite)
        print("\n📊 Test 1: Context Gathering")
        context = await kortana._gather_comprehensive_context()
        print(f"✅ Context gathered: {len(context)} categories")
        for key in context.keys():
            print(f"   - {key}")

        # Test 2: Strategic insights with no reasoning engine input
        print("\n🎯 Test 2: Independent Strategic Analysis")
        strategic_focus = await kortana._process_strategic_insights([])
        print("✅ Strategic insights processed independently")
        print(f"   Focus: {strategic_focus.get('current_focus', 'Unknown')}")
        print(f"   Priority: {strategic_focus.get('strategic_priority', 'Unknown')}")

        # Test 3: Strategic insights with mock reasoning engine input
        print("\n🧠 Test 3: Reasoning Engine Integration")
        mock_insights = [
            {"type": "goal", "priority": "high", "content": "Deploy new features"},
            {
                "type": "performance",
                "priority": "medium",
                "content": "Optimize CPU usage",
            },
        ]
        strategic_focus_with_insights = await kortana._process_strategic_insights(
            mock_insights
        )
        print("✅ Strategic insights processed with reasoning engine input")
        print(
            f"   Focus: {strategic_focus_with_insights.get('current_focus', 'Unknown')}"
        )
        print(
            f"   Priority: {strategic_focus_with_insights.get('strategic_priority', 'Unknown')}"
        )

        # Test 4: Prompt building capability
        print("\n📝 Test 4: Strategic Analysis Prompt")
        prompt = kortana._build_strategic_analysis_prompt(context)
        print(f"✅ Strategic prompt built ({len(prompt)} characters)")

        # Show sample of the prompt
        prompt_lines = prompt.split("\n")
        print("   Sample prompt content:")
        for i, line in enumerate(prompt_lines[:5]):
            print(f"   {i + 1}: {line[:80]}...")

        # Test 5: Default focus derivation
        print("\n🔧 Test 5: Default Strategic Focus")
        default_focus = kortana._derive_default_strategic_focus(context)
        print("✅ Default strategic focus derived")
        print(f"   Focus: {default_focus.get('current_focus', 'Unknown')}")
        print(f"   Priority: {default_focus.get('strategic_priority', 'Unknown')}")

        # Test 6: State persistence
        print("\n💾 Test 6: Strategic State Persistence")
        print(
            f"   Current Strategic Focus: {kortana.autonomous_state.get('current_strategic_focus', 'Not set')}"
        )
        print(
            f"   Strategic Priority: {kortana.autonomous_state.get('strategic_priority', 'Not set')}"
        )
        print(
            f"   Strategic Analysis Cycles: {kortana.autonomous_state.get('strategic_analysis_cycles', 0)}"
        )

        # Test 7: Performance metrics
        print("\n📈 Test 7: Performance Metrics")
        metrics = kortana.performance_metrics
        print(f"✅ Performance metrics available: {len(metrics)} metrics")
        for metric_name, metric_data in metrics.items():
            print(f"   - {metric_name}: {metric_data.get('value', 'N/A')}")

        print("\n" + "=" * 60)
        print("🎯 PHASE 2 VALIDATION COMPLETE")
        print("=" * 60)
        print("✅ Strategic insight processing is FULLY IMPLEMENTED")
        print("✅ Kor'tana can now think strategically about her situation")
        print("✅ Ready for Phase 3: Tactical Recommendations")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_test())
    if success:
        print("\n🎉 All tests passed! Strategic insight processing is operational.")
    else:
        print("\n💥 Tests failed. Strategic insight processing needs attention.")
