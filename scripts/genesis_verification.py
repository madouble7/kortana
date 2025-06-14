#!/usr/bin/env python3
"""
GENESIS PROTOCOL VERIFICATION
Checks the status of Kor'tana's first autonomous software engineering goal
"""

import sqlite3
from datetime import datetime


def check_genesis_status():
    """Verify the Genesis Protocol goal and system status"""
    print("🔍 GENESIS PROTOCOL STATUS CHECK")
    print("=" * 50)

    try:
        # Connect to database
        conn = sqlite3.connect("kortana.db")
        cursor = conn.cursor()

        # Check for Genesis goal
        cursor.execute("""
            SELECT
                id,
                title,
                status,
                priority,
                created_at,
                description
            FROM goals
            WHERE title LIKE '%GENESIS%'
            ORDER BY id DESC
            LIMIT 1
        """)

        genesis_goal = cursor.fetchone()

        if genesis_goal:
            print("✅ GENESIS PROTOCOL GOAL FOUND!")
            print(f"📋 Goal ID: {genesis_goal[0]}")
            print(f"🎯 Title: {genesis_goal[1]}")
            print(f"📊 Status: {genesis_goal[2]}")
            print(f"⚡ Priority: {genesis_goal[3]}")
            print(f"📅 Created: {genesis_goal[4]}")
            print()
            print("📄 DESCRIPTION:")
            print("-" * 30)
            print(
                genesis_goal[5][:500] + "..."
                if len(genesis_goal[5]) > 500
                else genesis_goal[5]
            )
            print()
        else:
            print("❌ No Genesis Protocol goal found!")
            print("⚠️  Need to create the autonomous software engineering task")
            return False

        # Check recent goals
        cursor.execute("""
            SELECT COUNT(*) as total_goals
            FROM goals
        """)
        total_goals = cursor.fetchone()[0]

        print("📊 SYSTEM STATUS:")
        print(f"   Total Goals: {total_goals}")

        # Check recent autonomous activity
        cursor.execute("""
            SELECT
                COUNT(*) as recent_memories
            FROM core_memory
            WHERE created_at > datetime('now', '-1 hour')
        """)
        recent_activity = cursor.fetchone()[0]
        print(f"   Recent Memory Activity (1h): {recent_activity}")

        # Check learning
        cursor.execute("""
            SELECT
                COUNT(*) as core_beliefs
            FROM core_memory
            WHERE memory_type = 'CORE_BELIEF'
        """)
        core_beliefs = cursor.fetchone()[0]
        print(f"   Core Beliefs Learned: {core_beliefs}")

        print()
        print("🚀 STATUS: Kor'tana is ready for autonomous software engineering!")
        print("🔄 The system will process the Genesis goal in the next cycle...")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def insert_genesis_goal_if_missing():
    """Insert the Genesis goal if it doesn't exist"""
    try:
        conn = sqlite3.connect("kortana.db")
        cursor = conn.cursor()

        # Check if Genesis goal exists
        cursor.execute("SELECT COUNT(*) FROM goals WHERE title LIKE '%GENESIS%'")
        if cursor.fetchone()[0] > 0:
            print("✅ Genesis goal already exists")
            conn.close()
            return True

        print("📝 Creating Genesis Protocol goal...")

        # Get next ID
        cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM goals")
        next_id = cursor.fetchone()[0]

        # Insert Genesis goal
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

        cursor.execute(
            """
            INSERT INTO goals (
                id, goal_type, title, description, status, priority, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                next_id,
                "IMPROVEMENT",
                "GENESIS: Refactor goal_router.py architecture",
                goal_description,
                "PENDING",
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        print(f"✅ Genesis Protocol goal created with ID: {next_id}")
        return True

    except Exception as e:
        print(f"❌ Failed to create Genesis goal: {e}")
        return False


if __name__ == "__main__":
    print("🚀 INITIALIZING GENESIS PROTOCOL...")
    print()

    # Create goal if missing
    if insert_genesis_goal_if_missing():
        print()
        # Check status
        check_genesis_status()
        print()
        print("🎉 GENESIS PROTOCOL IS ACTIVE!")
        print("🤖 Kor'tana is now ready for autonomous software engineering!")
    else:
        print("❌ Failed to initialize Genesis Protocol")
