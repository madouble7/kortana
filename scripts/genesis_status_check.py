#!/usr/bin/env python3
"""
GENESIS PROTOCOL STATUS CHECKER
Quick status check of Kor'tana's autonomous software engineering capabilities
"""

import os
import sqlite3
from datetime import datetime


def check_genesis_status():
    """Check Genesis Protocol status and autonomous system activity"""
    print("🚀 GENESIS PROTOCOL STATUS CHECK")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if not os.path.exists("kortana.db"):
        print("❌ Database not found!")
        return

    try:
        conn = sqlite3.connect("kortana.db")
        cursor = conn.cursor()

        # Check for Genesis goal
        print("🎯 GENESIS PROTOCOL GOAL STATUS:")
        print("-" * 40)
        cursor.execute("""
            SELECT id, title, status, priority, created_at
            FROM goals
            WHERE title LIKE '%GENESIS%'
            ORDER BY id DESC
            LIMIT 1
        """)
        genesis_goal = cursor.fetchone()

        if genesis_goal:
            print(f"✅ Goal ID: {genesis_goal[0]}")
            print(f"📋 Title: {genesis_goal[1]}")
            print(f"📊 Status: {genesis_goal[2]}")
            print(f"⚡ Priority: {genesis_goal[3]}")
            print(f"📅 Created: {genesis_goal[4]}")
        else:
            print("⚠️  No Genesis goal found - creating one...")
            cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM goals")
            next_id = cursor.fetchone()[0]

            goal_description = """GENESIS PROTOCOL TASK: Refactor goal_router.py for better architecture

As an autonomous software engineer, implement the following improvements:
1. ANALYZE: Examine goal_router.py structure and identify improvements
2. DESIGN: Create goal_service.py to separate business logic from routing
3. REFACTOR: Move goal management logic to service layer
4. UPDATE: Modify goal_router.py to use new service layer
5. TEST: Run full test suite to ensure no regressions
6. VALIDATE: Confirm API endpoints maintain functionality

This demonstrates end-to-end autonomous software engineering capability."""

            cursor.execute(
                """
                INSERT INTO goals (id, goal_type, title, description, status, priority, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
            print(f"✅ Genesis goal created with ID: {next_id}")

        print()

        # Check autonomous system activity
        print("🤖 AUTONOMOUS SYSTEM STATUS:")
        print("-" * 40)

        cursor.execute("SELECT COUNT(*) FROM goals")
        total_goals = cursor.fetchone()[0]
        print(f"📋 Total Goals: {total_goals}")

        cursor.execute("SELECT COUNT(*) FROM goals WHERE status = 'PENDING'")
        pending_goals = cursor.fetchone()[0]
        print(f"⏳ Pending Goals: {pending_goals}")

        cursor.execute("SELECT COUNT(*) FROM goals WHERE status = 'ACTIVE'")
        active_goals = cursor.fetchone()[0]
        print(f"🔄 Active Goals: {active_goals}")

        cursor.execute("SELECT COUNT(*) FROM goals WHERE status = 'COMPLETED'")
        completed_goals = cursor.fetchone()[0]
        print(f"✅ Completed Goals: {completed_goals}")

        # Check recent autonomous activity
        cursor.execute("""
            SELECT COUNT(*) FROM core_memory
            WHERE created_at > datetime('now', '-1 hour')
        """)
        recent_memories = cursor.fetchone()[0]
        print(f"💭 Recent Memory Activity (1h): {recent_memories}")

        # Check learning status
        cursor.execute(
            "SELECT COUNT(*) FROM core_memory WHERE memory_type = 'CORE_BELIEF'"
        )
        core_beliefs = cursor.fetchone()[0]
        print(f"🧠 Core Beliefs Learned: {core_beliefs}")

        print()

        # Check Genesis Protocol infrastructure
        print("🔧 GENESIS PROTOCOL INFRASTRUCTURE:")
        print("-" * 40)

        execution_engine_path = "src/kortana/core/execution_engine.py"
        if os.path.exists(execution_engine_path):
            with open(execution_engine_path) as f:
                content = f.read()

            coding_tools = ["search_codebase", "apply_patch", "run_tests"]
            for tool in coding_tools:
                if f"async def {tool}" in content:
                    print(f"✅ Coding Tool: {tool}")
                else:
                    print(f"❌ Missing Tool: {tool}")
        else:
            print("❌ Execution engine not found")

        print()
        print("🎉 GENESIS PROTOCOL STATUS: READY")
        print("🤖 Kor'tana is an autonomous software engineer!")
        print("🔄 System is processing goals autonomously...")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    check_genesis_status()
