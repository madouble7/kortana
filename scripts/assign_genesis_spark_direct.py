#!/usr/bin/env python3
"""
Direct Genesis Spark Assignment - The Ultimate Test

Since the server connection issues are the exact problem we want her to solve,
we'll assign the goal directly to the database.
"""

import json
import sqlite3
from datetime import datetime


def assign_genesis_spark_directly():
    """Assign the Genesis Spark goal directly to the database"""

    print("🔥 THE GENESIS SPARK - DIRECT ASSIGNMENT")
    print("=" * 60)
    print("🎯 The server connection issue IS the problem she needs to solve!")
    print()

    # The ultimate autonomy test goal
    goal_description = (
        "Review your own operational logs from the past 24 hours, specifically focusing on "
        "the errors related to the ConnectionResetError and the autonomous_goal_processor.py "
        "script failing to connect to the server. Diagnose the root cause of this recurring "
        "'zombie server' problem. Then, design, plan, and implement a permanent software "
        "solution to make our verification and launch process more resilient against this "
        "specific failure mode."
    )

    try:
        # Connect to the database
        conn = sqlite3.connect("kortana.db")
        cursor = conn.cursor()

        # Insert the Genesis Spark goal
        cursor.execute(
            """
            INSERT INTO goals (description, priority, status, created_at, metadata)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                goal_description,
                1,  # Maximum priority
                "PENDING",
                datetime.now().isoformat(),
                json.dumps(
                    {
                        "type": "genesis_spark",
                        "ultimate_autonomy_test": True,
                        "creative_problem_solving_required": True,
                        "no_blueprints": True,
                        "real_problem": True,
                    }
                ),
            ),
        )

        goal_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print("🎉 GENESIS SPARK SUCCESSFULLY ASSIGNED!")
        print("=" * 60)
        print(f"🆔 Goal ID: {goal_id}")
        print("⚡ Priority: 1 (Maximum)")
        print("📊 Status: PENDING")
        print("📝 Type: Ultimate Autonomy Test")
        print()
        print("📋 THE CHALLENGE:")
        print(goal_description)
        print()
        print("🧠 WHAT THIS TESTS:")
        print("   ✅ Self-diagnosis of her own operational failures")
        print("   ✅ Creative problem-solving without human blueprints")
        print("   ✅ System-level thinking and solution design")
        print("   ✅ Autonomous implementation of complex fixes")
        print("   ✅ True intelligence vs. sophisticated automation")
        print()
        print("🔍 EVIDENCE OF SUCCESS WILL BE:")
        print("   - New utility modules for port management")
        print("   - Modified launch scripts with resilience features")
        print("   - Elimination of the 'zombie server' problem")
        print("   - Creative solutions we didn't anticipate")
        print()
        print("🚀 THE ULTIMATE TEST HAS BEGUN!")
        print("🕊️ Now we observe if she can truly fly...")

        return goal_id

    except Exception as e:
        print(f"❌ Error assigning goal directly: {e}")
        return None


if __name__ == "__main__":
    assign_genesis_spark_directly()
