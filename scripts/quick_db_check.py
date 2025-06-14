#!/usr/bin/env python3
"""
Quick database check for Batch 8 verification
"""

import sqlite3

# Database path
db_path = r"c:\project-kortana\kortana.db"


def quick_check():
    """Quick check of database state."""
    print("🔍 QUICK DATABASE CHECK - Batch 8 Learning Loop")
    print("=" * 55)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check total memories
        cursor.execute("SELECT COUNT(*) as count FROM core_memories;")
        total_memories = cursor.fetchone()["count"]
        print(f"💭 Total memories: {total_memories}")

        # Check core beliefs
        cursor.execute(
            "SELECT COUNT(*) as count FROM core_memories WHERE memory_type = 'CORE_BELIEF';"
        )
        belief_count = cursor.fetchone()["count"]
        print(f"🧠 Core beliefs: {belief_count}")

        if belief_count > 0:
            print("\n✅ CORE BELIEFS FOUND:")
            cursor.execute("""
                SELECT title, content, created_at
                FROM core_memories
                WHERE memory_type = 'CORE_BELIEF'
                ORDER BY created_at DESC
                LIMIT 3
            """)
            beliefs = cursor.fetchall()

            for i, belief in enumerate(beliefs, 1):
                print(f"\n  #{i}: {belief['title']}")
                print(f"      {belief['content'][:80]}...")
                print(f"      Created: {belief['created_at']}")

        # Check for learning loop activity
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM core_memories
            WHERE memory_metadata LIKE '%performance_analysis_task%'
        """)
        learning_memories = cursor.fetchone()["count"]
        print(f"\n🔬 Learning loop memories: {learning_memories}")

        # Check recent goals
        cursor.execute("SELECT COUNT(*) as count FROM goals;")
        goal_count = cursor.fetchone()["count"]
        print(f"🎯 Total goals: {goal_count}")

        if goal_count > 0:
            cursor.execute("""
                SELECT description, status, created_at
                FROM goals
                ORDER BY created_at DESC
                LIMIT 3
            """)
            recent_goals = cursor.fetchall()
            print("\n📋 Recent goals:")
            for goal in recent_goals:
                print(f"   • {goal['description'][:50]}... [{goal['status']}]")

        # Analysis
        print("\n🔬 LEARNING LOOP STATUS:")
        if learning_memories > 0:
            print("   ✅ Learning loop has been active!")
        elif belief_count > 0:
            print("   🟡 Beliefs exist, checking if self-generated...")
        else:
            print("   🔴 No learning activity detected yet")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    quick_check()
