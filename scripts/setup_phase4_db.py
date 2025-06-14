#!/usr/bin/env python3
"""
Phase 4 Database Setup - Simple Approach
Create necessary tables for Phase 4 observation without complex imports
"""

import os
import sqlite3
from datetime import datetime

# Database file path
DB_PATH = "./kortana_memory_dev.db"

def create_tables():
    """Create necessary tables for Phase 4 observation"""
    print("Setting up Phase 4 database tables...")

    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create goals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'PENDING',
            priority INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create plan_steps table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER,
            step_number INTEGER,
            description TEXT,
            action_type VARCHAR(50),
            parameters TEXT,
            status VARCHAR(20) DEFAULT 'PENDING',
            result TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            executed_at DATETIME,
            FOREIGN KEY (goal_id) REFERENCES goals (id)
        )
    ''')

    # Create core_memory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS core_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_type VARCHAR(50),
            content TEXT,
            relevance_score REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()

    # Verify tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"Created tables: {tables}")

    required_tables = ['goals', 'plan_steps', 'core_memory']
    missing_tables = [t for t in required_tables if t not in tables]

    if not missing_tables:
        print("✅ All required tables created successfully!")

        # Check if Genesis goal already exists
        cursor.execute("SELECT id, description, status FROM goals WHERE description LIKE '%GENESIS%'")
        genesis_goals = cursor.fetchall()

        if genesis_goals:
            print(f"Found existing Genesis goals: {len(genesis_goals)}")
            for goal in genesis_goals:
                print(f"  ID {goal[0]}: {goal[1][:50]}... (Status: {goal[2]})")
        else:
            print("No existing Genesis goals found")
    else:
        print(f"❌ Missing tables: {missing_tables}")

    conn.close()
    return len(missing_tables) == 0

def create_genesis_goal():
    """Create the Genesis Protocol goal directly in SQLite"""
    print("\nCreating Genesis Protocol goal...")

    goal_description = """GENESIS PROTOCOL TASK: Refactor goal_router.py for better architecture

As an autonomous software engineer, implement the following improvements to goal_router.py:

1. ANALYZE: Examine the current goal_router.py structure and identify opportunities for improvement
2. DESIGN: Create a new goal_service.py module to separate business logic from API routing
3. REFACTOR: Move goal management logic from router to service layer
4. UPDATE: Modify goal_router.py to use the new service layer
5. TEST: Run the full test suite to ensure no regressions
6. VALIDATE: Confirm the API endpoints still work correctly

This task demonstrates end-to-end autonomous software engineering: analysis, design, implementation, testing, and validation.

Success Criteria:
- goal_service.py created with proper separation of concerns
- goal_router.py refactored to use service layer
- All existing tests pass
- API endpoints maintain same functionality
- Code follows project conventions and best practices

EXECUTION PLAN:
The autonomous system will use the following action types:
- SEARCH_CODEBASE: To analyze current code structure
- APPLY_PATCH: To implement code changes
- RUN_TESTS: To validate implementations
- CREATE_FILE: To create new service modules"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if Genesis goal already exists
    cursor.execute("SELECT id FROM goals WHERE description LIKE '%GENESIS PROTOCOL TASK%'")
    existing = cursor.fetchone()

    if existing:
        print(f"✅ Genesis goal already exists with ID: {existing[0]}")
        conn.close()
        return existing[0]

    # Insert the Genesis goal
    cursor.execute('''
        INSERT INTO goals (description, status, priority, created_at, updated_at)
        VALUES (?, 'PENDING', 1, ?, ?)
    ''', (goal_description, datetime.now(), datetime.now()))

    goal_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"✅ Genesis goal created with ID: {goal_id}")
    return goal_id

def monitor_setup():
    """Show the current state for monitoring"""
    print("\n" + "="*60)
    print("🔬 PHASE 4: THE PROVING GROUND - OBSERVATION READY")
    print("="*60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Show goals
    cursor.execute("SELECT id, status, created_at, substr(description, 1, 80) FROM goals")
    goals = cursor.fetchall()

    print(f"\n📊 Current Goals in Database: {len(goals)}")
    for goal in goals:
        print(f"  ID {goal[0]}: {goal[3]}... (Status: {goal[1]}, Created: {goal[2]})")

    # Show plan steps
    cursor.execute("SELECT COUNT(*) FROM plan_steps")
    plan_count = cursor.fetchone()[0]
    print(f"\n📋 Plan Steps: {plan_count}")

    # Show memory entries
    cursor.execute("SELECT COUNT(*) FROM core_memory")
    memory_count = cursor.fetchone()[0]
    print(f"\n🧠 Core Memory Entries: {memory_count}")

    conn.close()

    print("\n🚀 Phase 4 Observation Protocol:")
    print("   ✅ Database tables ready")
    print("   ✅ Genesis goal created")
    print("   🔍 Ready to monitor autonomous processing")
    print("   ⏳ Waiting for Kor'tana to begin autonomous execution...")

if __name__ == "__main__":
    if create_tables():
        goal_id = create_genesis_goal()
        monitor_setup()
    else:
        print("❌ Failed to create required tables")
