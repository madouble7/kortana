#!/usr/bin/env python3
"""
Test Database Creation
=====================

Simple test to verify kortana.db creation and functionality.
"""

import os
import sqlite3
from datetime import datetime


def test_db_creation():
    """Test creating and using the database"""
    db_path = "kortana.db"

    print("🧪 Testing Kor'tana Database Creation")
    print("=" * 40)

    # Remove existing if present
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Removed existing database")

    # Create connection and table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create context table
    cursor.execute(
        """
        CREATE TABLE context (
            task_id TEXT PRIMARY KEY,
            summary TEXT,
            code TEXT,
            issues TEXT,
            commit_ref TEXT,
            timestamp TEXT,
            tokens INTEGER
        )
    """
    )

    # Insert test record
    test_data = (
        "test_task_001",
        "Test summary for autonomous system",
        "print('Hello Kor'tana')",
        "No pending issues",
        "github.com/test/commit/abc123",
        datetime.now().isoformat(),
        150,
    )

    cursor.execute(
        """
        INSERT INTO context VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        test_data,
    )

    conn.commit()

    # Verify data
    cursor.execute("SELECT * FROM context")
    records = cursor.fetchall()

    conn.close()

    # Show results
    print(f"✅ Database created: {db_path}")
    print(f"📊 Records inserted: {len(records)}")

    if records:
        record = records[0]
        print("📝 Test record:")
        print(f"   Task ID: {record[0]}")
        print(f"   Summary: {record[1][:50]}...")
        print(f"   Tokens: {record[6]}")

    print("\n🎯 Database test successful!")
    return True


if __name__ == "__main__":
    test_db_creation()
