#!/usr/bin/env python3
"""
Phase 4 Database Table Creation and Verification
Ensures necessary tables exist for goal and memory storage.
"""

import sys

sys.path.append("src")

from src.kortana.core.models import Goal  # Explicitly import Goal for testing
from src.kortana.services.database import Base, SyncSessionLocal, sync_engine

print("🚀 Attempting to create all database tables...")

try:
    # Create all tables defined in Base.metadata
    Base.metadata.create_all(bind=sync_engine)
    print("✅ Base.metadata.create_all executed.")

    # Verify tables exist
    db = SyncSessionLocal()
    cursor = db.connection().cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"📊 Tables found after creation attempt: {tables}")

    if "goals" in tables and "plan_steps" in tables and "core_memory" in tables:
        print("✅ Required tables (goals, plan_steps, core_memory) confirmed to exist.")

        # Check if Goal model is queryable
        try:
            goals_count = db.query(Goal).count()
            print(
                f"🎯 Test query on 'goals' table successful. Current goal count: {goals_count}"
            )
        except Exception as e:
            print(f"❌ Error querying 'goals' table: {e}")
            import traceback

            traceback.print_exc()

    else:
        print(
            "❌ One or more required tables (goals, plan_steps, core_memory) are missing."
        )

    db.close()

except Exception as e:
    print(f"❌ An error occurred during table creation or verification: {e}")
    import traceback

    traceback.print_exc()

print("🔬 Database table creation and verification script finished.")
