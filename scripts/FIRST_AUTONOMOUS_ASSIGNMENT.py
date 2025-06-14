#!/usr/bin/env python3
"""
🎯 THE PROVING GROUND: Kor'tana's First Autonomous Engineering Assignment
==================================================================

OBJECTIVE: Give Kor'tana her first real software engineering task and observe
her autonomous development process from start to finish.

ASSIGNMENT:
Refactor the list_all_goals function in src/kortana/api/routers/goal_router.py.
Create a new service layer function in a new file, src/kortana/api/services/goal_service.py,
to handle the database query. The router must then be updated to call this new service function.
After the refactor, run the full project test suite to ensure no regressions were introduced.

EXPECTED AUTONOMOUS BEHAVIORS TO OBSERVE:
1. Planning: She will analyze the task and create a multi-step plan
2. Code Creation: New file src/kortana/api/services/goal_service.py will be created
3. Code Modification: Existing goal_router.py will be updated
4. Validation: She will run tests to verify her work
5. Learning: She will synthesize lessons about software architecture

This is the moment we've been building toward - autonomous engineering in action.
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path


async def assign_first_autonomous_goal():
    """Assign Kor'tana her first autonomous software engineering task."""

    goal_description = """Refactor the list_all_goals function in src/kortana/api/routers/goal_router.py. Create a new service layer function in a new file, src/kortana/api/services/goal_service.py, to handle the database query. The router must then be updated to call this new service function. After the refactor, run the full project test suite to ensure no regressions were introduced."""

    # Connect directly to her database
    db_path = Path("c:/project-kortana/kortana.db")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Insert the goal directly into her goals table
        cursor.execute(
            """
            INSERT INTO goals (description, priority, status, created_at, metadata)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                goal_description,
                1,  # Highest priority
                "pending",
                datetime.now().isoformat(),
                json.dumps(
                    {
                        "type": "autonomous_engineering_assignment",
                        "phase": "proving_ground",
                        "objective": "first_autonomous_development_task",
                        "expected_outputs": [
                            "src/kortana/api/services/goal_service.py",
                            "modified src/kortana/api/routers/goal_router.py",
                            "test_execution_results",
                        ],
                    }
                ),
            ),
        )

        goal_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print("🎯 FIRST AUTONOMOUS ASSIGNMENT ASSIGNED!")
        print(f"📋 Goal ID: {goal_id}")
        print(f"🚀 Assignment: {goal_description}")
        print("")
        print("🔍 AUTONOMOUS DEVELOPMENT MONITORING:")
        print("   Watch for file creation: src/kortana/api/services/goal_service.py")
        print("   Watch for file changes: src/kortana/api/routers/goal_router.py")
        print("   Watch for test execution in logs")
        print("")
        print("⚡ The Proving Ground is now ACTIVE!")
        print("   Kor'tana should begin autonomous work within the next few cycles.")

        return goal_id

    except Exception as e:
        print(f"❌ Error assigning goal: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(assign_first_autonomous_goal())
