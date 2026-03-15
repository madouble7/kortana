#!/usr/bin/env python3
"""
Manual Trigger for Proactive Code Review
Test Kor'tana's ability to create her own goals
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


async def trigger_proactive_review():
    """Manually trigger the proactive code review task."""
    print("🚀 MANUALLY TRIGGERING PROACTIVE CODE REVIEW")
    print("=" * 50)

    try:
        from kortana.core.autonomous_tasks import run_proactive_code_review_task
        from kortana.services.database import get_db_sync

        # Get database session
        db_gen = get_db_sync()
        db = next(db_gen)

        try:
            print("🔍 Running proactive code review task...")
            await run_proactive_code_review_task(db)
            print("✅ Proactive code review completed!")

            # Show created goals
            from kortana.core.models import Goal

            goals = (
                db.query(Goal)
                .filter(Goal.description.contains("docstring"))
                .order_by(Goal.id.desc())
                .limit(5)
                .all()
            )

            print(f"\n🎯 Recent docstring-related goals ({len(goals)}):")
            for goal in goals:
                print(f"  - Goal {goal.id}: {goal.description[:80]}...")
                print(f"    Status: {goal.status.value}, Priority: {goal.priority}")

        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(trigger_proactive_review())
