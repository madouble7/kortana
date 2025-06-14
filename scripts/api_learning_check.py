#!/usr/bin/env python3
"""
API-based learning loop verification
"""

from datetime import datetime

import requests

# FastAPI server configuration
BASE_URL = "http://localhost:8000"
output_file = r"c:\project-kortana\api_learning_check.txt"


def check_server():
    """Check if server is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def get_memories():
    """Get memories via API."""
    try:
        response = requests.get(f"{BASE_URL}/memories/", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def get_goals():
    """Get goals via API."""
    try:
        response = requests.get(f"{BASE_URL}/goals/", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def analyze_learning_state():
    """Analyze learning state via API."""
    results = []
    results.append("🌐 API-BASED LEARNING LOOP VERIFICATION")
    results.append("=" * 50)
    results.append(f"Timestamp: {datetime.now()}")
    results.append("")

    # Check server
    if not check_server():
        results.append("❌ FastAPI server is not responding")
        results.append("The autonomous system may be running but API is not accessible")
        return results

    results.append("✅ FastAPI server is responding")

    # Get memories
    memories = get_memories()
    if "error" in memories:
        results.append(f"❌ Error fetching memories: {memories['error']}")
    else:
        results.append(f"💭 Total memories fetched: {len(memories)}")

        # Analyze core beliefs
        core_beliefs = [m for m in memories if m.get("memory_type") == "CORE_BELIEF"]
        results.append(f"🧠 Core beliefs: {len(core_beliefs)}")

        if core_beliefs:
            results.append("\n✅ CORE BELIEFS FOUND:")
            for i, belief in enumerate(core_beliefs[-3:], 1):  # Last 3
                results.append(f"\n  #{i}: {belief.get('title', 'Untitled')}")
                content = belief.get("content", "")
                results.append(f"      Content: {content[:80]}...")
                results.append(f"      Created: {belief.get('created_at', 'Unknown')}")

                # Check if self-generated
                metadata = belief.get("memory_metadata", {})
                if isinstance(metadata, str):
                    is_self_generated = "performance_analysis_task" in metadata
                else:
                    is_self_generated = (
                        metadata.get("source") == "performance_analysis_task"
                    )
                results.append(f"      Self-generated: {is_self_generated}")

        # Check for learning-related memories
        learning_memories = [
            m
            for m in memories
            if "performance_analysis_task" in str(m.get("memory_metadata", ""))
        ]
        results.append(f"\n🔬 Learning loop memories: {len(learning_memories)}")

        # Check for goal outcome memories
        goal_memories = [
            m
            for m in memories
            if "goal_processing_cycle" in str(m.get("memory_metadata", ""))
        ]
        results.append(f"📊 Goal outcome memories: {len(goal_memories)}")

    # Get goals
    goals = get_goals()
    if "error" in goals:
        results.append(f"❌ Error fetching goals: {goals['error']}")
    else:
        results.append(f"🎯 Total goals: {len(goals)}")

        if goals:
            results.append("\n📋 Recent goals:")
            for goal in goals[-5:]:  # Last 5
                desc = goal.get("description", "No description")
                status = goal.get("status", "Unknown")
                results.append(f"   • {desc[:50]}... [{status}]")

    # Analysis
    if check_server():
        learning_count = len(
            [
                m
                for m in memories
                if "performance_analysis_task" in str(m.get("memory_metadata", ""))
            ]
        )
        belief_count = len(
            [m for m in memories if m.get("memory_type") == "CORE_BELIEF"]
        )
        goal_count = len(
            [
                m
                for m in memories
                if "goal_processing_cycle" in str(m.get("memory_metadata", ""))
            ]
        )

        results.append("\n🔬 LEARNING LOOP STATUS:")
        if learning_count > 0:
            results.append("   ✅ LEARNING LOOP IS ACTIVE!")
            results.append("   Self-generated memories detected via API.")
        elif belief_count > 0 and goal_count > 0:
            results.append("   🟡 LEARNING LOOP IS READY")
            results.append("   Experiences exist, may process on next cycle.")
        elif goal_count > 0:
            results.append("   🟠 EXPERIENCES AVAILABLE")
            results.append("   Goal outcomes exist but no beliefs yet.")
        else:
            results.append("   🔴 LIMITED LEARNING DATA")
            results.append("   May need more autonomous cycles to detect activity.")

    return results


def main():
    """Main function."""
    try:
        results = analyze_learning_state()

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            for line in results:
                f.write(line + "\n")

        print(f"API learning check complete! Results in: {output_file}")

        # Print key findings
        if check_server():
            print("✅ FastAPI server is accessible")
        else:
            print("❌ FastAPI server not accessible")

    except Exception as e:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Error during API check: {e}\n")
            f.write(f"Timestamp: {datetime.now()}\n")
        print(f"Error occurred, check: {output_file}")


if __name__ == "__main__":
    main()
