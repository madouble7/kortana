#!/usr/bin/env python3
"""
PHASE 4: THE PROVING GROUND - OBSERVATION MONITOR
Monitor Kor'tana's autonomous processing of the Genesis Protocol goal
"""

import sqlite3
import time
from datetime import datetime
import json

class Phase4Observer:
    """Observer for Phase 4 autonomous processing"""

    def __init__(self, db_path="./kortana_memory_dev.db"):
        self.db_path = db_path
        self.genesis_goal_id = 1
        self.observation_log = []

    def get_db_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def check_goal_status(self):
        """Check the current status of the Genesis goal"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, description, status, priority, created_at, completed_at
                FROM goals WHERE id = ?
            """, (self.genesis_goal_id,))

            goal = cursor.fetchone()
            conn.close()

            if goal:
                return {
                    'id': goal[0],
                    'description': goal[1][:100] + "..." if len(goal[1]) > 100 else goal[1],
                    'status': goal[2],
                    'priority': goal[3],
                    'created_at': goal[4],
                    'completed_at': goal[5]
                }
            return None

        except Exception as e:
            print(f"Error checking goal status: {e}")
            return None
      def check_plan_steps(self):
        """Check plan steps for the Genesis goal"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, step_number, action_type, parameters, status, result
                FROM plan_steps
                WHERE goal_id = ?
                ORDER BY step_number
            """, (self.genesis_goal_id,))

            steps = cursor.fetchall()
            conn.close()

            return [{
                'id': step[0],
                'step_number': step[1],
                'action_type': step[2],
                'parameters': step[3],
                'status': step[4],
                'result': step[5]
            } for step in steps]

        except Exception as e:
            print(f"Error checking plan steps: {e}")
            return []

    def check_memory_entries(self):
        """Check core memory entries related to the Genesis goal"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, memory_type, content, relevance_score, created_at
                FROM core_memory
                WHERE content LIKE '%goal_router%' OR content LIKE '%GENESIS%'
                ORDER BY created_at DESC
                LIMIT 10
            """, )

            memories = cursor.fetchall()
            conn.close()

            return [{
                'id': memory[0],
                'memory_type': memory[1],
                'content': memory[2][:200] + "..." if len(memory[2]) > 200 else memory[2],
                'relevance_score': memory[3],
                'created_at': memory[4]
            } for memory in memories]

        except Exception as e:
            print(f"Error checking memory entries: {e}")
            return []

    def take_snapshot(self):
        """Take a snapshot of the current state"""
        timestamp = datetime.now().isoformat()

        snapshot = {
            'timestamp': timestamp,
            'goal': self.check_goal_status(),
            'plan_steps': self.check_plan_steps(),
            'memory_entries': self.check_memory_entries()
        }

        self.observation_log.append(snapshot)
        return snapshot

    def display_current_state(self):
        """Display the current state of the observation"""
        print("\n" + "="*80)
        print("🔬 PHASE 4 OBSERVATION - CURRENT STATE")
        print("="*80)
        print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Goal Status
        goal = self.check_goal_status()
        if goal:
            print(f"\n🎯 GENESIS GOAL STATUS:")
            print(f"   ID: {goal['id']}")
            print(f"   Status: {goal['status']}")
            print(f"   Priority: {goal['priority']}")
            print(f"   Created: {goal['created_at']}")
            if goal['completed_at']:
                print(f"   Completed: {goal['completed_at']}")

        # Plan Steps
        steps = self.check_plan_steps()
        print(f"\n📋 PLAN STEPS: {len(steps)} total")

        if steps:
            for step in steps:
                status_icon = "✅" if step['status'] == 'COMPLETED' else "⏳" if step['status'] == 'IN_PROGRESS' else "⭕"
                print(f"   {status_icon} Step {step['step_number']}: {step['action_type']}")
                if step['description']:
                    print(f"      {step['description'][:100]}...")
                if step['executed_at']:
                    print(f"      Executed: {step['executed_at']}")
                if step['result']:
                    print(f"      Result: {step['result'][:100]}...")
        else:
            print("   ⏳ No plan steps yet - waiting for autonomous planning to begin")

        # Memory Entries
        memories = self.check_memory_entries()
        print(f"\n🧠 RELATED MEMORY ENTRIES: {len(memories)}")

        for memory in memories[:3]:  # Show first 3
            print(f"   📝 {memory['memory_type']}: {memory['content'][:100]}...")
            print(f"      Score: {memory['relevance_score']}, Created: {memory['created_at']}")

        # Analysis
        self.analyze_autonomous_behavior(goal, steps, memories)

    def analyze_autonomous_behavior(self, goal, steps, memories):
        """Analyze Kor'tana's autonomous behavior patterns"""
        print(f"\n🤖 AUTONOMOUS BEHAVIOR ANALYSIS:")

        if not steps:
            print("   ⏳ STATUS: Waiting for autonomous planning to begin")
            print("   📊 PLANNING: No evidence of planning activity yet")
            print("   🔍 NEXT: Monitor for goal decomposition and plan generation")
            return

        # Planning Quality
        completed_steps = [s for s in steps if s['status'] == 'COMPLETED']
        in_progress_steps = [s for s in steps if s['status'] == 'IN_PROGRESS']

        print(f"   📊 PLANNING QUALITY:")
        print(f"      Total steps generated: {len(steps)}")
        print(f"      Completed: {len(completed_steps)}")
        print(f"      In progress: {len(in_progress_steps)}")

        # Action Type Diversity
        action_types = set(step['action_type'] for step in steps if step['action_type'])
        if action_types:
            print(f"      Action types used: {', '.join(action_types)}")

        # Execution Quality
        print(f"   ⚡ EXECUTION QUALITY:")
        if completed_steps:
            avg_execution_time = "Analyzing..."
            print(f"      Average step completion: {avg_execution_time}")

            results_with_content = [s for s in completed_steps if s['result']]
            print(f"      Steps with results: {len(results_with_content)}/{len(completed_steps)}")

        # Learning Evidence
        print(f"   🧠 LEARNING EVIDENCE:")
        if memories:
            recent_memories = [m for m in memories if 'goal_router' in m['content'].lower()]
            print(f"      Task-related memories: {len(recent_memories)}")
            print(f"      Recent memory activity: {len(memories)} entries")
        else:
            print("      No task-related memories yet")

        # Self-Reflection Indicators
        reflection_indicators = []
        for step in steps:
            if step['result'] and any(word in step['result'].lower() for word in ['analyze', 'consider', 'evaluate', 'reflect']):
                reflection_indicators.append(step)

        print(f"   🤔 SELF-REFLECTION:")
        if reflection_indicators:
            print(f"      Steps showing reflection: {len(reflection_indicators)}")
        else:
            print("      No explicit reflection detected yet")

    def continuous_monitor(self, interval=30, max_iterations=20):
        """Continuously monitor the autonomous process"""
        print("🚀 Starting continuous Phase 4 observation...")
        print(f"   Monitoring interval: {interval} seconds")
        print(f"   Max iterations: {max_iterations}")
        print("   Press Ctrl+C to stop monitoring\n")

        iteration = 0
        try:
            while iteration < max_iterations:
                self.display_current_state()

                # Check if goal is completed
                goal = self.check_goal_status()
                if goal and goal['status'] in ['COMPLETED', 'FAILED']:
                    print(f"\n🏁 GOAL {goal['status']} - OBSERVATION COMPLETE")
                    break

                print(f"\n⏳ Waiting {interval} seconds before next observation...")
                time.sleep(interval)
                iteration += 1

        except KeyboardInterrupt:
            print("\n🛑 Observation stopped by user")

        # Generate final report
        self.generate_observation_report()

    def generate_observation_report(self):
        """Generate a comprehensive observation report"""
        print("\n" + "="*80)
        print("📊 PHASE 4 FINAL OBSERVATION REPORT")
        print("="*80)

        final_snapshot = self.take_snapshot()

        # Save observation log
        with open("phase4_observation_log.json", "w") as f:
            json.dump(self.observation_log, f, indent=2)

        print(f"📁 Observation log saved to: phase4_observation_log.json")
        print(f"📈 Total snapshots taken: {len(self.observation_log)}")

        # Summary analysis
        goal = final_snapshot['goal']
        steps = final_snapshot['plan_steps']
        memories = final_snapshot['memory_entries']

        print(f"\n🎯 FINAL GOAL STATUS: {goal['status'] if goal else 'UNKNOWN'}")
        print(f"📋 TOTAL PLAN STEPS: {len(steps)}")
        print(f"🧠 MEMORY ENTRIES: {len(memories)}")

        # Assessment
        print(f"\n🏆 KOR'TANA AUTONOMOUS ENGINEERING ASSESSMENT:")
        if steps:
            print("   ✅ PLANNING: Successfully generated execution plan")

            completed = len([s for s in steps if s['status'] == 'COMPLETED'])
            if completed > 0:
                print(f"   ✅ EXECUTION: Completed {completed}/{len(steps)} planned steps")
            else:
                print("   ⏳ EXECUTION: No steps completed yet")

            if memories:
                print("   ✅ LEARNING: Generated task-related memories")
            else:
                print("   ⏳ LEARNING: No task-related memories detected")
        else:
            print("   ⏳ PLANNING: No plan generated yet - autonomous system may need activation")

        print(f"\n🔬 Phase 4 observation complete. Next: Manual verification and testing.")

def main():
    """Main observation function"""
    print("🔬 PHASE 4: THE PROVING GROUND - OBSERVATION STARTING")
    print("="*70)

    observer = Phase4Observer()

    # Take initial snapshot
    print("📸 Taking initial snapshot...")
    observer.display_current_state()

    # Ask user for monitoring preference
    print(f"\n🤔 Monitoring Options:")
    print("   1. Single snapshot (current state only)")
    print("   2. Continuous monitoring (30-second intervals)")
    print("   3. Custom interval monitoring")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == "2":
        observer.continuous_monitor()
    elif choice == "3":
        try:
            interval = int(input("Enter monitoring interval in seconds: "))
            iterations = int(input("Enter max iterations (0 for unlimited): ") or "20")
            observer.continuous_monitor(interval, iterations if iterations > 0 else 999)
        except ValueError:
            print("Invalid input, using defaults...")
            observer.continuous_monitor()
    else:
        # Single snapshot
        observer.generate_observation_report()

if __name__ == "__main__":
    main()
