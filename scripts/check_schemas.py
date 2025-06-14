#!/usr/bin/env python3
"""
Check and fix plan_steps table schema
"""

import sqlite3


def check_plan_steps_schema():
    """Check the actual schema of plan_steps table"""
    print("Checking plan_steps table schema...")

    try:
        conn = sqlite3.connect("./kortana_memory_dev.db")
        cursor = conn.cursor()

        # Get schema for plan_steps table
        cursor.execute("PRAGMA table_info(plan_steps)")
        columns = cursor.fetchall()

        print("Plan_steps table schema:")
        for col in columns:
            print(
                f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'} - Default: {col[4]}"
            )

        conn.close()
        return [col[1] for col in columns]

    except Exception as e:
        print(f"Error checking schema: {e}")
        return []


def check_all_tables():
    """Check all table schemas"""
    print("Checking all table schemas...")

    try:
        conn = sqlite3.connect("./kortana_memory_dev.db")
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            if table != "sqlite_sequence":
                print(f"\n{table} table:")
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  {col[1]} ({col[2]})")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    check_plan_steps_schema()
    print("\n" + "=" * 50)
    check_all_tables()
