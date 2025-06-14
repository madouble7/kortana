import sqlite3
from datetime import datetime

# Create goals table and assign first autonomous task
conn = sqlite3.connect("kortana.db")
cursor = conn.cursor()

# Create goals table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        priority INTEGER DEFAULT 1,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        metadata TEXT
    )
""")

# Assign the first autonomous engineering goal
goal_description = """Refactor the list_all_goals function in src/kortana/api/routers/goal_router.py. Create a new service layer function in a new file, src/kortana/api/services/goal_service.py, to handle the database query. The router must then be updated to call this new service function. After the refactor, run the full project test suite to ensure no regressions were introduced."""

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
        '{"type": "autonomous_engineering_assignment", "phase": "proving_ground"}',
    ),
)

goal_id = cursor.lastrowid
conn.commit()
conn.close()

print("🎯 FIRST AUTONOMOUS ASSIGNMENT ASSIGNED!")
print(f"📋 Goal ID: {goal_id}")
print("🚀 Task: Refactor list_all_goals function and create service layer")
print("")
print("🔍 WHAT TO OBSERVE:")
print("   ✅ File creation: src/kortana/api/services/goal_service.py")
print("   ✅ File modification: src/kortana/api/routers/goal_router.py")
print("   ✅ Test execution in autonomous logs")
print("   ✅ Planning and validation steps")
print("")
print("⚡ THE PROVING GROUND IS NOW ACTIVE!")
print("   Kor'tana should begin autonomous work within the next few cycles.")
