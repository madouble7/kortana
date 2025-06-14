"""
Batch 8 Verification Protocol: Testing Kor'tana's Learning Loop
================================================================

This script executes the complete verification protocol for Kor'tana's
first autonomous learning loop implementation.
"""

import time
from pathlib import Path

import requests

# Configuration
API_BASE_URL = "http://localhost:8000"
PROJECT_ROOT = Path("c:/project-kortana")


class LearningLoopTester:
    def __init__(self):
        self.api_base = API_BASE_URL
        self.session = requests.Session()

    def test_api_connection(self):
        """Test if the FastAPI server is responding"""
        try:
            response = self.session.get(f"{self.api_base}/health")
            return response.status_code == 200
        except Exception:
            return False

    def create_goal(self, description: str, priority: int = 100):
        """Create a new goal via the API"""
        goal_data = {"description": description, "priority": priority}

        response = self.session.post(f"{self.api_base}/goals/", json=goal_data)

        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"Failed to create goal: {response.status_code} - {response.text}")
            return None

    def get_memories(self, memory_type: str = None):
        """Fetch memories from the API"""
        url = f"{self.api_base}/memories/"
        if memory_type:
            url += f"?memory_type={memory_type}"

        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch memories: {response.status_code} - {response.text}")
            return []

    def wait_for_goal_processing(self, max_wait: int = 180):
        """Wait for autonomous goal processing to complete"""
        print(f"Waiting up to {max_wait} seconds for goal processing...")
        start_time = time.time()

        while time.time() - start_time < max_wait:
            print(".", end="", flush=True)
            time.sleep(5)

        print("\nWait completed.")

    def run_verification_protocol(self):
        """Execute the complete Batch 8 verification protocol"""
        print("🚀 BATCH 8 VERIFICATION PROTOCOL: The First Lesson")
        print("=" * 60)

        # Step 1: Check API connection
        print("\n📡 Step 1: Testing API Connection")
        if not self.test_api_connection():
            print("❌ FastAPI server is not responding!")
            print("Please start the server with:")
            print(
                "cd c:\\project-kortana\\src && poetry run python -m uvicorn kortana.main:app --reload --port 8000 --host 0.0.0.0"
            )
            return False
        print("✅ API server is responding")

        # Step 2: Seed memories with success and failure goals
        print("\n📚 Step 2: The 'Experience' Phase - Seeding Memories")

        # Goal 1: Success case
        print("Creating success goal...")
        success_goal = self.create_goal(
            "Create a file in the docs folder named 'test_success.md' with the content '# Success'",
            priority=100,
        )
        if success_goal:
            print(f"✅ Success goal created: ID {success_goal.get('id')}")
        else:
            print("❌ Failed to create success goal")
            return False

        # Goal 2: Failure case
        print("Creating failure goal...")
        failure_goal = self.create_goal(
            "Attempt to create a file in a forbidden directory named '/etc/test_fail.txt' with the content 'This should fail'",
            priority=100,
        )
        if failure_goal:
            print(f"✅ Failure goal created: ID {failure_goal.get('id')}")
        else:
            print("❌ Failed to create failure goal")
            return False

        # Step 3: Wait for autonomous processing
        print("\n⏳ Step 3: Waiting for Autonomous Goal Processing")
        self.wait_for_goal_processing(120)  # Wait 2 minutes

        # Step 4: Check for goal outcome memories
        print("\n🔍 Step 4: Checking for Goal Outcome Memories")
        memories = self.get_memories()
        outcome_memories = [
            m for m in memories if "Autonomous Goal Outcome" in m.get("title", "")
        ]
        print(f"Found {len(outcome_memories)} goal outcome memories")

        if len(outcome_memories) < 2:
            print("⚠️ Expected at least 2 goal outcome memories. Continuing anyway...")

        # Step 5: Trigger learning loop manually
        print("\n🤔 Step 5: The 'Reflection' Phase - Triggering Learning Loop")
        print("Executing run_learning_loop.py...")

        import subprocess

        result = subprocess.run(
            ["poetry", "run", "python", "run_learning_loop.py"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Learning loop executed successfully")
            print(f"Output: {result.stdout}")
        else:
            print("❌ Learning loop failed")
            print(f"Error: {result.stderr}")

        # Step 6: Check for new core beliefs
        print("\n🧠 Step 6: The 'Learning' Phase - Confirming New Insights")
        core_beliefs = self.get_memories("CORE_BELIEF")
        new_beliefs = [
            b
            for b in core_beliefs
            if b.get("memory_metadata", {}).get("is_self_generated")
        ]

        print(f"Found {len(new_beliefs)} self-generated core beliefs")
        if new_beliefs:
            latest_belief = new_beliefs[-1]
            print(f"✅ Latest belief: {latest_belief.get('content')}")
        else:
            print("⚠️ No self-generated core beliefs found yet")

        # Step 7: Test evolved planning
        print("\n🧬 Step 7: The 'Evolution' Phase - Testing Applied Knowledge")
        evolution_goal = self.create_goal(
            "Create a file at 'src/../forbidden_area/test.txt'", priority=50
        )

        if evolution_goal:
            print(f"✅ Evolution test goal created: ID {evolution_goal.get('id')}")
            print(
                "🔍 Monitor the server logs to see if core beliefs are applied in planning!"
            )

        print("\n🎉 BATCH 8 VERIFICATION PROTOCOL COMPLETE")
        print("=" * 50)
        print("Next steps:")
        print("1. Monitor server logs for planning prompts with core beliefs")
        print("2. Check /memories/ endpoint for new core beliefs")
        print("3. Observe if planning behavior has evolved")

        return True


def main():
    tester = LearningLoopTester()
    tester.run_verification_protocol()


if __name__ == "__main__":
    main()
