#!/usr/bin/env python3
"""
Database structure investigation for Phase 4 observation
"""

import os
import sqlite3


def investigate_database():
    """Check the actual database structure"""
    print("🔍 DATABASE STRUCTURE INVESTIGATION")
    print("=" * 50)

    if not os.path.exists("kortana.db"):
        print("❌ kortana.db not found!")
        return

    try:
        conn = sqlite3.connect("kortana.db")
        cursor = conn.cursor()

        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print("📊 EXISTING TABLES:")
        for table in tables:
            print(f"  - {table[0]}")

        print()

        # Check for any goal-related data
        if any("goal" in table[0].lower() for table in tables):
            print("🎯 GOAL-RELATED TABLES FOUND:")
            for table in tables:
                if "goal" in table[0].lower():
                    table_name = table[0]
                    print(f"\n📋 Table: {table_name}")

                    # Get table schema
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    print("  Columns:")
                    for col in columns:
                        print(f"    - {col[1]} ({col[2]})")

                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    print(f"  Rows: {count}")

                    # Show recent entries if any
                    if count > 0:
                        cursor.execute(
                            f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 3;"
                        )
                        rows = cursor.fetchall()
                        print("  Recent entries:")
                        for row in rows:
                            print(f"    {row}")

        # Also check core_memory for any Genesis-related content
        print("\n💭 CHECKING CORE_MEMORY FOR GENESIS CONTENT:")
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='core_memory';"
        )
        if cursor.fetchone():
            cursor.execute("""
                SELECT id, memory_type, content, created_at
                FROM core_memory
                WHERE content LIKE '%GENESIS%' OR content LIKE '%refactor%' OR content LIKE '%goal_router%'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            memory_entries = cursor.fetchall()

            if memory_entries:
                for entry in memory_entries:
                    print(f"  🧠 {entry[1]} | {entry[3]}")
                    print(
                        f"     {entry[2][:100]}{'...' if len(entry[2]) > 100 else ''}"
                    )
                    print()
            else:
                print("  ⏳ No Genesis-related memories found")
        else:
            print("  ⚠️ core_memory table not found")

        conn.close()

    except Exception as e:
        print(f"❌ Error investigating database: {e}")


if __name__ == "__main__":
    investigate_database()
