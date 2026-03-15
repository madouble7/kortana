#!/usr/bin/env python3
"""
Test the goals API directly to see the specific error
"""

import traceback

from src.kortana.core.models import Goal, GoalStatus
from src.kortana.services.database import SyncSessionLocal


def test_goals_directly():
    """Test the goals functionality directly"""
    try:
        # Create a session
        db = SyncSessionLocal()

        print("✅ Database session created")

        # Try to query goals
        goals = db.query(Goal).all()
        print(f"✅ Goals query successful: {len(goals)} goals found")

        # Try to create a goal
        test_goal = Goal(
            description="Test goal", status=GoalStatus.PENDING, priority=100
        )

        db.add(test_goal)
        db.commit()
        db.refresh(test_goal)

        print(f"✅ Goal created successfully: ID {test_goal.id}")

        # Query again
        goals = db.query(Goal).all()
        print(f"✅ Updated goals count: {len(goals)}")

        db.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    test_goals_directly()
