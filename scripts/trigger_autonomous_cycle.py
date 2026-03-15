#!/usr/bin/env python3
"""
PHASE 4: MANUAL AUTONOMOUS CYCLE TRIGGER
Manually trigger Kor'tana's autonomous goal processing cycle
"""

import asyncio
import sys

sys.path.append("src")

from src.kortana.core.autonomous_tasks import autonomous_goal_processing_cycle


async def trigger_autonomous_cycle():
    """Manually trigger the autonomous goal processing cycle"""
    print("🚀 MANUALLY TRIGGERING AUTONOMOUS GOAL PROCESSING CYCLE")
    print("=" * 60)

    try:
        await autonomous_goal_processing_cycle()
        print("✅ Autonomous cycle completed successfully")
    except Exception as e:
        print(f"❌ Error during autonomous cycle: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(trigger_autonomous_cycle())
