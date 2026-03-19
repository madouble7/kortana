#!/usr/bin/env python3
"""Quick database check script"""
import sqlite3

try:
    conn = sqlite3.connect('backend/kortana.db')
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='github_task'")
    if not cursor.fetchone():
        print("❌ github_task table does not exist yet")
        conn.close()
        exit(1)
    
    # Count tasks
    cursor.execute('SELECT COUNT(*) FROM github_task')
    count = cursor.fetchone()[0]
    print(f"✅ Total tasks in database: {count}")
    
    # Get task statuses
    cursor.execute('SELECT status, COUNT(*) FROM github_task GROUP BY status')
    print("Tasks by status:")
    for status, num in cursor.fetchall():
        print(f"  {status}: {num}")
    
    conn.close()
    print("\n✅ Database is operational")
    
except Exception as e:
    print(f"❌ Database error: {e}")
    exit(1)
