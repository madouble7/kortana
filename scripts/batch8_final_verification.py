#!/usr/bin/env python3
"""
Batch 8 Final Verification Protocol
===================================

This script should be run during a maintenance window when the relay system
is temporarily paused to verify the learning loop functionality.

INSTRUCTIONS:
1. Stop the autonomous relay system
2. Run this script to verify learning loop state
3. Restart the autonomous system
"""

import json
import sqlite3
from datetime import datetime

import requests

# Configuration
DB_PATH = r"c:\project-kortana\kortana.db"
API_BASE = "http://localhost:8000"
OUTPUT_FILE = r"c:\project-kortana\BATCH8_FINAL_VERIFICATION.json"


def comprehensive_database_analysis():
    """Perform comprehensive database analysis."""
    print("🔍 COMPREHENSIVE DATABASE ANALYSIS")
    print("=" * 40)

    results = {
        "timestamp": datetime.now().isoformat(),
        "database_analysis": {},
        "learning_loop_status": {},
        "core_beliefs": [],
        "goal_outcomes": [],
        "learning_timeline": {},
        "recommendations": [],
    }

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Basic statistics
        cursor.execute("SELECT COUNT(*) as count FROM core_memories;")
        total_memories = cursor.fetchone()["count"]
        results["database_analysis"]["total_memories"] = total_memories
        print(f"💭 Total memories: {total_memories}")

        # Core beliefs analysis
        cursor.execute(
            "SELECT COUNT(*) as count FROM core_memories WHERE memory_type = 'CORE_BELIEF';"
        )
        belief_count = cursor.fetchone()["count"]
        results["database_analysis"]["core_beliefs_count"] = belief_count
        print(f"🧠 Core beliefs: {belief_count}")

        # Get all core beliefs with details
        cursor.execute("""
            SELECT title, content, created_at, memory_metadata
            FROM core_memories
            WHERE memory_type = 'CORE_BELIEF'
            ORDER BY created_at DESC
        """)
        beliefs = cursor.fetchall()

        for belief in beliefs:
            belief_data = {
                "title": belief["title"],
                "content": belief["content"],
                "created_at": belief["created_at"],
                "is_self_generated": "performance_analysis_task"
                in (belief["memory_metadata"] or ""),
                "metadata": belief["memory_metadata"],
            }
            results["core_beliefs"].append(belief_data)

            # Print belief summary
            print(f"\n  📋 {belief['title']}")
            print(f"      Created: {belief['created_at']}")
            print(f"      Self-generated: {belief_data['is_self_generated']}")
            print(f"      Content: {belief['content'][:100]}...")

        # Learning loop activity analysis
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM core_memories
            WHERE memory_metadata LIKE '%performance_analysis_task%'
        """)
        learning_memories = cursor.fetchone()["count"]
        results["learning_loop_status"]["self_generated_memories"] = learning_memories
        print(f"\n🔬 Learning loop generated memories: {learning_memories}")

        # Goal processing memories
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM core_memories
            WHERE memory_metadata LIKE '%goal_processing_cycle%'
        """)
        goal_processing_memories = cursor.fetchone()["count"]
        results["learning_loop_status"]["goal_processing_memories"] = (
            goal_processing_memories
        )
        print(f"📊 Goal processing memories: {goal_processing_memories}")

        # Get recent goal outcomes
        cursor.execute("""
            SELECT title, content, created_at, memory_metadata
            FROM core_memories
            WHERE memory_metadata LIKE '%goal_processing_cycle%'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        goal_outcomes = cursor.fetchall()

        for outcome in goal_outcomes:
            outcome_data = {
                "title": outcome["title"],
                "content": outcome["content"][:200],
                "created_at": outcome["created_at"],
                "metadata": outcome["metadata"],
            }
            results["goal_outcomes"].append(outcome_data)

        print(f"   Recent goal outcomes: {len(goal_outcomes)} found")

        # Timeline analysis
        if beliefs:
            oldest_belief = min(beliefs, key=lambda x: x["created_at"])
            newest_belief = max(beliefs, key=lambda x: x["created_at"])
            results["learning_timeline"]["first_belief"] = oldest_belief["created_at"]
            results["learning_timeline"]["latest_belief"] = newest_belief["created_at"]

            print("\n📅 Learning timeline:")
            print(f"   First belief: {oldest_belief['created_at']}")
            print(f"   Latest belief: {newest_belief['created_at']}")

        # Goals analysis
        cursor.execute("SELECT COUNT(*) as count FROM goals;")
        total_goals = cursor.fetchone()["count"]
        results["database_analysis"]["total_goals"] = total_goals
        print(f"\n🎯 Total goals in system: {total_goals}")

        # Recent goals
        cursor.execute("""
            SELECT id, description, status, priority, created_at, updated_at
            FROM goals
            ORDER BY created_at DESC
            LIMIT 10
        """)
        recent_goals = cursor.fetchall()

        print(f"   Recent goals: {len(recent_goals)} found")
        for goal in recent_goals[:3]:
            print(f"   • {goal['description'][:50]}... [{goal['status']}]")

        conn.close()

        # Analysis and recommendations
        if learning_memories > 0:
            results["learning_loop_status"]["status"] = "ACTIVE"
            results["learning_loop_status"]["message"] = (
                "Learning loop is generating self-reflective memories"
            )
            results["recommendations"].append("✅ Learning loop is operational")
        elif belief_count > 0 and goal_processing_memories > 0:
            results["learning_loop_status"]["status"] = "READY"
            results["learning_loop_status"]["message"] = (
                "Experiences available for learning"
            )
            results["recommendations"].append("🟡 Monitor for learning loop activation")
        else:
            results["learning_loop_status"]["status"] = "INACTIVE"
            results["learning_loop_status"]["message"] = "No learning activity detected"
            results["recommendations"].append(
                "🔴 Investigate learning loop configuration"
            )

        # Additional recommendations
        if total_goals > 20:
            results["recommendations"].append(
                "📊 Rich goal dataset available for learning"
            )
        if belief_count > 5:
            results["recommendations"].append("🧠 Substantial belief system developing")
        if goal_processing_memories > 50:
            results["recommendations"].append(
                "💪 Extensive experience base for learning"
            )

    except Exception as e:
        results["error"] = str(e)
        print(f"❌ Database analysis error: {e}")

    return results


def test_api_endpoints():
    """Test API endpoints if server is running."""
    print("\n🌐 API ENDPOINT TESTING")
    print("=" * 25)

    api_results = {
        "server_accessible": False,
        "endpoints_tested": {},
        "memories_via_api": 0,
        "goals_via_api": 0,
    }

    try:
        # Test health endpoint
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            api_results["server_accessible"] = True
            print("✅ API server is accessible")

            # Test memories endpoint
            try:
                response = requests.get(f"{API_BASE}/memories/", timeout=10)
                response.raise_for_status()
                memories = response.json()
                api_results["memories_via_api"] = len(memories)
                api_results["endpoints_tested"]["memories"] = "success"
                print(f"✅ Memories endpoint: {len(memories)} memories retrieved")
            except Exception as e:
                api_results["endpoints_tested"]["memories"] = f"error: {e}"
                print(f"❌ Memories endpoint error: {e}")

            # Test goals endpoint
            try:
                response = requests.get(f"{API_BASE}/goals/", timeout=10)
                response.raise_for_status()
                goals = response.json()
                api_results["goals_via_api"] = len(goals)
                api_results["endpoints_tested"]["goals"] = "success"
                print(f"✅ Goals endpoint: {len(goals)} goals retrieved")
            except Exception as e:
                api_results["endpoints_tested"]["goals"] = f"error: {e}"
                print(f"❌ Goals endpoint error: {e}")

        else:
            print("❌ API server not responding")

    except Exception as e:
        print(f"❌ API connection error: {e}")
        api_results["connection_error"] = str(e)

    return api_results


def generate_final_report(db_results, api_results):
    """Generate final verification report."""
    print("\n📋 FINAL VERIFICATION REPORT")
    print("=" * 35)

    report = {
        "verification_timestamp": datetime.now().isoformat(),
        "batch_8_status": "UNKNOWN",
        "database_results": db_results,
        "api_results": api_results,
        "overall_assessment": {},
        "next_steps": [],
    }

    # Overall assessment
    db_beliefs = db_results.get("database_analysis", {}).get("core_beliefs_count", 0)
    learning_status = db_results.get("learning_loop_status", {}).get(
        "status", "UNKNOWN"
    )
    goal_experiences = db_results.get("learning_loop_status", {}).get(
        "goal_processing_memories", 0
    )

    print(f"🧠 Core beliefs found: {db_beliefs}")
    print(f"🔬 Learning loop status: {learning_status}")
    print(f"📊 Goal experiences: {goal_experiences}")

    if learning_status == "ACTIVE":
        report["batch_8_status"] = "SUCCESS"
        report["overall_assessment"]["message"] = (
            "Learning loop is actively generating insights"
        )
        print("\n✅ BATCH 8: SUCCESS - Learning loop is operational!")
    elif learning_status == "READY" and db_beliefs > 0:
        report["batch_8_status"] = "PARTIAL_SUCCESS"
        report["overall_assessment"]["message"] = (
            "Infrastructure ready, awaiting full activation"
        )
        print("\n🟡 BATCH 8: PARTIAL SUCCESS - Ready for activation")
    elif goal_experiences > 0:
        report["batch_8_status"] = "INFRASTRUCTURE_READY"
        report["overall_assessment"]["message"] = (
            "Experiences available, learning pending"
        )
        print("\n🟠 BATCH 8: INFRASTRUCTURE READY - Awaiting learning activation")
    else:
        report["batch_8_status"] = "NEEDS_INVESTIGATION"
        report["overall_assessment"]["message"] = (
            "Learning loop may need troubleshooting"
        )
        print("\n🔴 BATCH 8: NEEDS INVESTIGATION - Check configuration")

    # Next steps
    if learning_status == "ACTIVE":
        report["next_steps"].append("Monitor learning behavior and belief evolution")
        report["next_steps"].append("Test planning improvements with new beliefs")
    else:
        report["next_steps"].append("Verify learning task scheduler configuration")
        report["next_steps"].append("Check autonomous task execution logs")
        report["next_steps"].append("Manually trigger learning loop for testing")

    return report


def main():
    """Main verification function."""
    print("🔬 BATCH 8 FINAL VERIFICATION PROTOCOL")
    print("=" * 45)
    print("Comprehensive learning loop verification\n")

    # Database analysis
    db_results = comprehensive_database_analysis()

    # API testing
    api_results = test_api_endpoints()

    # Final report
    final_report = generate_final_report(db_results, api_results)

    # Save results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Full verification results saved to: {OUTPUT_FILE}")
    print("\n🎓 Batch 8 verification protocol complete!")


if __name__ == "__main__":
    main()
