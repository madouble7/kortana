#!/usr/bin/env python3
"""
🚀 MANUAL PROACTIVE CODE REVIEW TRIGGER
Manually run the proactive code review to test the functionality
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def run_manual_proactive_review():
    """Manually trigger proactive code review."""

    print("🚀 MANUAL PROACTIVE CODE REVIEW")
    print("=" * 40)

    try:
        # Import the proactive task
        from kortana.config import load_config
        from kortana.core.autonomous_tasks import run_proactive_code_review_task

        print("✅ Importing proactive code review task...")

        # Load config
        config = load_config()
        print("✅ Configuration loaded")

        # Run the proactive code review task
        print("🔍 Running proactive code review...")
        result = await run_proactive_code_review_task(config)

        print(f"📊 Proactive review result: {result}")
        print("✅ Proactive code review completed!")

        # Check if any goals were created
        import sqlite3

        conn = sqlite3.connect("kortana.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM goals WHERE created_at > datetime('now', '-1 minute')"
        )
        recent_goals = cursor.fetchone()[0]
        print(f"📋 New goals created in last minute: {recent_goals}")
        conn.close()

    except Exception as e:
        print(f"❌ Error running proactive review: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_manual_proactive_review())
