"""
Goal Engine for Kor'tana
Enables environmental scanning and autonomous goal generation.
"""

import logging
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class GoalType(Enum):
    MAINTENANCE = "maintenance"
    OPTIMIZATION = "optimization"
    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    RESEARCH = "research"
    LEARNING = "learning"

@dataclass
class Goal:
    id: str
    type: GoalType
    title: str
    description: str
    priority: int
    created_at: datetime
    due_date: datetime | None = None
    completed_at: datetime | None = None
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"

class GoalEngine:
    def __init__(self):
        # Import here to avoid circular imports
        from kortana.core.execution_engine import execution_engine
        from kortana.services.memory_system import memory_manager
        self.execution_engine = execution_engine
        self.memory_manager = memory_manager

    def scan_environment(self) -> list[Goal]:
        """
        Scans the environment to identify potential goals based on:
        - Project files and their status
        - System performance metrics
        - User requests and feedback
        - Outstanding issues and bugs
        """
        goals = []

        # Scan project files
        project_status = self._scan_project_files()
        if project_status["needs_optimization"]:
            goals.append(Goal(
                id=f"opt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                type=GoalType.OPTIMIZATION,
                title="Code Optimization Required",
                description=f"Optimize {project_status['high_complexity_files']} high complexity files",
                priority=2,
                created_at=datetime.now()
            ))

        # Scan system performance
        performance_metrics = self._scan_system_performance()
        if performance_metrics["memory_usage"] > 85:
            goals.append(Goal(
                id=f"maint_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                type=GoalType.MAINTENANCE,
                title="High Memory Usage Alert",
                description="Investigate and optimize memory usage",
                priority=1,
                created_at=datetime.now()
            ))

        # Scan for research opportunities
        research_topics = self._identify_research_opportunities()
        goals.extend([
            Goal(
                id=f"research_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}",
                type=GoalType.RESEARCH,
                title=f"Research: {topic}",
                description=f"Investigate and learn about {topic}",
                priority=3,
                created_at=datetime.now()
            )
            for i, topic in enumerate(research_topics)
        ])

        return goals

    def prioritize_goals(self, goals: list[Goal]) -> list[Goal]:
        """
        Prioritize goals based on type, urgency, and dependencies.
        Returns a sorted list of goals.
        """
        # Priority weights for different goal types
        type_weights = {
            GoalType.MAINTENANCE: 5,  # High priority for system health
            GoalType.BUG_FIX: 4,     # Critical for stability
            GoalType.OPTIMIZATION: 3, # Important for performance
            GoalType.FEATURE: 2,      # New capabilities
            GoalType.RESEARCH: 1,     # Long-term improvement
            GoalType.LEARNING: 1      # Long-term improvement
        }

        # Sort goals by weighted priority
        return sorted(goals, key=lambda g: (
            g.priority * type_weights[g.type],
            -len(g.dependencies or []),  # Fewer dependencies first
            g.created_at.timestamp()     # Older goals first
        ), reverse=True)

    def execute_goal(self, goal: Goal) -> bool:
        """
        Execute a goal using the appropriate strategy based on goal type.
        Returns True if execution was successful.
        """
        try:
            if goal.type == GoalType.MAINTENANCE:
                return self._execute_maintenance_goal(goal)
            elif goal.type == GoalType.OPTIMIZATION:
                return self._execute_optimization_goal(goal)
            elif goal.type == GoalType.RESEARCH:
                return self._execute_research_goal(goal)
            else:
                logger.warning(f"No execution strategy for goal type: {goal.type}")
                return False
        except Exception as e:
            logger.error(f"Failed to execute goal {goal.id}: {e}")
            return False

    def _execute_maintenance_goal(self, goal: Goal) -> bool:
        """Execute maintenance-type goals"""
        if "memory usage" in goal.description.lower():
            # Clean up memory-intensive processes
            result = self.execution_engine.execute_shell_command("wmic process where \"workingsetsize > 100000000\" get commandline,processid,workingsetsize")
            if not result["success"]:
                return False

            # Log memory-intensive processes
            logger.info(f"Memory usage analysis:\n{result['stdout']}")
            return True
        return False

    def _execute_optimization_goal(self, goal: Goal) -> bool:
        """Execute optimization-type goals"""
        if "high complexity files" in goal.description.lower():
            try:
                files = goal.description.split("Optimize ")[1].strip("[]").split(", ")
                for file_path in files:
                    content = self.execution_engine.read_file(f"src/{file_path}")
                    if content["success"]:
                        # Simple optimization: Split large functions
                        self._optimize_file_complexity(file_path, content["content"])
                return True
            except Exception as e:
                logger.error(f"Failed to optimize files: {e}")
        return False

    def _execute_research_goal(self, goal: Goal) -> bool:
        """Execute research-type goals"""
        try:
            topic = goal.title.split("Research: ")[1]
            # Store research topic in memory system
            self.memory_manager.store_research_topic(topic, goal.description)
            return True
        except Exception as e:
            logger.error(f"Failed to store research topic: {e}")
            return False

    def _optimize_file_complexity(self, file_path: str, content: str) -> None:
        """
        Optimize a file by splitting complex functions.
        This is a simplified implementation - in reality, this would use
        more sophisticated code analysis and transformation.
        """
        logger.info(f"Optimizing file complexity: {file_path}")
        # Implementation will be added in future updates
        return None

    def _scan_project_files(self) -> dict[str, list[str] | bool]:
        """Analyzes project files for potential improvements"""
        result = {
            "needs_optimization": False,
            "high_complexity_files": []
        }

        try:
            file_list = self.execution_engine.list_directory("src")
            if not file_list["success"]:
                return result

            for item in file_list["items"]:
                if item["type"] == "file" and item["name"].endswith(".py"):
                    content = self.execution_engine.read_file(f"src/{item['name']}")
                    if content["success"] and content["content"].count("def ") > 10:
                        result["needs_optimization"] = True
                        result["high_complexity_files"].append(item["name"])
        except Exception as e:
            logger.error(f"Error scanning project files: {e}")

        return result

    def _scan_system_performance(self) -> dict[str, float]:
        """Monitors system performance metrics"""
        metrics = {
            "memory_usage": 0.0,
            "cpu_usage": 0.0,
            "disk_usage": 0.0
        }

        try:
            # Use execution engine to get system metrics
            result = self.execution_engine.execute_shell_command("wmic CPU get loadpercentage")
            if result["success"]:
                with suppress(ValueError, IndexError):
                    metrics["cpu_usage"] = float(result["stdout"].split("\n")[1])

            # Memory usage
            result = self.execution_engine.execute_shell_command("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize")
            if result["success"]:
                with suppress(ValueError, IndexError):
                    lines = result["stdout"].strip().split("\n")
                    total = float(lines[1].split()[1])
                    free = float(lines[1].split()[0])
                    metrics["memory_usage"] = ((total - free) / total) * 100

        except Exception as e:
            logger.error(f"Error scanning system performance: {e}")

        return metrics

    def _identify_research_opportunities(self) -> list[str]:
        """Identifies areas where research could improve system capabilities"""
        try:
            # Check recent memory entries for knowledge gaps
            recent_interactions = self.memory_manager.get_recent_interactions(limit=100)
            knowledge_gaps = {
                interaction.split("about")[1].split(".")[0].strip()
                for interaction in recent_interactions
                if "I don't know" in interaction or "I'm not sure" in interaction
            }
            return list(knowledge_gaps)[:5]  # Limit to top 5 research opportunities
        except Exception as e:
            logger.error(f"Error identifying research opportunities: {e}")
            return []

# Create a global instance
goal_engine = GoalEngine()
