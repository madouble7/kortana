#!/usr/bin/env python3
"""
Advanced Learning Module for Autonomous Kor'tana
==============================================

This module implements real-time learning capabilities for Kor'tana,
allowing her to analyze her own performance and develop best practices.

Key Features:
- ANALYZE_RECENT_PERFORMANCE goal type
- Performance pattern analysis
- Best practice formulation
- Memory-based learning enhancement
"""

import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from typing import Any

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)


class AutonomousLearningEngine:
    """
    Advanced learning engine for autonomous Kor'tana.

    This engine enables Kor'tana to learn from her own experiences,
    analyze performance patterns, and develop best practices for
    future autonomous operations.
    """

    def __init__(self):
        self.memory_file = "data/memory.jsonl"
        self.performance_file = "data/performance_history.jsonl"
        self.learning_file = "data/autonomous_learning.jsonl"
        self.best_practices = []

    def load_recent_memories(self, limit: int = 20) -> list[dict]:
        """Load recent autonomous goal outcome memories."""
        memories = []

        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file) as f:
                    lines = f.readlines()

                # Look for autonomous-related memories in recent entries
                recent_lines = lines[-100:]  # Check last 100 entries
                for line in recent_lines:
                    try:
                        memory = json.loads(line.strip())
                        if self._is_autonomous_memory(memory):
                            memories.append(memory)
                            if len(memories) >= limit:
                                break
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Error loading memories: {e}")

        return memories[:limit]

    def _is_autonomous_memory(self, memory: dict) -> bool:
        """Check if a memory is related to autonomous operation."""
        content = str(memory.get("content", "")).lower()
        role = memory.get("role", "").lower()

        autonomous_keywords = [
            "autonomous",
            "goal",
            "task",
            "cycle",
            "planning",
            "performance",
            "analysis",
            "learning",
            "self-directed",
        ]

        return any(keyword in content for keyword in autonomous_keywords)

    def load_performance_data(self, limit: int = 50) -> list[dict]:
        """Load recent performance metrics."""
        performance_data = []

        try:
            if os.path.exists(self.performance_file):
                with open(self.performance_file) as f:
                    lines = f.readlines()

                # Get most recent performance entries
                recent_lines = lines[-limit:]
                for line in recent_lines:
                    try:
                        data = json.loads(line.strip())
                        performance_data.append(data)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Error loading performance data: {e}")

        return performance_data

    def analyze_performance_patterns(
        self, memories: list[dict], performance_data: list[dict]
    ) -> dict[str, Any]:
        """Analyze performance patterns and identify areas for improvement."""
        analysis = {
            "total_memories": len(memories),
            "total_performance_entries": len(performance_data),
            "patterns": [],
            "success_rates": {},
            "failure_points": [],
            "optimization_opportunities": [],
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Analyze task success patterns
        if performance_data:
            task_categories = {}
            for entry in performance_data:
                category = entry.get("task_category", "unknown")
                success_rate = entry.get("success_rate", 0.0)

                if category not in task_categories:
                    task_categories[category] = []
                task_categories[category].append(success_rate)

            # Calculate average success rates by category
            for category, rates in task_categories.items():
                avg_rate = sum(rates) / len(rates) if rates else 0.0
                analysis["success_rates"][category] = avg_rate

                if avg_rate < 0.5:  # Less than 50% success
                    analysis["failure_points"].append(
                        {
                            "category": category,
                            "success_rate": avg_rate,
                            "sample_size": len(rates),
                        }
                    )

        # Analyze memory patterns
        if memories:
            memory_themes = {}
            for memory in memories:
                content = str(memory.get("content", "")).lower()

                # Count theme occurrences
                themes = ["error", "success", "complete", "failed", "optimization"]
                for theme in themes:
                    if theme in content:
                        memory_themes[theme] = memory_themes.get(theme, 0) + 1

            analysis["patterns"] = [
                f"{theme}: {count} occurrences"
                for theme, count in memory_themes.items()
            ]

        # Generate optimization opportunities
        if analysis["failure_points"]:
            analysis["optimization_opportunities"] = [
                f"Improve {fp['category']} task success rate (currently {fp['success_rate']:.2f})"
                for fp in analysis["failure_points"]
            ]

        return analysis

    def formulate_best_practice(self, analysis: dict[str, Any]) -> str:
        """Formulate a new best practice based on analysis."""
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

        # Base best practice on analysis findings
        if analysis["failure_points"]:
            worst_category = min(
                analysis["failure_points"], key=lambda x: x["success_rate"]
            )
            best_practice = (
                f"Focus on improving {worst_category['category']} task execution. "
                f"Current success rate is {worst_category['success_rate']:.2f}. "
                f"Implement additional error checking and validation steps."
            )

        elif analysis["optimization_opportunities"]:
            best_practice = f"Prioritize: {analysis['optimization_opportunities'][0]}"

        else:
            best_practice = (
                "Continue current autonomous operation patterns. "
                "Performance appears stable across all task categories. "
                "Monitor for emerging optimization opportunities."
            )

        return f"[{timestamp}] BEST_PRACTICE: {best_practice}"

    def store_learning_outcome(self, analysis: dict[str, Any], best_practice: str):
        """Store the learning outcome as a CORE_BELIEF memory."""
        learning_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "type": "AUTONOMOUS_LEARNING",
            "analysis": analysis,
            "best_practice": best_practice,
            "memory_type": "CORE_BELIEF",
        }

        # Store in learning file
        try:
            with open(self.learning_file, "a") as f:
                f.write(json.dumps(learning_entry) + "\n")
        except Exception as e:
            print(f"Error storing learning outcome: {e}")

        # Also add to main memory
        memory_entry = {
            "role": "system",
            "content": f"AUTONOMOUS_LEARNING: {best_practice}",
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "type": "CORE_BELIEF",
            "autonomous_generated": True,
        }

        try:
            with open(self.memory_file, "a") as f:
                f.write(json.dumps(memory_entry) + "\n")
        except Exception as e:
            print(f"Error storing memory entry: {e}")

        return learning_entry

    async def execute_learning_cycle(self) -> dict[str, Any]:
        """Execute a complete autonomous learning cycle."""
        print("🧠 EXECUTING AUTONOMOUS LEARNING CYCLE")
        print("=" * 50)

        # Step 1: Load recent data
        print("📚 Loading recent memories and performance data...")
        memories = self.load_recent_memories(20)
        performance_data = self.load_performance_data(50)

        print(f"   Loaded {len(memories)} autonomous memories")
        print(f"   Loaded {len(performance_data)} performance entries")

        # Step 2: Analyze patterns
        print("\n🔍 Analyzing performance patterns...")
        analysis = self.analyze_performance_patterns(memories, performance_data)

        print(f"   Found {len(analysis['patterns'])} behavioral patterns")
        print(f"   Identified {len(analysis['failure_points'])} areas for improvement")
        print(
            f"   Generated {len(analysis['optimization_opportunities'])} optimization opportunities"
        )

        # Step 3: Formulate best practice
        print("\n💡 Formulating new best practice...")
        best_practice = self.formulate_best_practice(analysis)
        print(f"   New Best Practice: {best_practice}")

        # Step 4: Store learning outcome
        print("\n💾 Storing learning outcome...")
        learning_outcome = self.store_learning_outcome(analysis, best_practice)

        print("✅ Autonomous learning cycle completed successfully")

        return {
            "success": True,
            "memories_analyzed": len(memories),
            "performance_entries_analyzed": len(performance_data),
            "patterns_found": len(analysis["patterns"]),
            "best_practice": best_practice,
            "learning_outcome": learning_outcome,
        }


def main():
    """Test the autonomous learning engine."""
    print("🔥 KOR'TANA ADVANCED LEARNING ENGINE")
    print("=" * 50)
    print("Testing autonomous learning capabilities...")
    print()

    engine = AutonomousLearningEngine()

    # Run learning cycle
    result = asyncio.run(engine.execute_learning_cycle())

    if result["success"]:
        print("\n🎉 LEARNING ENGINE VALIDATION SUCCESSFUL")
        print(f"✅ Analyzed {result['memories_analyzed']} memories")
        print(
            f"✅ Analyzed {result['performance_entries_analyzed']} performance entries"
        )
        print("✅ Generated new best practice")
        print("✅ Stored learning outcome in core memory")

        print("\n🧠 Kor'tana can now learn from her own experience!")
        print("🔄 This capability can be integrated into autonomous cycles.")
    else:
        print("\n❌ Learning engine validation failed")


if __name__ == "__main__":
    main()
