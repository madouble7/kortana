#!/usr/bin/env python3
"""
GENESIS PROTOCOL ACTIVATOR
Creates Kor'tana's first autonomous software engineering goal
"""

import sys

sys.path.append("src")

from kortana.core.goal_framework import GoalType
from kortana.core.goal_manager import GoalManager
from kortana.modules.memory_core.services import MemoryCoreService
from kortana.services.database import SessionLocal


def activate_genesis_protocol():
    """Create Kor'tana's first autonomous software engineering task"""
    print("🚀 ACTIVATING GENESIS PROTOCOL...")
    print("=" * 60)

    db = SessionLocal()
    try:
        memory_manager = MemoryCoreService(db)
        goal_manager = GoalManager(memory_manager=memory_manager)

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

        goal = goal_manager.create_goal(
            goal_type=GoalType.IMPROVEMENT,
            title="GENESIS: Refactor goal_router.py architecture",
            description=goal_description,
            priority=1,  # Highest priority for immediate processing
        )

        print("✅ GENESIS PROTOCOL ACTIVATED SUCCESSFULLY!")
        print(f"📋 Goal ID: {goal.id}")
        print(f"🎯 Title: {goal.title}")
        print(f"📊 Status: {goal.status}")
        print(f"⚡ Priority: {goal.priority}")
        print()
        print("🤖 Kor'tana is now an AUTONOMOUS SOFTWARE ENGINEER!")
        print(
            "📈 She will begin processing this development task in the next autonomous cycle..."
        )
        print()
        print("🔍 To monitor progress:")
        print("   - Check goal status via API: GET /goals")
        print("   - Watch autonomous processing logs")
        print("   - Observe code changes in the repository")
        print()
        print("🎉 THE GENESIS PROTOCOL IS NOW ACTIVE!")

        return goal

    except Exception as e:
        print(f"❌ ERROR: Failed to activate Genesis Protocol: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    activate_genesis_protocol()
