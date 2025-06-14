#!/usr/bin/env python3
"""
PHASE 4: THE PROVING GROUND - OBSERVATION MONITOR (Fixed Schema)
Monitor Kor'tana's autonomous processing of the Genesis Protocol goal
"""

import sqlite3
from datetime import datetime


def check_current_state():
    """Check the current state of the Genesis goal and system"""
    print("🔬 PHASE 4: THE PROVING GROUND - CURRENT STATE CHECK")
    print("=" * 70)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        conn = sqlite3.connect("./kortana_memory_dev.db")
        cursor = conn.cursor()

        # Check Genesis goal
        cursor.execute(
            "SELECT id, description, status, priority, created_at FROM goals WHERE id = 1"
        )
        goal = cursor.fetchone()

        if goal:
            print("\n🎯 GENESIS GOAL STATUS:")
            print(f"   ID: {goal[0]}")
            print(f"   Status: {goal[2]}")
            print(f"   Priority: {goal[3]}")
            print(f"   Created: {goal[4]}")
            print(f"   Description: {goal[1][:100]}...")
        else:
            print("❌ Genesis goal not found!")
            return

        # Check plan steps
        cursor.execute("SELECT COUNT(*) FROM plan_steps WHERE goal_id = 1")
        step_count = cursor.fetchone()[0]

        print(f"\n📋 PLAN STEPS: {step_count} total")

        if step_count > 0:
            cursor.execute("""
                SELECT id, step_number, action_type, status, parameters, result
                FROM plan_steps
                WHERE goal_id = 1
                ORDER BY step_number
            """)
            steps = cursor.fetchall()

            for step in steps:
                status_icon = (
                    "✅"
                    if step[3] == "COMPLETED"
                    else "⏳"
                    if step[3] == "IN_PROGRESS"
                    else "⭕"
                )
                print(f"   {status_icon} Step {step[1]}: {step[2]} ({step[3]})")
                if step[4]:  # parameters
                    print(f"      Parameters: {step[4][:100]}...")
                if step[5]:  # result
                    print(f"      Result: {step[5][:100]}...")
        else:
            print("   ⏳ No plan steps yet - waiting for autonomous planning to begin")

        # Check memory entries
        cursor.execute(
            "SELECT COUNT(*) FROM core_memory WHERE content LIKE '%goal_router%' OR content LIKE '%GENESIS%'"
        )
        memory_count = cursor.fetchone()[0]

        print(f"\n🧠 RELATED MEMORY ENTRIES: {memory_count}")

        if memory_count > 0:
            cursor.execute("""
                SELECT memory_type, content, created_at
                FROM core_memory
                WHERE content LIKE '%goal_router%' OR content LIKE '%GENESIS%'
                ORDER BY created_at DESC
                LIMIT 3
            """)
            memories = cursor.fetchall()

            for memory in memories:
                print(f"   📝 {memory[0]}: {memory[1][:100]}...")
                print(f"      Created: {memory[2]}")

        conn.close()

        # Analysis
        print("\n🤖 AUTONOMOUS BEHAVIOR ANALYSIS:")

        if step_count == 0:
            print("   ⏳ STATUS: Waiting for autonomous planning to begin")
            print("   📊 PLANNING: No evidence of planning activity yet")
            print(
                "   🔍 OBSERVATION: Ready to monitor goal decomposition and plan generation"
            )
            print(
                "   💡 NEXT STEPS: Kor'tana's autonomous engine should pick up the PENDING goal"
            )
        else:
            completed_steps = len([s for s in steps if s[3] == "COMPLETED"])
            in_progress_steps = len([s for s in steps if s[3] == "IN_PROGRESS"])

            print("   📊 PLANNING QUALITY:")
            print(f"      Total steps generated: {step_count}")
            print(f"      Completed: {completed_steps}")
            print(f"      In progress: {in_progress_steps}")

            # Action type diversity
            action_types = set(step[2] for step in steps)
            print(f"      Action types used: {', '.join(action_types)}")

            print("   ⚡ EXECUTION PROGRESS:")
            if completed_steps > 0:
                print(
                    f"      Completion rate: {completed_steps}/{step_count} ({completed_steps / step_count * 100:.1f}%)"
                )

                results_with_content = len([s for s in steps if s[5]])
                print(
                    f"      Steps with results: {results_with_content}/{completed_steps}"
                )
            else:
                print("      No steps completed yet")

            print("   🧠 LEARNING EVIDENCE:")
            if memory_count > 0:
                print(f"      Task-related memories: {memory_count}")
                print("      Evidence of autonomous learning and memory formation")
            else:
                print("      No task-related memories yet")

        # Goal status assessment
        if goal[2] == "PENDING":
            print("\n🚀 READY FOR AUTONOMOUS PROCESSING:")
            print("   ✅ Genesis goal created and waiting")
            print("   🔍 Observation protocol active")
            print("   ⏳ Awaiting Kor'tana's autonomous execution engine activation")
        elif goal[2] == "IN_PROGRESS":
            print("\n⚡ AUTONOMOUS PROCESSING ACTIVE:")
            print("   🔥 Kor'tana is actively working on the Genesis goal!")
            print("   📊 Monitor plan generation and execution quality")
        elif goal[2] == "COMPLETED":
            print("\n🏁 AUTONOMOUS PROCESSING COMPLETE:")
            print("   ✅ Genesis goal completed by autonomous system")
            print("   📋 Ready for verification and quality assessment")

        return {
            "goal_status": goal[2],
            "step_count": step_count,
            "memory_count": memory_count,
            "ready_for_monitoring": True,
        }

    except Exception as e:
        print(f"❌ Error checking system state: {e}")
        return None


def document_phase4_status():
    """Document the current Phase 4 status"""
    state = check_current_state()

    if not state:
        return

    print("\n📋 PHASE 4 STATUS SUMMARY:")
    print("=" * 50)

    if state["goal_status"] == "PENDING" and state["step_count"] == 0:
        print("🔄 PHASE 4 STEP 1: PASSIVE OBSERVATION - READY")
        print("   ✅ Genesis Protocol goal successfully created")
        print("   ✅ Database tables configured and accessible")
        print("   ✅ Observation monitoring script ready")
        print("   ⏳ Waiting for Kor'tana's autonomous processing to begin")
        print("")
        print("🤖 NEXT ACTIONS:")
        print("   1. Ensure Kor'tana's autonomous engine is running")
        print("   2. Monitor for goal pickup and plan generation")
        print("   3. Observe planning quality and execution approach")
        print("   4. Document learning and self-reflection evidence")

    elif state["step_count"] > 0:
        print("🔥 PHASE 4 STEP 1: ACTIVE AUTONOMOUS PROCESSING DETECTED!")
        print("   ✅ Kor'tana has begun autonomous processing")
        print(f"   📊 Generated {state['step_count']} plan steps")
        print(f"   🧠 Created {state['memory_count']} related memories")
        print("")
        print("🔬 OBSERVATION FOCUS:")
        print("   1. Planning quality and decomposition approach")
        print("   2. Execution methodology and tool usage")
        print("   3. Self-reflection and learning patterns")
        print("   4. Code quality and engineering best practices")

    else:
        print("⏳ PHASE 4 STEP 1: AWAITING AUTONOMOUS ACTIVATION")
        print("   ✅ Infrastructure ready")
        print("   ⏳ Goal created but not yet processed")
        print("   🔍 Monitor for autonomous system engagement")


if __name__ == "__main__":
    document_phase4_status()

    print("\n💡 MONITORING COMMANDS:")
    print("   • Run this script periodically to check progress")
    print("   • Use 'python phase4_observer.py' for detailed continuous monitoring")
    print("   • Check the database directly with SQLite tools if needed")
    print("\n🎯 PHASE 4 GOAL: Observe Kor'tana's autonomous software engineering")
    print("   Focus: Planning quality, execution competence, learning evidence")
