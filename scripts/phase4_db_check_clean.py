#!/usr/bin/env python3
"""
Phase 4 Database Check - Emoji-free version
Checks necessary tables and Genesis goal status without emojis.
"""

import os
import sqlite3
import sys

sys.path.append("src")


print("--- Phase 4 Database Status Check ---")
print("-------------------------------------")

db_file = "kortana_memory_dev.db"
if not os.path.exists(db_file):
    print(f"Error: Database file not found at {db_file}")
    sys.exit(1)

try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # List all tables
    print("Checking for tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Found tables: {tables}")

    required_tables = ["goals", "plan_steps", "core_memory"]
    missing_tables = [table for table in required_tables if table not in tables]

    if missing_tables:
        print(f"Error: The following required tables are missing: {missing_tables}")
        conn.close()
        sys.exit(1)
    else:
        print("Required tables (goals, plan_steps, core_memory) are present.")

    print("-------------------------------------")

    # Check for Genesis goal
    print("Checking for Genesis goal...")
    cursor.execute("""
        SELECT id, description, status, priority, created_at
        FROM goals
        WHERE description LIKE '%GENESIS PROTOCOL TASK%'
        ORDER BY id DESC
        LIMIT 1
    """)
    genesis_goal = cursor.fetchone()

    if genesis_goal:
        goal_id, description, status, priority, created_at = genesis_goal
        print("Genesis Protocol Goal Found:")
        print(f"  ID: {goal_id}")
        print(f"  Status: {status}")
        print(f"  Priority: {priority}")
        print(f"  Created: {created_at}")
        print(f"  Description: {description[:100]}...")
    else:
        print("No Genesis Protocol goal found in the database.")

    print("-------------------------------------")

    # Check recent autonomous activity in core_memory
    print("Checking recent autonomous memory activity (last 24 hours)...")
    cursor.execute("""
        SELECT memory_type, content, created_at
        FROM core_memory
        WHERE created_at > datetime('now', '-1 day')
        ORDER BY created_at DESC
        LIMIT 5
    """)
    recent_memories = cursor.fetchall()

    if recent_memories:
        print("Recent memories found:")
        for mem in recent_memories:
            print(f"  Type: {mem[0]} | Created: {mem[2]}")
            print(f"  Content: {mem[1][:80]}...")
    else:
        print("No recent autonomous memory activity found.")

    print("-------------------------------------")

    conn.close()

except Exception as e:
    print(f"An error occurred during database check: {e}")
    import traceback

    traceback.print_exc()

print("--- Database check complete ---")
