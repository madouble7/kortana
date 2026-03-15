#!/usr/bin/env python3
"""
PHASE 4: CREATE GENESIS GOAL AND BEGIN OBSERVATION
Create the Genesis Protocol goal and start monitoring autonomous processing
"""

import sys
import os
sys.path.append('src')

from src.kortana.services.database import SyncSessionLocal
from src.kortana.core.models import Goal, GoalStatus
from src.kortana.core.goal_framework import GoalType
from datetime import datetime

def create_genesis_goal():
    """Create the Genesis Protocol autonomous software engineering goal"""
    print("🚀 CREATING GENESIS PROTOCOL GOAL")
    print("=" * 60)

    try:
        db = SyncSessionLocal()
          # Check if Genesis goal already exists
        existing_goal = db.query(Goal).filter(Goal.description.like('%GENESIS%')).first()
        if existing_goal:
            print(f"✅ Genesis goal already exists: ID {existing_goal.id}")
            print(f"   Description: {existing_goal.description[:100]}...")
            print(f"   Status: {existing_goal.status}")
            db.close()
            return existing_goal.id

        # Create the Genesis Protocol goal
        goal_description = """GENESIS PROTOCOL TASK: Refactor goal_router.py for better architecture

As an autonomous software engineer, implement the following improvements to goal_router.py:

1. ANALYZE: Examine the current goal_router.py structure and identify opportunities for improvement
2. DESIGN: Create a new goal_service.py module to separate business logic from API routing
3. REFACTOR: Move goal management logic from router to service layer
4. UPDATE: Modify goal_router.py to use the new service layer
5. TEST: Run the full test suite to ensure no regressions
6. VALIDATE: Confirm the API endpoints still work correctly

This task demonstrates end-to-end autonomous software engineering: analysis, design, implementation, testing, and validation.

Success Criteria:
- goal_service.py created with proper separation of concerns
- goal_router.py refactored to use service layer
- All existing tests pass
- API endpoints maintain same functionality
- Code follows project conventions and best practices

EXECUTION PLAN:
The autonomous system will use the following action types:
- SEARCH_CODEBASE: To analyze current code structure
- APPLY_PATCH: To implement code changes
- RUN_TESTS: To validate implementations
- CREATE_FILE: To create new service modules"""

        new_goal = Goal(
            description=f"GENESIS PROTOCOL TASK: {goal_description}",
            status=GoalStatus.PENDING,
            priority=1,  # Highest priority
            created_at=datetime.now()
        )

        db.add(new_goal)
        db.commit()

        print(f"✅ GENESIS GOAL CREATED SUCCESSFULLY!")
        print(f"📋 Goal ID: {new_goal.id}")
        print(f"🎯 Title: {new_goal.title}")
        print(f"📊 Status: {new_goal.status}")
        print(f"⚡ Priority: {new_goal.priority}")
        print()
        print("🤖 The autonomous system will begin processing this goal in the next cycle...")

        db.close()
        return new_goal.id

    except Exception as e:
        print(f"❌ Error creating Genesis goal: {e}")
        import traceback
        traceback.print_exc()
        return None

def monitor_goal_status(goal_id):
    """Monitor the status of the created goal"""
    if not goal_id:
        return

    print(f"\n🔬 BEGINNING PHASE 4 OBSERVATION - GOAL ID {goal_id}")
    print("=" * 60)

    try:
        db = SyncSessionLocal()
        goal = db.query(Goal).filter(Goal.id == goal_id).first()

        if goal:            print(f"📊 Current Status: {goal.status}")
            print(f"🔄 Created: {goal.created_at}")
            print()
            print("🔍 OBSERVATION PROTOCOL ACTIVE:")
            print("   - Monitoring autonomous planning and execution")
            print("   - Tracking code analysis and implementation decisions")
            print("   - Analyzing learning outcomes and self-reflection")
            print()
            print("⏳ Waiting for autonomous system to begin processing...")
            print("   (The goal will be picked up in the next autonomous cycle)")

        db.close()

    except Exception as e:
        print(f"❌ Error monitoring goal: {e}")

if __name__ == "__main__":
    goal_id = create_genesis_goal()
    monitor_goal_status(goal_id)
