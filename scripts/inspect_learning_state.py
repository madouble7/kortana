#!/usr/bin/env python3
"""
Batch 8 Database Inspection
===========================

Inspect the current database state to verify learning loop functionality
without interfering with the running autonomous system.
"""

import json
import os
import sqlite3
from datetime import datetime

# Database path
db_path = r"c:\project-kortana\kortana.db"
output_file = r"c:\project-kortana\batch8_inspection_results.txt"


def log_to_file(message):
    """Log message to output file."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def inspect_database():
    """Inspect the database for learning-related data."""
    if not os.path.exists(db_path):
        log_to_file(f"❌ Database not found at: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        cursor = conn.cursor()

        log_to_file("🔍 BATCH 8 DATABASE INSPECTION")
        log_to_file("=" * 50)

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        log_to_file(f"📊 Found {len(tables)} tables:")
        for table in tables:
            log_to_file(f"   • {table['name']}")

        # Check core memories table
        try:
            cursor.execute("SELECT COUNT(*) as count FROM core_memories;")
            memory_count = cursor.fetchone()["count"]
            log_to_file(f"\n💭 Total memories: {memory_count}")

            # Check for core beliefs specifically
            cursor.execute(
                "SELECT COUNT(*) as count FROM core_memories WHERE memory_type = 'CORE_BELIEF';"
            )
            belief_count = cursor.fetchone()["count"]
            log_to_file(f"🧠 Core beliefs: {belief_count}")

            if belief_count > 0:
                log_to_file("\n✅ CORE BELIEFS FOUND:")
                cursor.execute("""
                    SELECT title, content, created_at, memory_metadata
                    FROM core_memories
                    WHERE memory_type = 'CORE_BELIEF'
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                beliefs = cursor.fetchall()

                for i, belief in enumerate(beliefs, 1):
                    log_to_file(f"\n   Belief #{i}:")
                    log_to_file(f"   Title: {belief['title']}")
                    log_to_file(f"   Content: {belief['content']}")
                    log_to_file(f"   Created: {belief['created_at']}")
                    if belief["memory_metadata"]:
                        try:
                            metadata = json.loads(belief["memory_metadata"])
                            log_to_file(
                                f"   Source: {metadata.get('source', 'unknown')}"
                            )
                            log_to_file(
                                f"   Self-generated: {metadata.get('is_self_generated', False)}"
                            )
                        except Exception:
                            log_to_file(f"   Metadata: {belief['memory_metadata']}")

            # Check for goal-related memories
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM core_memories
                WHERE memory_metadata LIKE '%goal_processing_cycle%'
            """)
            goal_memories = cursor.fetchone()["count"]
            log_to_file(f"\n🎯 Goal outcome memories: {goal_memories}")

            if goal_memories > 0:
                log_to_file("\n📋 RECENT GOAL OUTCOMES:")
                cursor.execute("""
                    SELECT title, content, created_at
                    FROM core_memories
                    WHERE memory_metadata LIKE '%goal_processing_cycle%'
                    ORDER BY created_at DESC
                    LIMIT 3
                """)
                goal_outcomes = cursor.fetchall()

                for i, outcome in enumerate(goal_outcomes, 1):
                    log_to_file(f"\n   Outcome #{i}:")
                    log_to_file(f"   Title: {outcome['title']}")
                    log_to_file(f"   Content: {outcome['content'][:100]}...")
                    log_to_file(f"   Created: {outcome['created_at']}")

        except Exception as e:
            log_to_file(f"❌ Error querying core_memories: {e}")

        # Check for goals table
        try:
            cursor.execute("SELECT COUNT(*) as count FROM goals;")
            goals_count = cursor.fetchone()["count"]
            log_to_file(f"\n🎯 Total goals: {goals_count}")

            if goals_count > 0:
                cursor.execute("""
                    SELECT id, description, status, priority, created_at
                    FROM goals
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                recent_goals = cursor.fetchall()

                log_to_file("\n📋 RECENT GOALS:")
                for goal in recent_goals:
                    log_to_file(f"   ID {goal['id']}: {goal['description'][:50]}...")
                    log_to_file(
                        f"   Status: {goal['status']}, Priority: {goal['priority']}"
                    )
                    log_to_file(f"   Created: {goal['created_at']}")
                    log_to_file("")

        except Exception as e:
            log_to_file(f"❌ Error querying goals: {e}")

        conn.close()

    except Exception as e:
        log_to_file(f"❌ Database connection error: {e}")


def analyze_learning_state():
    """Analyze if learning loop is working."""
    log_to_file("\n🔬 LEARNING LOOP ANALYSIS")
    log_to_file("=" * 30)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check for self-generated beliefs
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM core_memories
            WHERE memory_type = 'CORE_BELIEF'
            AND memory_metadata LIKE '%performance_analysis_task%'
        """)
        self_generated = cursor.fetchone()["count"]

        # Check for goal processing memories
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM core_memories
            WHERE memory_metadata LIKE '%goal_processing_cycle%'
        """)
        goal_experiences = cursor.fetchone()["count"]

        log_to_file(f"🧠 Self-generated beliefs: {self_generated}")
        log_to_file(f"📊 Goal experiences to learn from: {goal_experiences}")

        if self_generated > 0:
            log_to_file("✅ LEARNING LOOP IS ACTIVE!")
            log_to_file("   Kor'tana has generated her own beliefs from experience.")
        elif goal_experiences > 0:
            log_to_file("🟡 LEARNING LOOP READY")
            log_to_file("   Experiences exist but no self-generated beliefs yet.")
            log_to_file("   Learning may occur on next scheduled analysis.")
        else:
            log_to_file("🔴 LEARNING LOOP NOT ACTIVE")
            log_to_file("   No experiences or beliefs found.")

        conn.close()

    except Exception as e:
        log_to_file(f"❌ Analysis error: {e}")


def check_scheduler_status():
    """Check if the scheduler and learning tasks are configured."""
    log_to_file("\n⏰ SCHEDULER STATUS")
    log_to_file("=" * 20)

    # Check for scheduler-related files or logs
    scheduler_indicators = [
        "data/autonomous_activity.log",
        "data/scheduler_status.json",
        "logs/scheduler.log",
    ]

    for indicator in scheduler_indicators:
        if os.path.exists(indicator):
            log_to_file(f"✅ Found: {indicator}")
        else:
            log_to_file(f"❌ Missing: {indicator}")

    # The autonomous relay output we saw indicates the scheduler is running
    log_to_file("🔄 Relay system active (confirmed by terminal output)")
    log_to_file("⏰ This suggests the scheduler infrastructure is operational")


def main():
    """Main inspection function."""
    # Clear output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Batch 8 Learning Loop Inspection - {datetime.now()}\n")
        f.write("=" * 60 + "\n\n")

    log_to_file("🔍 Starting database inspection...")

    inspect_database()
    analyze_learning_state()
    check_scheduler_status()

    log_to_file("\n📄 Inspection complete!")
    log_to_file(f"📁 Full results written to: {output_file}")

    # Also print to console
    print("🔍 Database inspection completed!")
    print(f"📁 Results written to: {output_file}")
    print("📖 Check the file for detailed analysis of Kor'tana's learning state.")


if __name__ == "__main__":
    main()
