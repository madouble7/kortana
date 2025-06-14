#!/usr/bin/env python3
"""
Silent database inspection for Batch 8 learning loop verification.
This script writes results to a file without interfering with terminal output.
"""

import json
import os
import sqlite3
from datetime import datetime

# Paths
db_path = r"c:\project-kortana\kortana.db"
output_path = r"c:\project-kortana\learning_verification_results.json"


def silent_inspect():
    """Inspect database and write results to JSON file."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "inspection_type": "Batch 8 Learning Loop Verification",
        "database_path": db_path,
        "status": "unknown",
        "memories": {},
        "goals": {},
        "learning_analysis": {},
        "errors": [],
    }

    try:
        if not os.path.exists(db_path):
            results["errors"].append(f"Database not found: {db_path}")
            results["status"] = "error"
            return results

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check memories
        try:
            cursor.execute("SELECT COUNT(*) as count FROM core_memories;")
            results["memories"]["total"] = cursor.fetchone()["count"]

            cursor.execute(
                "SELECT COUNT(*) as count FROM core_memories WHERE memory_type = 'CORE_BELIEF';"
            )
            results["memories"]["core_beliefs"] = cursor.fetchone()["count"]

            # Get recent core beliefs
            cursor.execute("""
                SELECT title, content, created_at, memory_metadata
                FROM core_memories
                WHERE memory_type = 'CORE_BELIEF'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            beliefs = cursor.fetchall()
            results["memories"]["recent_beliefs"] = []
            for belief in beliefs:
                results["memories"]["recent_beliefs"].append(
                    {
                        "title": belief["title"],
                        "content": belief["content"][:200] + "..."
                        if len(belief["content"]) > 200
                        else belief["content"],
                        "created_at": belief["created_at"],
                        "is_self_generated": "performance_analysis_task"
                        in (belief["memory_metadata"] or ""),
                    }
                )

            # Check for learning loop activity
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM core_memories
                WHERE memory_metadata LIKE '%performance_analysis_task%'
            """)
            results["learning_analysis"]["self_generated_memories"] = cursor.fetchone()[
                "count"
            ]

            # Check goal processing memories
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM core_memories
                WHERE memory_metadata LIKE '%goal_processing_cycle%'
            """)
            results["learning_analysis"]["goal_experiences"] = cursor.fetchone()[
                "count"
            ]

        except Exception as e:
            results["errors"].append(f"Memory query error: {str(e)}")

        # Check goals
        try:
            cursor.execute("SELECT COUNT(*) as count FROM goals;")
            results["goals"]["total"] = cursor.fetchone()["count"]

            # Get recent goals
            cursor.execute("""
                SELECT id, description, status, priority, created_at
                FROM goals
                ORDER BY created_at DESC
                LIMIT 10
            """)
            goals = cursor.fetchall()
            results["goals"]["recent_goals"] = []
            for goal in goals:
                results["goals"]["recent_goals"].append(
                    {
                        "id": goal["id"],
                        "description": goal["description"][:100] + "..."
                        if len(goal["description"]) > 100
                        else goal["description"],
                        "status": goal["status"],
                        "priority": goal["priority"],
                        "created_at": goal["created_at"],
                    }
                )

        except Exception as e:
            results["errors"].append(f"Goals query error: {str(e)}")

        conn.close()

        # Analyze learning loop status
        self_generated = results["learning_analysis"].get("self_generated_memories", 0)
        goal_experiences = results["learning_analysis"].get("goal_experiences", 0)
        core_beliefs = results["memories"].get("core_beliefs", 0)

        if self_generated > 0:
            results["learning_analysis"]["status"] = "active"
            results["learning_analysis"]["message"] = (
                "Learning loop is active - Kor'tana has generated her own beliefs!"
            )
        elif core_beliefs > 0 and goal_experiences > 0:
            results["learning_analysis"]["status"] = "ready"
            results["learning_analysis"]["message"] = (
                "Learning loop is ready - experiences exist, awaiting next analysis cycle"
            )
        elif goal_experiences > 0:
            results["learning_analysis"]["status"] = "pending"
            results["learning_analysis"]["message"] = (
                "Experiences available for learning, but no beliefs generated yet"
            )
        else:
            results["learning_analysis"]["status"] = "inactive"
            results["learning_analysis"]["message"] = "No learning activity detected"

        results["status"] = "success"

    except Exception as e:
        results["errors"].append(f"Database connection error: {str(e)}")
        results["status"] = "error"

    return results


def main():
    """Main function to run inspection and save results."""
    results = silent_inspect()

    # Write results to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Also create a simple text summary
    summary_path = r"c:\project-kortana\learning_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("BATCH 8 LEARNING LOOP VERIFICATION SUMMARY\n")
        f.write("=" * 50 + "\n")
        f.write(f"Timestamp: {results['timestamp']}\n")
        f.write(f"Status: {results['status']}\n\n")

        if results["status"] == "success":
            f.write(f"💭 Total memories: {results['memories'].get('total', 0)}\n")
            f.write(f"🧠 Core beliefs: {results['memories'].get('core_beliefs', 0)}\n")
            f.write(f"🎯 Total goals: {results['goals'].get('total', 0)}\n")
            f.write(
                f"🔬 Self-generated memories: {results['learning_analysis'].get('self_generated_memories', 0)}\n"
            )
            f.write(
                f"📊 Goal experiences: {results['learning_analysis'].get('goal_experiences', 0)}\n\n"
            )

            f.write(
                f"Learning Status: {results['learning_analysis'].get('status', 'unknown')}\n"
            )
            f.write(
                f"Message: {results['learning_analysis'].get('message', 'No message')}\n\n"
            )

            if results["memories"].get("recent_beliefs"):
                f.write("Recent Core Beliefs:\n")
                for i, belief in enumerate(results["memories"]["recent_beliefs"], 1):
                    f.write(f"{i}. {belief['title']}\n")
                    f.write(f"   Self-generated: {belief['is_self_generated']}\n")
                    f.write(f"   Created: {belief['created_at']}\n")
                    f.write(f"   Content: {belief['content']}\n\n")

        if results["errors"]:
            f.write("Errors:\n")
            for error in results["errors"]:
                f.write(f"❌ {error}\n")


if __name__ == "__main__":
    main()
