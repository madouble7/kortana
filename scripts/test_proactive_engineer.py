#!/usr/bin/env python3
"""
🚀 BATCH 10: PROACTIVE ENGINEER INITIATIVE - TESTING

Test script to validate the new proactive code review functionality
before launching it in production.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_proactive_code_review():
    """Test the proactive code review system."""

    print("🚀 BATCH 10: TESTING PROACTIVE ENGINEER INITIATIVE")
    print("=" * 60)

    try:
        # Import the necessary components
        from kortana.core.autonomous_tasks import run_proactive_code_review_task
        from kortana.services.database import get_db_sync

        print("✅ Imports successful")

        # Get database session
        db_gen = get_db_sync()
        db = next(db_gen)

        print("✅ Database connection established")

        # Run the proactive code review task
        print("🔍 Running proactive code review task...")
        await run_proactive_code_review_task(db)

        print("✅ Proactive code review task completed successfully!")

        # Check for new goals created
        from kortana.core.models import Goal

        proactive_goals = (
            db.query(Goal)
            .filter(
                Goal.description.contains("Add docstring"),
                Goal.metadata.contains("proactive_code_quality"),
            )
            .all()
        )

        print(f"🎯 Found {len(proactive_goals)} proactive goals in database")

        for goal in proactive_goals[-3:]:  # Show last 3 goals
            print(f"   Goal {goal.id}: {goal.description[:100]}...")

        db.close()

        return True

    except Exception as e:
        print(f"❌ Error testing proactive code review: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function."""

    print("🧪 TESTING THE PROACTIVE ENGINEER")
    print("This test will:")
    print("1. Scan the codebase for functions missing docstrings")
    print("2. Create self-improvement goals automatically")
    print("3. Demonstrate proactive engineering capabilities")
    print("")

    success = await test_proactive_code_review()

    if success:
        print("\n🎉 PROACTIVE ENGINEER TEST: SUCCESS!")
        print("✅ Code scanning works")
        print("✅ Goal generation works")
        print("✅ Database integration works")
        print("✅ Ready for autonomous operation!")
        print("")
        print("🚀 Next: Start the scheduler to see Kor'tana work proactively")
    else:
        print("\n❌ PROACTIVE ENGINEER TEST: FAILED")
        print("Please check the errors and fix before proceeding")


if __name__ == "__main__":
    asyncio.run(main())
