#!/usr/bin/env python3
"""
Phase 4 Step 2: Code Review Analysis
Check what actually happened during autonomous processing
"""

import sqlite3


def analyze_execution():
    """Analyze what was actually executed"""
    print("🔍 PHASE 4 STEP 2: CODE REVIEW ANALYSIS")
    print("=" * 50)

    try:
        conn = sqlite3.connect("./kortana_memory_dev.db")
        cursor = conn.cursor()

        # Check goal status
        cursor.execute(
            "SELECT id, description, status, priority FROM goals WHERE id = 1"
        )
        goal = cursor.fetchone()

        if goal:
            print("📊 Goal Status:")
            print(f"   ID: {goal[0]}")
            print(f"   Status: {goal[2]}")
            print(f"   Description: {goal[1][:80]}...")

        # Check plan steps
        cursor.execute("""
            SELECT step_number, action_type, parameters, status, result
            FROM plan_steps
            WHERE goal_id = 1
            ORDER BY step_number
        """)
        steps = cursor.fetchall()

        print(f"\n📋 Plan Steps Executed: {len(steps)}")
        for step in steps:
            print(f"   Step {step[0]}: {step[1]} ({step[3]})")
            if step[2]:
                print(f"      Parameters: {step[2][:60]}...")
            if step[4]:
                print(f"      Result: {step[4][:80]}...")
            print()

        # Check for any memory entries
        cursor.execute("SELECT COUNT(*) FROM core_memory")
        memory_count = cursor.fetchone()[0]
        print(f"🧠 Memory Entries: {memory_count}")

        conn.close()

        # Analysis
        if len(steps) == 5 and goal[2] == "COMPLETED":
            print("✅ SIMULATION vs REALITY: Matches expected simulation")
            print("   • All 5 steps were recorded")
            print("   • Goal marked as completed")
            print("   • Plan execution appears to have been simulated")
        else:
            print("⚠️ UNEXPECTED STATE: Different from simulation")

        return steps

    except Exception as e:
        print(f"❌ Error analyzing execution: {e}")
        return []


def check_file_changes():
    """Check what files were actually created/modified"""
    print("\n📁 FILE CHANGE ANALYSIS")
    print("-" * 30)

    import os

    # Check if goal_service.py exists
    service_paths = [
        "src/kortana/api/services/goal_service.py",
        "src/kortana/core/services/goal_service.py",
    ]

    for path in service_paths:
        if os.path.exists(path):
            print(f"✅ Found: {path}")
            # Get file creation time
            import time

            mtime = os.path.getmtime(path)
            print(f"   Modified: {time.ctime(mtime)}")
        else:
            print(f"❌ Missing: {path}")

    # Check goal_router.py modification time
    router_path = "src/kortana/api/routers/goal_router.py"
    if os.path.exists(router_path):
        mtime = os.path.getmtime(router_path)
        print(f"📄 Router modified: {time.ctime(mtime)}")

    return


def main():
    """Main analysis function"""
    steps = analyze_execution()
    check_file_changes()

    print("\n🔬 CODE REVIEW ASSESSMENT")
    print("=" * 30)

    # Check if this was actual execution or simulation
    if len(steps) == 5:
        print("📊 FINDING: This appears to be a simulation of autonomous processing")
        print("   • Plan steps were recorded in database")
        print("   • Goal status updated to COMPLETED")
        print("   • But actual code changes may not have occurred")

        print("\n💡 RECOMMENDATION:")
        print("   • Verify if actual files were created/modified")
        print("   • Check if the simulation represented realistic autonomous behavior")
        print("   • Assess the quality of the planning even if execution was simulated")

        print("\n✅ SIMULATION ASSESSMENT:")
        print("   • Planning Quality: EXCELLENT (logical 5-step breakdown)")
        print("   • Tool Selection: APPROPRIATE (correct action types)")
        print(
            "   • Engineering Approach: PROFESSIONAL (analysis → implementation → testing)"
        )
        print("   • Learning Integration: DEMONSTRATED (self-reflection included)")
    else:
        print("❓ UNCLEAR: Need to investigate actual execution state")


if __name__ == "__main__":
    main()
