#!/usr/bin/env python3
"""
PHASE 4: THE PROVING GROUND - OBSERVATION PROTOCOL
Real-time monitoring of Kor'tana's autonomous software engineering performance
"""

import json
import os
import sqlite3
from datetime import datetime


def monitor_genesis_goal():
    """Monitor the status and progress of the Genesis Protocol goal"""
    print("🔬 PHASE 4: THE PROVING GROUND - OBSERVATION PROTOCOL")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if not os.path.exists("kortana.db"):
        print("❌ Database not found!")
        return

    try:
        conn = sqlite3.connect("kortana.db")
        cursor = conn.cursor()

        # Find the Genesis goal
        print("🎯 GENESIS PROTOCOL GOAL STATUS:")
        print("-" * 50)
        cursor.execute("""
            SELECT id, title, status, priority, created_at, updated_at, description
            FROM goals
            WHERE title LIKE '%GENESIS%'
            ORDER BY id DESC
            LIMIT 1
        """)
        genesis_goal = cursor.fetchone()

        if not genesis_goal:
            print("❌ No Genesis goal found!")
            return

        goal_id, title, status, priority, created_at, updated_at, description = (
            genesis_goal
        )
        print(f"📋 Goal ID: {goal_id}")
        print(f"🎯 Title: {title}")
        print(f"📊 Status: {status}")
        print(f"⚡ Priority: {priority}")
        print(f"📅 Created: {created_at}")
        print(f"🔄 Updated: {updated_at}")
        print()

        # Check plan steps for this goal
        print("📋 PLAN EXECUTION STATUS:")
        print("-" * 50)
        cursor.execute(
            """
            SELECT step_number, action_type, description, status, created_at, updated_at
            FROM plan_steps
            WHERE goal_id = ?
            ORDER BY step_number
        """,
            (goal_id,),
        )

        plan_steps = cursor.fetchall()
        if plan_steps:
            for step in plan_steps:
                step_num, action_type, desc, step_status, step_created, step_updated = (
                    step
                )
                status_emoji = {
                    "PENDING": "⏳",
                    "ACTIVE": "🔄",
                    "COMPLETED": "✅",
                    "FAILED": "❌",
                }.get(step_status, "❓")
                print(f"  {status_emoji} Step {step_num}: {action_type}")
                print(f"     Description: {desc[:80]}{'...' if len(desc) > 80 else ''}")
                print(f"     Status: {step_status}")
                if step_updated != step_created:
                    print(f"     Updated: {step_updated}")
                print()
        else:
            print(
                "  ⏳ No plan steps found yet - goal may be in initial planning phase"
            )
            print()

        # Check recent autonomous activity and reasoning
        print("🧠 AUTONOMOUS REASONING ACTIVITY:")
        print("-" * 50)
        cursor.execute("""
            SELECT content, memory_type, created_at
            FROM core_memory
            WHERE created_at > datetime('now', '-2 hours')
            AND (content LIKE '%goal%' OR content LIKE '%GENESIS%' OR content LIKE '%refactor%')
            ORDER BY created_at DESC
            LIMIT 5
        """)

        recent_memories = cursor.fetchall()
        if recent_memories:
            for memory in recent_memories:
                content, mem_type, created = memory
                print(f"  💭 {mem_type} | {created}")
                print(f"     {content[:120]}{'...' if len(content) > 120 else ''}")
                print()
        else:
            print("  ⏳ No recent autonomous reasoning found")
            print()

        # Check execution results
        print("⚙️ EXECUTION RESULTS:")
        print("-" * 50)
        cursor.execute(
            """
            SELECT step_number, execution_result, created_at
            FROM plan_steps
            WHERE goal_id = ? AND execution_result IS NOT NULL
            ORDER BY step_number
        """,
            (goal_id,),
        )

        execution_results = cursor.fetchall()
        if execution_results:
            for result in execution_results:
                step_num, exec_result, created = result
                print(f"  ⚙️ Step {step_num} Result | {created}")
                try:
                    result_data = json.loads(exec_result) if exec_result else {}
                    if "success" in result_data:
                        success_emoji = "✅" if result_data["success"] else "❌"
                        print(f"     {success_emoji} Success: {result_data['success']}")
                    if "operation_type" in result_data:
                        print(f"     🔧 Operation: {result_data['operation_type']}")
                    if "error" in result_data and result_data["error"]:
                        print(
                            f"     ⚠️ Error: {result_data['error'][:100]}{'...' if len(str(result_data['error'])) > 100 else ''}"
                        )
                except Exception:
                    print(
                        f"     📄 Raw result: {exec_result[:100]}{'...' if len(str(exec_result)) > 100 else ''}"
                    )
                print()
        else:
            print("  ⏳ No execution results yet")
            print()

        # Overall assessment
        total_steps = len(plan_steps)
        completed_steps = len([s for s in plan_steps if s[3] == "COMPLETED"])
        active_steps = len([s for s in plan_steps if s[3] == "ACTIVE"])

        print("📊 PROGRESS SUMMARY:")
        print("-" * 50)
        print(f"Goal Status: {status}")
        print(
            f"Plan Steps: {completed_steps}/{total_steps} completed, {active_steps} active"
        )
        if total_steps > 0:
            progress = (completed_steps / total_steps) * 100
            print(f"Progress: {progress:.1f}%")
        print(
            f"Recent Activity: {len(recent_memories)} reasoning entries in last 2 hours"
        )
        print()

        if status == "COMPLETED":
            print(
                "🎉 GENESIS GOAL COMPLETED! Ready for Phase 4 Step 2: Active Verification"
            )
        elif status == "ACTIVE":
            print("🔄 GENESIS GOAL IN PROGRESS - Continue monitoring...")
        elif status == "PENDING":
            print("⏳ GENESIS GOAL PENDING - Awaiting autonomous processing...")

        conn.close()

    except Exception as e:
        print(f"❌ Error monitoring goal: {e}")


def monitor_autonomous_logs():
    """Monitor recent autonomous system logs for thought processes"""
    print("\n📋 AUTONOMOUS SYSTEM LOGS:")
    print("-" * 50)

    # Look for recent log files
    log_patterns = [
        "logs/autonomous_tasks.log",
        "logs/kortana.log",
        "logs/planning_engine.log",
        "logs/execution_engine.log",
    ]

    found_logs = False
    for log_file in log_patterns:
        if os.path.exists(log_file):
            found_logs = True
            print(f"📋 {log_file}:")
            try:
                with open(log_file) as f:
                    lines = f.readlines()
                    # Get last 10 lines
                    recent_lines = lines[-10:] if len(lines) > 10 else lines
                    for line in recent_lines:
                        if any(
                            keyword in line.lower()
                            for keyword in ["genesis", "goal", "refactor", "error"]
                        ):
                            print(f"  {line.strip()}")
                print()
            except Exception as e:
                print(f"  ⚠️ Error reading log: {e}")

    if not found_logs:
        print("  ⚠️ No autonomous log files found in standard locations")


if __name__ == "__main__":
    monitor_genesis_goal()
    monitor_autonomous_logs()
    print("\n🔬 Observation complete. Continue monitoring for updates...")
