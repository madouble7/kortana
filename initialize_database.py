#!/usr/bin/env python3
"""
Initialize Database Tables for Kor'tana

This script creates the necessary database tables for goal management.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def initialize_database():
    """Initialize the database with required tables."""
    print("🗄️ INITIALIZING KOR'TANA DATABASE")
    print("=" * 40)

    try:
        from src.kortana.core.models import Goal
        from src.kortana.services.database import Base, sync_engine

        print("📦 Creating database tables...")

        # Create all tables
        Base.metadata.create_all(bind=sync_engine)

        print("✅ Database tables created successfully!")
        print("📋 Tables created:")
        print("   • goals - For storing autonomous goals")
        print("   • plan_steps - For storing goal execution plans")

        # Test database connectivity
        from src.kortana.services.database import get_db_sync
        db = next(get_db_sync())
        try:
            goal_count = db.query(Goal).count()
            print(f"\n🔍 Database test: Found {goal_count} existing goals")
            print("✅ Database is ready for proactive engineering!")
        finally:
            db.close()

        return True

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🤖 Kor'tana Database Initialization")
    print("Setting up tables for autonomous goal management...")
    print()

    success = initialize_database()

    if success:
        print("\n🎉 DATABASE READY!")
        print("🚀 Kor'tana can now store and manage autonomous goals")
    else:
        print("\n💥 DATABASE INITIALIZATION FAILED")
        sys.exit(1)
