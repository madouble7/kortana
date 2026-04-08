"""
Phase 7 Cycle #3: Intelligent Task Filtering Service
Multi-source context injection with impact-based prioritization
Enables autonomous evolution targeting the most impactful opportunities
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from src.kortana.database import get_db_manager
from src.kortana.logger import log_error, log_request
from src.kortana.models import GitHubTask


class EvolutionImpactLevel(str, Enum):
    """Impact levels for evolution opportunities"""

    CRITICAL = "critical"  # Core autonomy, security, or HOP engine
    HIGH = "high"  # Performance, stability, or major features
    MEDIUM = "medium"  # Minor enhancements or optimizations
    LOW = "low"  # Documentation or non-critical improvements


@dataclass
class TaskImpactContext:
    """Context information for intelligent task prioritization"""

    task_id: str
    impact_score: float  # 0.0-1.0
    impact_level: EvolutionImpactLevel
    evolution_relevance: bool  # True if task relates to Phase 7 evolution
    complexity_score: float  # 0.0-1.0 (higher = more complex)
    dependencies_count: int  # Number of dependent tasks
    multi_source_signals: Dict[str, Any] = field(default_factory=dict)
    context_injections: List[str] = field(default_factory=list)
    priority_multiplier: float = 1.0

    def get_execution_priority(self) -> float:
        """Calculate final execution priority based on all factors"""
        base_score = self.impact_score

        # Evolution relevance multiplier
        if self.evolution_relevance:
            base_score *= 1.5

        # Dependency reduction (tasks with dependents are prioritized)
        if self.dependencies_count > 0:
            base_score *= 1.0 + (self.dependencies_count * 0.2)

        # Complexity consideration (some tasks must run first regardless of complexity)
        complexity_factor = 1.0 - (self.complexity_score * 0.3)
        base_score *= complexity_factor

        # Apply multi-source signal boost
        if self.multi_source_signals:
            signal_boost = min(len(self.multi_source_signals) * 0.1, 0.3)
            base_score *= 1.0 + signal_boost

        # Apply custom priority multiplier
        base_score *= self.priority_multiplier

        # Clamp to 0-1 range
        return min(max(base_score, 0.0), 1.0)


@dataclass
class ContextInjection:
    """Multi-source context for enriching task analysis"""

    source: str  # "github", "discord", "user", "system"
    signal_type: str  # "mention", "priority_tag", "urgency", "expertise"
    content: str  # The actual context content
    timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 0.8  # 0.0-1.0 confidence in this signal


class TaskFilteringService:
    """Intelligent task filtering with multi-source context injection"""

    def __init__(self):
        """Initialize task filtering service"""
        self.db_manager = get_db_manager()
        self.cached_contexts: Dict[str, List[ContextInjection]] = {}
        self.impact_weights = {
            "github_stars": 0.15,
            "github_forks": 0.1,
            "github_watchers": 0.1,
            "comments_count": 0.1,
            "evolution_tag": 0.3,  # Major weight for Phase 7 related
            "complexity": 0.15,
            "priority_label": 0.2,
        }

    @staticmethod
    def _task_body(task: GitHubTask) -> str:
        """Return task long-form text across legacy/current model shapes."""
        return getattr(task, "body", None) or getattr(task, "description", "") or ""

    async def filter_and_rank_tasks(
        self, tasks: List[GitHubTask], limit: int | None = None
    ) -> List[tuple[GitHubTask, TaskImpactContext]]:
        """
        Filter and rank tasks by impact and relevance

        Args:
            tasks: List of GitHub tasks to filter
            limit: Maximum number of tasks to return

        Returns:
            Sorted list of (task, impact_context) tuples, highest priority first
        """
        ranked_tasks = []

        for task in tasks:
            try:
                impact_context = await self._calculate_task_impact(task)
                ranked_tasks.append((task, impact_context))
            except Exception as e:
                log_error(
                    "task_filtering",
                    f"Failed to calculate impact for task {task.id}: {str(e)}",
                )
                continue

        # Sort by execution priority (highest first)
        ranked_tasks.sort(key=lambda x: x[1].get_execution_priority(), reverse=True)

        if limit:
            ranked_tasks = ranked_tasks[:limit]

        return ranked_tasks

    async def inject_multi_source_context(
        self, task_id: str, sources: List[str] | None = None
    ) -> List[ContextInjection]:
        """
        Inject context from multiple sources (GitHub, Discord, user feedback)

        Args:
            task_id: ID of the task
            sources: List of sources to inject from ("github", "discord", "user", "system")

        Returns:
            List of context injections
        """
        if sources is None:
            sources = ["github", "discord", "user"]

        injections = []

        try:
            # GitHub context injection
            if "github" in sources:
                github_context = await self._inject_github_context(task_id)
                injections.extend(github_context)

            # Discord context injection
            if "discord" in sources:
                discord_context = await self._inject_discord_context(task_id)
                injections.extend(discord_context)

            # User input context
            if "user" in sources:
                user_context = await self._inject_user_context(task_id)
                injections.extend(user_context)

            # Cache injections for reuse
            self.cached_contexts[task_id] = injections

        except Exception as e:
            log_error(
                "task_filtering", f"Failed to inject context for {task_id}: {str(e)}"
            )

        return injections

    async def _calculate_task_impact(self, task: GitHubTask) -> TaskImpactContext:
        """Calculate impact score and context for a single task"""

        # Inject multi-source context
        task_id = str(task.id)
        context_injections = await self.inject_multi_source_context(task_id)

        # Extract impact signals from task
        impact_score = self._calculate_base_impact(task)

        # Determine evolution relevance
        evolution_tags = [
            "autonomy",
            "hop",
            "phase-7",
            "evolution",
            "self-optimization",
        ]

        # Safe string joining for robustness
        title = task.title or ""
        body = self._task_body(task)
        combined_text = (title + " " + body).lower()

        evolution_relevant = any(tag.lower() in combined_text for tag in evolution_tags)

        # Calculate complexity from task body length and type
        complexity_score = min(len(body) / 2000.0, 1.0)

        # Build multi-source signals, preserving all signals per source
        multi_source_signals = defaultdict(list)
        for injection in context_injections:
            multi_source_signals[injection.source].append(
                {
                    "signal_type": injection.signal_type,
                    "confidence": injection.confidence,
                    "content": injection.content,
                }
            )
        # Convert to plain dict for downstream compatibility
        multi_source_signals_dict = dict(multi_source_signals)

        # Count dependencies
        dependencies_count = 0
        if hasattr(task, "depends_on") and task.depends_on:
            dependencies_count = (
                len(task.depends_on.split(","))
                if isinstance(task.depends_on, str)
                else 0
            )

        # Determine impact level
        if impact_score >= 0.7:
            impact_level = EvolutionImpactLevel.CRITICAL
        elif impact_score >= 0.5:
            impact_level = EvolutionImpactLevel.HIGH
        elif impact_score >= 0.3:
            impact_level = EvolutionImpactLevel.MEDIUM
        else:
            impact_level = EvolutionImpactLevel.LOW

        # Apply evolution bonus if relevant
        priority_multiplier = 1.5 if evolution_relevant else 1.0

        return TaskImpactContext(
            task_id=str(task.id),
            impact_score=impact_score,
            impact_level=impact_level,
            evolution_relevance=evolution_relevant,
            complexity_score=complexity_score,
            dependencies_count=dependencies_count,
            multi_source_signals=multi_source_signals_dict,
            context_injections=[inj.content for inj in context_injections],
            priority_multiplier=priority_multiplier,
        )

    def _calculate_base_impact(self, task: GitHubTask) -> float:
        """Calculate base impact score from GitHub task properties"""
        score = 0.0

        # GitHub metrics impact
        github_score = (
            (getattr(task, "github_stars", 0) / 1000.0)
            * self.impact_weights["github_stars"]
            + (getattr(task, "github_forks", 0) / 500.0)
            * self.impact_weights["github_forks"]
            + (getattr(task, "github_watchers", 0) / 500.0)
            * self.impact_weights["github_watchers"]
            + (min(getattr(task, "comments", 0) / 50.0, 1.0))
            * self.impact_weights["comments_count"]
        )
        score += github_score

        # Task label impact
        labels = getattr(task, "labels", "")
        if "critical" in labels.lower() or "urgent" in labels.lower():
            score += self.impact_weights["priority_label"]

        # Evolution relevance impact (high weight for Phase 7 evolution)
        body = self._task_body(task)
        if any(tag in (task.title + " " + body).lower() for tag in ["autonomy", "hop", "phase-7", "evolution"]):
            score += self.impact_weights["evolution_tag"]

        return min(score, 1.0)

    async def _inject_github_context(self, task_id: str) -> List[ContextInjection]:
        """Inject context from GitHub (comments, related issues, PR activity)"""
        injections = []

        try:
            async with self.db_manager.session_scope() as db:
                task = await db.get(GitHubTask, task_id)
                if not task:
                    return injections

                # Check for related evolution discussions
                body = self._task_body(task)
                if "phase-7" in task.title.lower() or "evolution" in body.lower():
                    injections.append(
                        ContextInjection(
                            source="github",
                            signal_type="evolution_related",
                            content=f"Task related to Phase 7 evolution: {task.title}",
                            confidence=0.95,
                        )
                    )

                # Check for expert mentions in comments
                comments = getattr(task, "comments", 0)
                if comments > 10:
                    injections.append(
                        ContextInjection(
                            source="github",
                            signal_type="high_engagement",
                            content=f"High community engagement: {comments} comments",
                            confidence=0.8,
                        )
                    )
        except Exception as e:
            log_error("task_filtering", f"GitHub context injection failed: {str(e)}")

        return injections

    async def _inject_discord_context(self, task_id: str) -> List[ContextInjection]:
        """Inject context from Discord (mentions, discussions, user feedback)"""
        injections = []

        # This integrates with Discord bot if available
        # For now, return empty list - would expand with actual Discord API calls
        try:
            # TODO: Implement Discord API integration
            # This would fetch mentions, reactions, and discussions about this task
            pass
        except Exception as e:
            log_error("task_filtering", f"Discord context injection failed: {str(e)}")

        return injections

    async def _inject_user_context(self, task_id: str) -> List[ContextInjection]:
        """Inject context from user feedback and explicit priorities"""
        injections = []

        try:
            async with self.db_manager.session_scope() as db:
                task = await db.get(GitHubTask, task_id)
                if not task:
                    return injections

                # Check for explicit priority markers
                body = self._task_body(task)
                if "blocking" in task.title.lower() or "blocker" in body.lower():
                    injections.append(
                        ContextInjection(
                            source="user",
                            signal_type="blocking",
                            content="Task identified as blocking critical work",
                            confidence=0.9,
                        )
                    )

                # Check for urgent markers
                if "urgent" in task.title.lower() or "ASAP" in body:
                    injections.append(
                        ContextInjection(
                            source="user",
                            signal_type="urgency",
                            content="Task marked as urgent by user",
                            confidence=0.85,
                        )
                    )
        except Exception as e:
            log_error("task_filtering", f"User context injection failed: {str(e)}")

        return injections

    async def get_highest_impact_tasks(
        self, tasks: List[GitHubTask], count: int = 5
    ) -> List[tuple[GitHubTask, TaskImpactContext]]:
        """
        Get the highest impact tasks for evolution

        Args:
            tasks: List of available tasks
            count: Number of high-impact tasks to return

        Returns:
            Top impact tasks sorted by execution priority
        """
        ranked = await self.filter_and_rank_tasks(tasks, limit=count)

        log_request(
            "task_filtering",
            "phase_7_cycle_3",
            total_tasks=len(tasks),
            selected_count=len(ranked),
            top_task=ranked[0][1].impact_level if ranked else None,
        )

        return ranked
