#!/usr/bin/env python3
"""
Check actual database schema and create Genesis goal
"""

import sqlite3


def check_schema():
    """Check the actual schema of the goals table"""
    print("Checking actual database schema...")

    try:
        conn = sqlite3.connect("./kortana_memory_dev.db")
        cursor = conn.cursor()

        # Get schema for goals table
        cursor.execute("PRAGMA table_info(goals)")
        columns = cursor.fetchall()

        print("Goals table schema:")
        for col in columns:
            print(
                f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'} - Default: {col[4]}"
            )

        conn.close()
        return [col[1] for col in columns]

    except Exception as e:
        print(f"Error checking schema: {e}")
        return []


def create_genesis_goal_simple():
    """Create Genesis goal with correct schema"""
    print("\nCreating Genesis Protocol goal...")

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

        # Insert with just the columns that exist
        cursor.execute(
            """
            INSERT INTO goals (description, status, priority)
            VALUES (?, 'PENDING', 1)
        """,
            (goal_description,),
        )

        goal_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print("✅ Genesis goal created successfully!")
        print(f"   Goal ID: {goal_id}")
        print("   Status: PENDING")
        print("   Priority: 1 (Highest)")

        return goal_id

    except Exception as e:
        print(f"Error creating Genesis goal: {e}")
        return None


if __name__ == "__main__":
    columns = check_schema()
    if columns:
        goal_id = create_genesis_goal_simple()
        if goal_id:
            print(f"\n🚀 PHASE 4 GENESIS GOAL READY - ID: {goal_id}")
            print("🔬 Ready for autonomous system observation and execution")
        else:
            print("❌ Failed to create Genesis goal")
    else:
        print("❌ Could not check database schema")
