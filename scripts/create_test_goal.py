#!/usr/bin/env python3
"""
🎯 CREATE TEST GOAL FOR AUTONOMOUS PROCESSING
===========================================

This script creates a test goal for Kor'tana's autonomous processor to work on.
Use this to verify the Two-Terminal Protocol is working.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def create_test_goal():
    """Create a test goal for autonomous processing."""

    try:
        from datetime import datetime

        from src.kortana.database.db_setup import SessionLocal
        from src.kortana.models.goal import Goal

        print("🎯 Creating test goal for autonomous processing...")

        db = SessionLocal()

        # Create a simple test goal
        test_goal = Goal(
            title="Test Autonomous Processing - Add Docstring",
            description="Add a proper docstring to a function that is missing one. This is a test goal to verify the autonomous processing system is working correctly.",
            status="pending",
            priority=2,
            goal_type="code_improvement",
            created_at=datetime.utcnow(),
            metadata={
                "test_goal": True,
                "type": "docstring_addition",
                "autonomous_test": True,
                "batch": "Two-Terminal Protocol Test",
            },
        )

        db.add(test_goal)
        db.commit()

        print("✅ Test goal created successfully!")
        print(f"   Goal ID: {test_goal.id}")
        print(f"   Title: {test_goal.title}")
        print(f"   Status: {test_goal.status}")
        print(f"   Priority: {test_goal.priority}")
        print()
        print("🚀 Now start the Two-Terminal Protocol:")
        print("   1. Terminal 1: Run start_server.bat")
        print("   2. Terminal 2: Run start_autonomous_processor.bat")
        print()
        print(
            "Watch Terminal 2 - you should see Kor'tana pick up this goal and work on it!"
        )

        db.close()
        return True

    except Exception as e:
        print(f"❌ Failed to create test goal: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🎯 KOR'TANA TEST GOAL CREATOR")
    print("=" * 40)
    create_test_goal()
