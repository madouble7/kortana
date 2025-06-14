#!/usr/bin/env python3
"""Test the context gathering capability"""

import asyncio
import os
import sys

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)

print("Testing Phase 5 context gathering...")

try:
    from phase5_advanced_autonomous import AdvancedAutonomousKortana

    print("✅ Phase 5 import successful")

    async def test_context():
        kortana = AdvancedAutonomousKortana()
        print("✅ Phase 5 instance created")

        print("Testing context gathering...")
        context = await kortana._gather_comprehensive_context()

        print("✅ Context gathered successfully!")
        print(f"Context categories: {list(context.keys())}")
        print(f"System status: {context.get('system_status', {}).keys()}")
        print(f"Recent activities: {len(context.get('recent_activity', []))}")
        print(f"Pending goals: {len(context.get('pending_goals', []))}")
        print(f"Core beliefs: {len(context.get('core_beliefs', []))}")

        # Show some details
        if context.get("environmental_factors"):
            env = context["environmental_factors"]
            print(f"Environment - Brain operational: {env.get('brain_operational')}")
            print(f"Environment - Uptime: {env.get('uptime_seconds', 0):.1f}s")

    asyncio.run(test_context())
    print("🎉 Context gathering test completed successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
