#!/usr/bin/env python3
"""
Phase 4 Database Check - Proper investigation of the Genesis goal status
"""

import os
import sqlite3


def check_kortana_database():
    """Check the correct Kor'tana database for Genesis goal status"""
    print("🔍 CHECKING kortana_memory_dev.db FOR GENESIS GOAL")
    print("=" * 60)

    db_file = "kortana_memory_dev.db"
    if not os.path.exists(db_file):
        print(f"❌ {db_file} not found!")
        return

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"📊 Tables found: {tables}")
        print()

        # Check goals table
        if "goals" in tables:
            cursor.execute("SELECT COUNT(*) FROM goals;")
            goals_count = cursor.fetchone()[0]
            print("🎯 GOALS TABLE ANALYSIS:")
            print(f"   Total goals: {goals_count}")

            if goals_count > 0:
                # Look for Genesis goal specifically
                cursor.execute("""
                    SELECT id, title, status, priority, created_at, description
                    FROM goals
                    WHERE title LIKE '%GENESIS%' OR description LIKE '%GENESIS%'
                    ORDER BY id DESC
                """)
                genesis_goals = cursor.fetchall()

                if genesis_goals:
                    print(f"   🚀 GENESIS GOALS FOUND: {len(genesis_goals)}")
                    for goal in genesis_goals:
                        print(f"      📋 ID {goal[0]}: {goal[1]}")
                        print(f"         Status: {goal[2]} | Priority: {goal[3]}")
                        print(f"         Created: {goal[4]}")
                        print(f"         Description: {goal[5][:100]}...")
                        print()
                else:
                    print("   ⚠️ No Genesis goals found")

                # Show all recent goals
                cursor.execute(
                    "SELECT id, title, status FROM goals ORDER BY id DESC LIMIT 5;"
                )
                recent_goals = cursor.fetchall()
                print("   📋 Recent goals:")
                for goal in recent_goals:
                    print(f"      {goal[0]}: {goal[1]} - {goal[2]}")
            else:
                print("   ⚠️ No goals in database yet")
        else:
            print("❌ Goals table not found!")

        print()

        # Check plan_steps if goals exist
        if "plan_steps" in tables:
            cursor.execute("SELECT COUNT(*) FROM plan_steps;")
            steps_count = cursor.fetchone()[0]
            print("📋 PLAN STEPS TABLE:")
            print(f"   Total plan steps: {steps_count}")

            if steps_count > 0:
                cursor.execute("""
                    SELECT ps.goal_id, ps.step_number, ps.action_type, ps.status, g.title
                    FROM plan_steps ps
                    LEFT JOIN goals g ON ps.goal_id = g.id
                    ORDER BY ps.goal_id DESC, ps.step_number
                    LIMIT 10
                """)
                recent_steps = cursor.fetchall()
                print("   Recent plan steps:")
                for step in recent_steps:
                    print(f"      Goal {step[0]} Step {step[1]}: {step[2]} - {step[3]}")
                    if step[4]:
                        print(f"         Goal: {step[4]}")

        print()

        # Check core_memory for autonomous reasoning
        if "core_memory" in tables:
            cursor.execute("SELECT COUNT(*) FROM core_memory;")
            memory_count = cursor.fetchone()[0]
            print("💭 CORE MEMORY TABLE:")
            print(f"   Total memories: {memory_count}")

            # Look for recent autonomous activity
            cursor.execute("""
                SELECT memory_type, content, created_at
                FROM core_memory
                WHERE created_at > datetime('now', '-24 hours')
                ORDER BY created_at DESC
                LIMIT 5
            """)
            recent_memories = cursor.fetchall()

            if recent_memories:
                print("   Recent autonomous memories (24h):")
                for mem in recent_memories:
                    print(f"      🧠 {mem[0]} | {mem[2]}")
                    print(f"         {mem[1][:80]}...")
                    print()

            # Look specifically for Genesis-related memories
            cursor.execute("""
                SELECT memory_type, content, created_at
                FROM core_memory
                WHERE content LIKE '%GENESIS%' OR content LIKE '%refactor%' OR content LIKE '%goal_router%'
                ORDER BY created_at DESC
                LIMIT 3
            """)
            genesis_memories = cursor.fetchall()

            if genesis_memories:
                print("   Genesis-related memories:")
                for mem in genesis_memories:
                    print(f"      🚀 {mem[0]} | {mem[2]}")
                    print(f"         {mem[1][:100]}...")
                    print()

        conn.close()

    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    check_kortana_database()
