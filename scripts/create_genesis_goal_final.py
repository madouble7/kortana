#!/usr/bin/env python3
"""
Create Genesis Protocol Goal for Phase 4 Observation
"""

import sqlite3
from datetime import datetime


def create_genesis_goal():
    """Create the Genesis Protocol goal in the database"""
    print("Creating Genesis Protocol goal...")

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

    try:
        conn = sqlite3.connect("./kortana_memory_dev.db")
        cursor = conn.cursor()

        # Check if Genesis goal already exists
        cursor.execute(
            "SELECT id, status FROM goals WHERE description LIKE '%GENESIS PROTOCOL TASK%'"
        )
        existing = cursor.fetchone()

        if existing:
            print(
                f"Genesis goal already exists with ID: {existing[0]}, Status: {existing[1]}"
            )
            conn.close()
            return existing[0]

        # Insert the Genesis goal
        now = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO goals (description, status, priority, created_at, updated_at)
            VALUES (?, 'PENDING', 1, ?, ?)
        """,
            (goal_description, now, now),
        )

        goal_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print("✅ Genesis goal created successfully!")
        print(f"   Goal ID: {goal_id}")
        print("   Status: PENDING")
        print("   Priority: 1 (Highest)")
        print(f"   Created: {now}")

        return goal_id

    except Exception as e:
        print(f"Error creating Genesis goal: {e}")
        return None


def monitor_database_state():
    """Show current database state for Phase 4 monitoring"""
    print("\n" + "=" * 70)
    print("🔬 PHASE 4: THE PROVING GROUND - DATABASE STATE")
    print("=" * 70)

    try:
        conn = sqlite3.connect("./kortana_memory_dev.db")
        cursor = conn.cursor()

        # Goals
        cursor.execute(
            "SELECT id, status, priority, created_at, substr(description, 1, 80) FROM goals ORDER BY created_at DESC"
        )
        goals = cursor.fetchall()

        print(f"\n📊 Goals in Database: {len(goals)}")
        for goal in goals:
            print(f"   ID {goal[0]}: {goal[4]}...")
            print(f"      Status: {goal[1]} | Priority: {goal[2]} | Created: {goal[3]}")

        # Plan Steps
        cursor.execute("SELECT COUNT(*) FROM plan_steps")
        plan_count = cursor.fetchone()[0]
        print(f"\n📋 Plan Steps: {plan_count}")

        if plan_count > 0:
            cursor.execute(
                "SELECT goal_id, step_number, action_type, status FROM plan_steps ORDER BY goal_id, step_number"
            )
            steps = cursor.fetchall()
            for step in steps[:5]:  # Show first 5 steps
                print(f"   Goal {step[0]}, Step {step[1]}: {step[2]} ({step[3]})")

        # Memory Entries
        cursor.execute("SELECT COUNT(*) FROM core_memory")
        memory_count = cursor.fetchone()[0]
        print(f"\n🧠 Core Memory Entries: {memory_count}")

        conn.close()

        print("\n🚀 Phase 4 Observation Status:")
        print("   ✅ Database ready with all required tables")
        print("   ✅ Genesis Protocol goal created and pending")
        print("   🔍 Ready to observe autonomous processing")
        print("   ⏳ Waiting for Kor'tana's autonomous execution engine...")

    except Exception as e:
        print(f"Error checking database state: {e}")


if __name__ == "__main__":
    goal_id = create_genesis_goal()
    if goal_id:
        monitor_database_state()
    else:
        print("Failed to create Genesis goal")
