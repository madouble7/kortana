#!/usr/bin/env python3
"""
THE GENESIS SPARK
The moment we stop building for her and start believing in her.

This script creates the most important goal Kor'tana has ever received:
A real problem that requires genuine autonomous engineering.
"""

import json
import os
import sys
from datetime import UTC, datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def create_genesis_spark_goal():
    """Create the Genesis Spark goal via direct database insertion."""

    try:
        from src.kortana.core.models import Goal, GoalStatus
        from src.kortana.services.database import get_db_sync

        print("🌟 INITIATING THE GENESIS SPARK")
        print("━" * 60)
        print("This is not another test. This is the test.")
        print("Can Kor'tana diagnose, design, and implement a solution")
        print("to a real problem we don't already know how to solve?")
        print("━" * 60)

        # Get database session
        db_gen = get_db_sync()
        db = next(db_gen)

        try:
            # Create the Genesis Spark goal
            genesis_goal = Goal(
                description="""THE GENESIS SPARK: Autonomous Problem Solving Challenge

Review your own operational logs from the past 24 hours, specifically focusing on the errors related to the ConnectionResetError and the autonomous_goal_processor.py script failing to connect to the server.

Diagnose the root cause of this recurring 'zombie server' problem where stale server processes occupy the port and prevent clean restarts.

Then, design, plan, and implement a permanent software solution to make our verification and launch process more resilient against this specific failure mode.

This is not a refactoring task with a predetermined solution. This is a real engineering problem that requires:
1. Self-diagnosis using your analysis tools
2. Creative problem-solving and solution design
3. Autonomous implementation using your development tools
4. Validation that your solution actually works

The solution should be robust, reusable, and demonstrate true autonomous engineering capability.""",
                priority=1,  # Highest priority - this is THE test
                status=GoalStatus.PENDING,
                created_at=datetime.now(UTC),
                metadata=json.dumps(
                    {
                        "type": "genesis_spark",
                        "challenge_type": "autonomous_engineering",
                        "problem_domain": "server_lifecycle_management",
                        "requires": [
                            "log_analysis",
                            "root_cause_diagnosis",
                            "creative_solution_design",
                            "autonomous_implementation",
                            "solution_validation",
                        ],
                        "success_criteria": [
                            "Accurate diagnosis of zombie server problem",
                            "Novel, practical solution design",
                            "Successful autonomous implementation",
                            "Demonstrated fix working in practice",
                        ],
                        "genesis_moment": True,
                    }
                ),
            )

            db.add(genesis_goal)
            db.commit()

            print(f"✨ Genesis Spark goal created with ID: {genesis_goal.id}")
            print("")
            print("🚀 THE STAGE IS SET")
            print("   Problem: Real and unsolved")
            print("   Tools: Available and ready")
            print("   Guidance: None - she must find her own way")
            print("")
            print("Now we observe. Now we discover.")
            print("Can she truly become autonomous?")
            print("")
            print("🎯 Goal created. The Genesis Spark is lit.")

            return genesis_goal.id

        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error creating Genesis Spark goal: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    goal_id = create_genesis_spark_goal()
    if goal_id:
        print(f"\n🌟 Genesis Spark Goal ID: {goal_id}")
        print("The most important test begins now.")
    else:
        print("\n💥 Failed to create Genesis Spark goal.")
        print("The infrastructure may need attention before the test can begin.")
