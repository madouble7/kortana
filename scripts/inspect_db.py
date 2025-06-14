#!/usr/bin/env python3
"""
Direct database inspection for Phase 4
"""

import sqlite3


def inspect_database():
    """Inspect the current state of the database"""
    print("Inspecting kortana_memory_dev.db...")

    try:
        conn = sqlite3.connect("./kortana_memory_dev.db")
        cursor = conn.cursor()

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        print(f"Tables found: {tables}")

        # If goals table exists, check for Genesis goals
        if 'goals' in tables:
            cursor.execute("SELECT id, status, substr(description, 1, 100) FROM goals")
            goals = cursor.fetchall()
            print(f"\nGoals in database: {len(goals)}")
            for goal in goals:
                print(f"  ID {goal[0]}: {goal[1]} - {goal[2]}...")

        # If no tables, create them
        if not tables:
            print("No tables found. Creating tables...")
            create_basic_tables(cursor)
            conn.commit()
            print("Tables created.")

        conn.close()
        return len(tables) > 0

    except Exception as e:
        print(f"Error: {e}")
        return False

def create_basic_tables(cursor):
    """Create basic tables"""
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

if __name__ == "__main__":
    inspect_database()
