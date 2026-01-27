#!/usr/bin/env python3
"""
Check Genesis Protocol Goal Status
"""

import sys

sys.path.append("src")

from kortana.core.models import Goal
from kortana.services.database import SyncSessionLocal


def check_genesis_goal():
    """Check if the Genesis Protocol goal was created"""
    print("🔍 CHECKING GENESIS PROTOCOL GOAL STATUS")
    print("=" * 50)

    db = SyncSessionLocal()
    try:
        goals = db.query(Goal).all()
        print(f"📊 Total goals in database: {len(goals)}")

        if goals:
            print("\n📋 Recent Goals:")
            for goal in goals[-3:]:  # Show last 3 goals
                print(f"  • Goal {goal.id}: {goal.description[:60]}...")
                print(f"    Status: {goal.status}")
                print(f"    Created: {goal.created_at}")
                print()
        else:
            print("❌ No goals found in database")

    except Exception as e:
        print(f"❌ Error checking goals: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    check_genesis_goal()
