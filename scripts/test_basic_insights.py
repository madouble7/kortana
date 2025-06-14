#!/usr/bin/env python3
"""Simple test for strategic insights"""

import os
import sys

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)

try:
    print("Testing strategic insights import...")
    from phase5_advanced_autonomous import AdvancedAutonomousKortana
    print("✅ Import successful")

    print("Creating instance...")
    kortana = AdvancedAutonomousKortana()
    print("✅ Instance created")

    print("Testing default strategic focus...")
    context = {
        "performance_analysis": {"system_health_score": 0.9, "cognitive_load": 0.3},
        "pending_goals": [{"description": "test goal"}]
    }

    focus = kortana._derive_default_strategic_focus(context)
    print(f"✅ Default focus: {focus}")

    print("Testing insight parsing...")
    test_text = '{"current_focus": "GOAL_EXECUTION", "strategic_priority": "Test priority"}'
    parsed = kortana._parse_strategic_insights(test_text)
    print(f"✅ Parsed insights: {parsed}")

    print("🎉 Basic tests passed!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
