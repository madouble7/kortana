#!/usr/bin/env python3
"""
Quick database check for Batch 8 verification - File Output Version
"""

import sqlite3
from datetime import datetime

# Database path
db_path = r"c:\project-kortana\kortana.db"
output_file = r"c:\project-kortana\learning_check_results.txt"


def quick_check():
    """Quick check of database state."""
    results = []
    results.append("🔍 QUICK DATABASE CHECK - Batch 8 Learning Loop")
    results.append("=" * 55)
    results.append(f"Timestamp: {datetime.now()}")
    results.append("")

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check total memories
        cursor.execute("SELECT COUNT(*) as count FROM core_memories;")
        total_memories = cursor.fetchone()["count"]
        results.append(f"💭 Total memories: {total_memories}")

        # Check core beliefs
        cursor.execute(
            "SELECT COUNT(*) as count FROM core_memories WHERE memory_type = 'CORE_BELIEF';"
        )
        belief_count = cursor.fetchone()["count"]
        results.append(f"🧠 Core beliefs: {belief_count}")

        if belief_count > 0:
            results.append("\n✅ CORE BELIEFS FOUND:")
            cursor.execute("""
                SELECT title, content, created_at, memory_metadata
                FROM core_memories
                WHERE memory_type = 'CORE_BELIEF'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            beliefs = cursor.fetchall()

            for i, belief in enumerate(beliefs, 1):
                results.append(f"\n  #{i}: {belief['title']}")
                results.append(f"      Content: {belief['content'][:100]}...")
                results.append(f"      Created: {belief['created_at']}")
                # Check if self-generated
                is_self_generated = "performance_analysis_task" in (
                    belief["memory_metadata"] or ""
                )
                results.append(f"      Self-generated: {is_self_generated}")

        # Check for learning loop activity
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM core_memories
            WHERE memory_metadata LIKE '%performance_analysis_task%'
        """)
        learning_memories = cursor.fetchone()["count"]
        results.append(f"\n🔬 Learning loop memories: {learning_memories}")

        # Check for goal outcome memories
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM core_memories
            WHERE memory_metadata LIKE '%goal_processing_cycle%'
        """)
        goal_outcomes = cursor.fetchone()["count"]
        results.append(f"📊 Goal outcome memories: {goal_outcomes}")

        # Check recent goals
        cursor.execute("SELECT COUNT(*) as count FROM goals;")
        goal_count = cursor.fetchone()["count"]
        results.append(f"🎯 Total goals: {goal_count}")

        if goal_count > 0:
            cursor.execute("""
                SELECT description, status, created_at
                FROM goals
                ORDER BY created_at DESC
                LIMIT 5
            """)
            recent_goals = cursor.fetchall()
            results.append("\n📋 Recent goals:")
            for goal in recent_goals:
                results.append(f"   • {goal['description'][:60]}... [{goal['status']}]")
                results.append(f"     Created: {goal['created_at']}")

        # Analysis
        results.append("\n🔬 LEARNING LOOP STATUS ANALYSIS:")
        if learning_memories > 0:
            results.append("   ✅ LEARNING LOOP IS ACTIVE!")
            results.append("   Kor'tana has generated her own beliefs from experience.")
        elif belief_count > 0 and goal_outcomes > 0:
            results.append("   🟡 LEARNING LOOP IS READY")
            results.append("   Experiences exist, awaiting next scheduled analysis.")
        elif goal_outcomes > 0:
            results.append("   🟠 EXPERIENCES AVAILABLE")
            results.append("   Goal outcomes exist but no beliefs generated yet.")
        else:
            results.append("   🔴 NO LEARNING ACTIVITY DETECTED")
            results.append("   No experiences or beliefs found.")

        # Check recent memory types
        cursor.execute("""
            SELECT memory_type, COUNT(*) as count
            FROM core_memories
            GROUP BY memory_type
            ORDER BY count DESC
        """)
        memory_types = cursor.fetchall()
        results.append("\n📊 MEMORY TYPE BREAKDOWN:")
        for mem_type in memory_types:
            results.append(f"   {mem_type['memory_type']}: {mem_type['count']}")

        conn.close()

    except Exception as e:
        results.append(f"❌ Error: {e}")
        import traceback

        results.append(f"Traceback: {traceback.format_exc()}")

    return results


def main():
    """Main function to run check and save results."""
    results = quick_check()

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        for line in results:
            f.write(line + "\n")

    # Also print a summary
    print(f"Database check complete! Results written to: {output_file}")


if __name__ == "__main__":
    main()
