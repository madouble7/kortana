"""
KOR'TANA Intelligent Task Prioritization System

Replaces FIFO task processing with dynamic priority queuing based on:
- Impact potential (lines of code changed, tests affected)
- Evolution relevance (advancement toward autonomous goals)
- Dependency chains (blocking other tasks)
- Time sensitivity (deadlines, SLAs)
- Real-time signals (user mentions, test failures)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from src.kortana.logger import get_logger

logger = get_logger(__name__)


class TaskPriority(Enum):
    """Priority levels"""

    CRITICAL = 5  # System stability threatened
    HIGH = 4  # Major progression blocker
    MEDIUM = 3  # Standard autonomous work
    LOW = 2  # Nice-to-have improvements
    DEFERRED = 1  # Can wait indefinitely


class TaskSignal(Enum):
    """Real-time signals affecting priority"""

    USER_MENTION = "user_mention"
    TEST_FAILURE = "test_failure"
    PERFORMANCE_REGRESSION = "perf_regression"
    SECURITY_FINDING = "security"
    BUILD_BLOCKER = "build_blocker"
    API_QUOTA_PRESSURE = "quota_pressure"


@dataclass
class TaskPriorityScore:
    """Composite priority score with weighted factors"""

    task_id: str
    base_priority: TaskPriority = TaskPriority.MEDIUM

    # Weighted scoring factors (0.0 to 1.0)
    impact_score: float = 0.0  # Code impact magnitude
    evolution_score: float = 0.0  # Advancement toward autonomy goals
    dependency_score: float = 0.0  # Blocks other important work
    urgency_score: float = 0.0  # Time sensitivity
    signal_multiplier: float = 1.0  # Real-time signal boost

    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    signal_history: list[TaskSignal] = field(default_factory=list)
    score_history: list[float] = field(default_factory=list)

    # Weights (must sum to <1.0 to allow signal multiplier to boost)
    WEIGHT_IMPACT = 0.25
    WEIGHT_EVOLUTION = 0.30
    WEIGHT_DEPENDENCY = 0.20
    WEIGHT_URGENCY = 0.15
    # 0.10 reserved for signal multiplier

    @property
    def final_score(self) -> float:
        """Calculate weighted final priority score"""
        base_score = (
            self.impact_score * self.WEIGHT_IMPACT
            + self.evolution_score * self.WEIGHT_EVOLUTION
            + self.dependency_score * self.WEIGHT_DEPENDENCY
            + self.urgency_score * self.WEIGHT_URGENCY
        )

        # Apply signal multiplier (can boost up to 1.4x)
        final = base_score * self.signal_multiplier

        # Add base priority weight (ensures critical/high don't get deprioritized)
        final += self.base_priority.value * 0.05

        return min(final, 10.0)  # Cap at 10.0

    def record_signal(self, signal: TaskSignal) -> None:
        """Record a real-time signal and adjust multiplier"""
        self.signal_history.append(signal)

        # Adjust multiplier based on signal type
        if signal == TaskSignal.BUILD_BLOCKER:
            self.signal_multiplier = min(self.signal_multiplier * 1.4, 2.0)
        elif signal in (TaskSignal.TEST_FAILURE, TaskSignal.SECURITY_FINDING):
            self.signal_multiplier = min(self.signal_multiplier * 1.3, 1.8)
        elif signal == TaskSignal.USER_MENTION:
            self.signal_multiplier = min(self.signal_multiplier * 1.1, 1.5)
        elif signal == TaskSignal.API_QUOTA_PRESSURE:
            self.signal_multiplier = max(self.signal_multiplier * 0.8, 0.5)

        logger.debug(
            f"Task {self.task_id}: Signal {signal.value}, "
            f"multiplier now {self.signal_multiplier:.2f}"
        )

    def add_to_history(self) -> None:
        """Record current score to history for trending"""
        self.score_history.append(self.final_score)


class IntelligentTaskQueue:
    """
    Priority queue that dynamically ranks tasks based on multiple factors.
    Prevents starvation of lower-priority work while focusing on high-impact tasks.
    """

    def __init__(self, max_queue_size: int = 1000):
        self.max_queue_size = max_queue_size
        self.tasks: dict[str, TaskPriorityScore] = {}
        self.execution_history: list[tuple[str, float, datetime]] = []

    def add_task(
        self,
        task_id: str,
        base_priority: TaskPriority = TaskPriority.MEDIUM,
        impact_score: float = 0.0,
        evolution_score: float = 0.0,
        dependency_score: float = 0.0,
        urgency_score: float = 0.0,
    ) -> Optional[TaskPriorityScore]:
        """
        Add task to queue with priority factors.

        Args:
            task_id: Unique task identifier
            base_priority: Base priority level
            impact_score: 0.0-1.0, estimated code/system impact
            evolution_score: 0.0-1.0, advancement toward autonomy
            dependency_score: 0.0-1.0, blocks other important work
            urgency_score: 0.0-1.0, time sensitivity (deadline proximity)

        Returns:
            TaskPriorityScore object for this task, or None if queue is full
        """
        if len(self.tasks) >= self.max_queue_size:
            logger.warning(f"Task queue at capacity ({self.max_queue_size})")
            return None

        task_score = TaskPriorityScore(
            task_id=task_id,
            base_priority=base_priority,
            impact_score=min(impact_score, 1.0),
            evolution_score=min(evolution_score, 1.0),
            dependency_score=min(dependency_score, 1.0),
            urgency_score=min(urgency_score, 1.0),
        )

        self.tasks[task_id] = task_score
        logger.info(
            f"Task {task_id} queued with score {task_score.final_score:.2f} "
            f"(impact={impact_score:.1f}, evolution={evolution_score:.1f})"
        )
        return task_score

    def peek_next(self) -> Optional[tuple[str, float]]:
        """
        Get next task to execute without removing it.

        Returns:
            (task_id, score) of highest priority task, or None if empty
        """
        if not self.tasks:
            return None

        best_task = max(self.tasks.items(), key=lambda x: x[1].final_score)
        return (best_task[0], best_task[1].final_score)

    def pop_next(self) -> Optional[tuple[str, TaskPriorityScore]]:
        """
        Remove and return next task to execute.

        Returns:
            (task_id, TaskPriorityScore) of highest priority task, or None if empty
        """
        if not self.tasks:
            return None

        best_task_id, best_score = max(
            self.tasks.items(), key=lambda x: x[1].final_score
        )

        del self.tasks[best_task_id]
        best_score.add_to_history()

        self.execution_history.append(
            (best_task_id, best_score.final_score, datetime.utcnow())
        )

        logger.info(
            f"Executing task {best_task_id} with priority score {best_score.final_score:.2f}"
        )

        return (best_task_id, best_score)

    def update_signals(self, task_id: str, signals: list[TaskSignal]) -> None:
        """Update task priority based on new real-time signals"""
        task = self.tasks.get(task_id)
        if not task:
            return

        for signal in signals:
            task.record_signal(signal)

    def get_queue_status(self) -> dict:
        """Get current queue status"""
        if not self.tasks:
            return {"size": 0, "next_task": None, "tasks": []}

        next_task_id, next_score = self.peek_next()
        tasks_sorted = sorted(
            self.tasks.items(),
            key=lambda x: x[1].final_score,
            reverse=True,
        )[:10]  # Top 10

        return {
            "size": len(self.tasks),
            "next_task": next_task_id,
            "next_score": next_score,
            "top_tasks": [
                {
                    "task_id": task_id,
                    "score": score.final_score,
                    "priority": score.base_priority.name,
                    "signals": [s.value for s in score.signal_history[-3:]],
                }
                for task_id, score in tasks_sorted
            ],
        }

    def get_starving_tasks(self, threshold_seconds: int = 3600) -> list[str]:
        """Find tasks waiting too long (prevent starvation)"""
        now = datetime.utcnow()
        starving = []

        for task_id, task_score in self.tasks.items():
            wait_time = (now - task_score.created_at).total_seconds()
            if wait_time > threshold_seconds:
                starving.append(task_id)

        if starving:
            logger.warning(
                f"Found {len(starving)} starving tasks "
                f"(waiting >{threshold_seconds}s)"
            )

        return starving

    def boost_priority(self, task_id: str, boost_factor: float = 1.5) -> None:
        """Temporarily boost a task's priority"""
        task = self.tasks.get(task_id)
        if task:
            task.signal_multiplier *= boost_factor
            logger.info(
                f"Boosted task {task_id} by {boost_factor}x, "
                f"new multiplier: {task.signal_multiplier:.2f}"
            )
