"""
Task Queue Service for Kor'tana
Manages task creation, enqueueing, and status tracking

Phase 7 Enhancement: Priority-based execution, dependency resolution,
health-aware queue management with atomic batch operations
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from celery.result import AsyncResult

from src.kortana.database import SessionLocal
from src.kortana.logger import log_error, log_request
from src.kortana.models import Task
from src.kortana.tasks import analyze_image, execute_hop_task, process_chat


class QueueHealthStatus(str, Enum):
    """Queue health states for graceful degradation"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class TaskExecutionContext:
    """Context for coordinated task execution with dependencies"""

    task_id: str
    dependencies: list[str] = field(default_factory=list)
    dependent_tasks: list[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3

    def can_execute(self, completed_tasks: set[str]) -> bool:
        """Check if all dependencies are satisfied"""
        return all(dep in completed_tasks for dep in self.dependencies)


@dataclass
class QueueMetrics:
    """Metrics for queue health monitoring"""

    total_tasks: int = 0
    pending_tasks: int = 0
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_execution_time: float = 0.0
    queue_saturation: float = 0.0  # 0.0-1.0
    health_status: QueueHealthStatus = QueueHealthStatus.HEALTHY


class TaskQueueService:
    """Service for managing task queue operations with priority and health awareness"""

    def __init__(self, max_concurrent: int = 10):
        """Initialize queue service with health monitoring

        Args:
            max_concurrent: Maximum concurrent tasks before queue becomes degraded
        """
        self.db = SessionLocal()
        self.max_concurrent = max_concurrent
        self.execution_contexts: dict[str, TaskExecutionContext] = {}
        self.completed_tasks: set[str] = set()
        self.metrics = QueueMetrics()

    def calculate_queue_health(self) -> QueueHealthStatus:
        """Calculate health status based on queue saturation"""
        try:
            active = self.db.query(Task).filter(Task.status == "active").count()

            saturation = (
                (active / self.max_concurrent) if self.max_concurrent > 0 else 0.0
            )

            if saturation > 0.9:
                return QueueHealthStatus.CRITICAL
            elif saturation > 0.7:
                return QueueHealthStatus.DEGRADED
            else:
                return QueueHealthStatus.HEALTHY
        except Exception as e:
            log_error("task_queue", f"Failed to calculate queue health: {str(e)}")
            return QueueHealthStatus.HEALTHY

    def get_queue_metrics(self) -> dict[str, Any]:
        """Get current queue metrics for monitoring"""
        try:
            total = self.db.query(Task).count()
            pending = self.db.query(Task).filter(Task.status == "pending").count()
            active = self.db.query(Task).filter(Task.status == "active").count()
            completed = self.db.query(Task).filter(Task.status == "completed").count()
            failed = self.db.query(Task).filter(Task.status == "failed").count()

            health = self.calculate_queue_health()
            saturation = (
                (active / self.max_concurrent) if self.max_concurrent > 0 else 0.0
            )

            self.metrics = QueueMetrics(
                total_tasks=total,
                pending_tasks=pending,
                active_tasks=active,
                completed_tasks=completed,
                failed_tasks=failed,
                queue_saturation=saturation,
                health_status=health,
            )

            return {
                "total_tasks": total,
                "pending_tasks": pending,
                "active_tasks": active,
                "completed_tasks": completed,
                "failed_tasks": failed,
                "queue_saturation": round(saturation, 2),
                "health_status": health.value,
                "max_concurrent": self.max_concurrent,
            }
        except Exception as e:
            log_error("task_queue", f"Failed to get queue metrics: {str(e)}")
            return {}

    async def enqueue_task_with_dependencies(
        self, task_data: dict[str, Any], dependencies: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Enqueue task with optional dependency tracking

        Args:
            task_data: Task metadata (title, description, priority, etc.)
            dependencies: List of task IDs that must complete first

        Returns:
            Created task with dependency context
        """
        try:
            task_id = str(uuid4())
            dependencies = dependencies or []

            # Validate dependencies exist
            if dependencies:
                for dep_id in dependencies:
                    dep_task = self.db.query(Task).filter(Task.id == dep_id).first()
                    if not dep_task:
                        raise ValueError(f"Dependency task not found: {dep_id}")

            # Create task
            task = Task(
                id=task_id,
                title=task_data.get("title"),
                description=task_data.get("description"),
                priority=task_data.get("priority", 5),
                command=task_data.get("command"),
                classification=task_data.get("classification", "auto"),
                status="pending",
                created_at=datetime.utcnow(),
            )

            self.db.add(task)
            self.db.commit()

            # Track execution context
            context = TaskExecutionContext(
                task_id=task_id,
                dependencies=dependencies,
            )
            self.execution_contexts[task_id] = context

            log_request("task_queue", f"Task created with dependencies: {task_id}")

            return {
                "task_id": task_id,
                "dependencies": dependencies,
                "priority": task.priority,
                "status": "pending",
            }
        except Exception as e:
            self.db.rollback()
            log_error(
                "task_queue", f"Failed to enqueue task with dependencies: {str(e)}"
            )
            raise

    async def get_next_executable_tasks(self, limit: int = 5) -> list[dict[str, Any]]:
        """
        Get next executable tasks based on priority and dependencies

        Respects queue health: degraded/critical reduces batch size

        Args:
            limit: Max tasks to return

        Returns:
            List of executable tasks ordered by priority
        """
        try:
            health = self.calculate_queue_health()

            # Reduce batch size during degradation
            if health == QueueHealthStatus.CRITICAL:
                limit = max(1, limit // 3)
            elif health == QueueHealthStatus.DEGRADED:
                limit = max(2, limit // 2)

            # Get pending tasks ordered by priority
            pending_tasks = (
                self.db.query(Task)
                .filter(Task.status == "pending")
                .order_by(Task.priority.desc())
                .all()
            )

            executable = []
            for task in pending_tasks:
                if len(executable) >= limit:
                    break

                context = self.execution_contexts.get(task.id)

                # Check if dependencies satisfied
                if context and not context.can_execute(self.completed_tasks):
                    continue

                executable.append(
                    {
                        "id": task.id,
                        "title": task.title,
                        "priority": task.priority,
                        "dependencies": context.dependencies if context else [],
                    }
                )

            return executable
        except Exception as e:
            log_error("task_queue", f"Failed to get executable tasks: {str(e)}")
            return []

    async def enqueue_task(self, task_data: dict[str, Any]) -> Task:
        """
        Create and enqueue a task

        Args:
            task_data: Dictionary containing task information
                - title: str
                - description: str (optional)
                - priority: int (1-10, default 5)
                - command: str (optional)
                - classification: str (default "auto")

        Returns:
            Created Task object
        """
        try:
            # Create task in database
            task = Task(
                id=str(uuid4()),
                title=task_data.get("title"),
                description=task_data.get("description"),
                priority=task_data.get("priority", 5),
                command=task_data.get("command"),
                classification=task_data.get("classification", "auto"),
                status="pending",
                created_at=datetime.utcnow(),
            )

            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)

            log_request("task_queue", f"Task created: {task.id} - {task.title}")

            return task

        except Exception as e:
            self.db.rollback()
            log_error("task_queue", f"Failed to create task: {str(e)}")
            raise

    async def execute_task(self, task_id: str) -> dict[str, Any]:
        """
        Execute a task immediately via Celery

        Args:
            task_id: UUID of task to execute

        Returns:
            dict with celery task info
        """
        try:
            # Get task from src.kortana.database
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")

            # Enqueue to Celery
            celery_task = execute_hop_task.delay(task_id)

            log_request("task_queue", f"Task enqueued to Celery: {task_id}")

            return {
                "task_id": task_id,
                "celery_task_id": celery_task.id,
                "status": "enqueued",
            }

        except Exception as e:
            log_error("task_queue", f"Failed to execute task {task_id}: {str(e)}")
            raise

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """
        Get current status of a task

        Args:
            task_id: UUID of task

        Returns:
            dict with task status information
        """
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")

            return {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "classification": task.classification,
                "priority": task.priority,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat()
                if task.completed_at
                else None,
                "result": task.result,
                "error": task.error,
            }

        except Exception as e:
            log_error("task_queue", f"Failed to get task status {task_id}: {str(e)}")
            raise

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending task

        Args:
            task_id: UUID of task to cancel

        Returns:
            bool indicating success
        """
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return False

            if task.status in ["completed", "failed"]:
                return False  # Cannot cancel completed/failed tasks

            task.status = "cancelled"
            task.updated_at = datetime.utcnow()
            self.db.commit()

            log_request("task_queue", f"Task cancelled: {task_id}")
            return True

        except Exception as e:
            self.db.rollback()
            log_error("task_queue", f"Failed to cancel task {task_id}: {str(e)}")
            raise

    async def list_tasks(
        self, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        List tasks with optional filtering

        Args:
            status: Filter by status (optional)
            limit: Max number of tasks to return
            offset: Pagination offset

        Returns:
            List of task dictionaries
        """
        try:
            query = self.db.query(Task)

            if status:
                query = query.filter(Task.status == status)

            tasks = (
                query.order_by(Task.created_at.desc()).limit(limit).offset(offset).all()
            )

            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "classification": t.classification,
                    "priority": t.priority,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in tasks
            ]

        except Exception as e:
            log_error("task_queue", f"Failed to list tasks: {str(e)}")
            raise

    async def enqueue_chat(
        self, message: str, conversation_id: str | None = None
    ) -> dict[str, Any]:
        """
        Enqueue a chat message for processing

        Args:
            message: User message text
            conversation_id: Optional conversation ID

        Returns:
            dict with celery task info
        """
        try:
            celery_task = process_chat.delay(message, conversation_id)

            log_request("task_queue", f"Chat enqueued: {celery_task.id}")

            return {
                "celery_task_id": celery_task.id,
                "status": "enqueued",
                "message": message[:100],
            }

        except Exception as e:
            log_error("task_queue", f"Failed to enqueue chat: {str(e)}")
            raise

    async def enqueue_image_analysis(
        self, image_url: str, prompt: str
    ) -> dict[str, Any]:
        """
        Enqueue an image for analysis

        Args:
            image_url: URL to image
            prompt: Analysis prompt

        Returns:
            dict with celery task info
        """
        try:
            celery_task = analyze_image.delay(image_url, prompt)

            log_request("task_queue", f"Image analysis enqueued: {celery_task.id}")

            return {
                "celery_task_id": celery_task.id,
                "status": "enqueued",
                "image_url": image_url,
            }

        except Exception as e:
            log_error("task_queue", f"Failed to enqueue image analysis: {str(e)}")
            raise

    async def get_celery_result(self, celery_task_id: str) -> dict[str, Any]:
        """
        Get result of a Celery task

        Args:
            celery_task_id: Celery task ID

        Returns:
            dict with task result and status
        """
        try:
            result = AsyncResult(celery_task_id)

            return {
                "celery_task_id": celery_task_id,
                "status": result.status,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
                "result": result.result if result.ready() else None,
            }

        except Exception as e:
            log_error(
                "task_queue", f"Failed to get Celery result {celery_task_id}: {str(e)}"
            )
            raise

    def close(self):
        """Close database session"""
        self.db.close()


# Singleton instance
_task_queue_service = None


def get_task_queue_service() -> TaskQueueService:
    """Get or create task queue service instance"""
    global _task_queue_service
    if _task_queue_service is None:
        _task_queue_service = TaskQueueService()
    return _task_queue_service
