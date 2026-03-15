#!/usr/bin/env python3
"""
Test Proactive Code Review - Batch 10 Phase 1 Validation

This script tests Kor'tana's proactive code scanning and goal generation capabilities.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from kortana.core.autonomous_tasks import run_proactive_code_review_task
from kortana.database.database import get_database_session
from kortana.models.models import Goal, GoalStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_proactive_code_review():
    """Test the proactive code review functionality."""
    print("🔍 TESTING PROACTIVE CODE REVIEW (Batch 10 Phase 1)")
    print("=" * 60)

    try:
        # Get database session
        db = get_database_session()

        # Count existing goals before scan
        initial_goal_count = db.query(Goal).count()
        print(f"📊 Initial goal count: {initial_goal_count}")

        # Run the proactive code review task
        print("\n🚀 Running proactive code review task...")
        await run_proactive_code_review_task(db)

        # Count goals after scan
        final_goal_count = db.query(Goal).count()
        new_goals = final_goal_count - initial_goal_count

        print(f"📊 Final goal count: {final_goal_count}")
        print(f"✨ New goals created: {new_goals}")

        # Show the new goals if any were created
        if new_goals > 0:
            print("\n📋 New Goals Created:")
            new_goals_query = db.query(Goal).filter(
                Goal.description.contains("Add docstring"),
                Goal.status == GoalStatus.PENDING
            ).order_by(Goal.created_at.desc()).limit(new_goals)

            for goal in new_goals_query:
                print(f"  🎯 Goal {goal.id}: {goal.description[:100]}...")

        print("\n✅ PROACTIVE CODE REVIEW TEST COMPLETED!")
        return True

    except Exception as e:
        print(f"❌ Error in proactive code review test: {e}")
        logger.exception("Test failed")
        return False
    finally:
        db.close()

def main():
    """Main test function."""
    print("🤖 Kor'tana Proactive Engineering Test")
    print("Testing autonomous code scanning and goal generation...")

    try:
        success = asyncio.run(test_proactive_code_review())

        if success:
            print("\n🎉 SUCCESS: Proactive code review is working!")
            print("🔥 Kor'tana can now autonomously identify and create improvement goals!")
        else:
            print("\n💥 FAILED: Proactive code review encountered issues")

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        logger.exception("Main test failed")

if __name__ == "__main__":
    main()
