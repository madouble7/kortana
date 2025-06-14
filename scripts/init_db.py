#!/usr/bin/env python3
"""
Kor'tana Database Initialization
===============================

Creates and initializes kortana.db with context management schema.
Supports task context packages, summaries, and handoff metadata.

Usage:
    python init_db.py
    python init_db.py --reset  # Drop and recreate all tables
"""

import os
import sqlite3
from datetime import datetime


def init_kortana_db(db_path="kortana.db", reset=False):
    """Initialize the Kor'tana database with required tables"""

    if reset and os.path.exists(db_path):
        os.remove(db_path)
        print(f"[RESET] Removed existing {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Context table - stores task context packages and summaries
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS context (
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

    # Agent activity table - tracks agent performance and handoffs
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            task_id TEXT,
            action_type TEXT,
            message_count INTEGER DEFAULT 0,
            tokens_used INTEGER DEFAULT 0,
            timestamp TEXT,
            metadata TEXT
        )
    """
    )

    # Token usage tracking table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            model_name TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0.0,
            timestamp TEXT,
            task_id TEXT
        )
    """
    )

    # System state table - global configuration and status
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS system_state (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
    """
    )

    # Initialize default system state
    default_state = [
        ("active_task_id", None),
        ("current_agent", "claude"),
        ("autonomy_level", "semi-auto"),
        ("max_tokens_per_task", "8000"),
        ("handoff_threshold", "7000"),
        ("system_status", "initialized"),
    ]

    for key, value in default_state:
        cursor.execute(
            """
            INSERT OR IGNORE INTO system_state (key, value, updated_at)
            VALUES (?, ?, ?)
        """,
            (key, str(value), datetime.now().isoformat()),
        )

    conn.commit()

    # Verify tables were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    conn.close()

    print(f"[OK] Database initialized: {db_path}")
    print(f"[INFO] Tables created: {', '.join(tables)}")

    return db_path


def get_db_stats(db_path="kortana.db"):
    """Get basic statistics about the database"""
    if not os.path.exists(db_path):
        print(f"[ERROR] Database {db_path} not found")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"\n[DATABASE STATS] {db_path}")
    print("=" * 40)

    # Count records in each table
    tables = ["context", "agent_activity", "token_usage", "system_state"]

    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table:15}: {count:4} records")
        except sqlite3.OperationalError:
            print(f"{table:15}: Table not found")

    # Show current system state
    cursor.execute("SELECT key, value FROM system_state")
    state = dict(cursor.fetchall())

    print("\n[SYSTEM STATE]:")
    for key, value in state.items():
        print(f"  {key}: {value}")

    conn.close()


def main():
    """Main entry point with command line options"""
    import argparse

    parser = argparse.ArgumentParser(description="Initialize Kor'tana Database")
    parser.add_argument(
        "--reset", action="store_true", help="Reset database (drop and recreate)"
    )
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--db", default="kortana.db", help="Database file path")

    args = parser.parse_args()

    if args.stats:
        get_db_stats(args.db)
    else:
        init_kortana_db(args.db, reset=args.reset)
        if os.path.exists(args.db):
            get_db_stats(args.db)


if __name__ == "__main__":
    main()
