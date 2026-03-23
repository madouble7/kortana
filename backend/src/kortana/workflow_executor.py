"""
Task Dependency Management for Autonomous Workflows
Enables composition of Celery tasks with dependencies, allowing workflows like:
- Task B waits for Task A output
- Multiple tasks run in parallel then combine results
- Conditional task execution based on results
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional

from celery import group
from redis import Redis

from src.kortana.distributed_lock import DistributedLock
from src.kortana.exceptions import KortanaException
from src.kortana.logger import get_logger

logger = get_logger(__name__)


class TaskDependencyType(Enum):
    """Types of task dependencies"""

    SEQUENTIAL = "sequential"  # Task B waits for Task A
    PARALLEL = "parallel"  # Tasks run together
    CONDITIONAL = "conditional"  # Task B only if Task A succeeds
    AGGREGATING = "aggregating"  # Multiple tasks then combine


@dataclass
class TaskNode:
    """Represents a task in a workflow"""

    task_name: str
    task_args: tuple = field(default_factory=tuple)
    task_kwargs: dict = field(default_factory=dict)
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dependencies: list[str] = field(default_factory=list)
    retry_on_failure: bool = True
    max_retries: int = 3
    timeout: int = 300

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WorkflowDefinition:
    """Autonomous workflow definition"""

    workflow_id: str
    name: str
    description: str
    nodes: dict[str, TaskNode] = field(default_factory=dict)  # node_id -> TaskNode
    created_at: float = field(default_factory=lambda: __import__("time").time())
    status: str = "draft"  # draft, active, completed, failed

    def add_task(
        self,
        task_name: str,
        task_args: Optional[tuple[Any, ...]] = None,
        task_kwargs: Optional[dict[str, Any]] = None,
        node_id: Optional[str] = None,
        dependencies: Optional[list[str]] = None,
    ) -> str:
        """Add task node to workflow"""
        node_id = node_id or str(uuid.uuid4())
        node = TaskNode(
            task_name=task_name,
            task_args=task_args or (),
            task_kwargs=task_kwargs or {},
            node_id=node_id,
            dependencies=dependencies or [],
        )
        self.nodes[node_id] = node
        return node_id

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """Add dependency between tasks"""
        if task_id in self.nodes:
            self.nodes[task_id].dependencies.append(depends_on)

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "created_at": self.created_at,
            "status": self.status,
        }


class WorkflowExecutor:
    """
    Executes autonomous workflows with dependency management
    Uses Celery chains, groups, and chords for composition
    """

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.prefix = "workflow:"

    def _get_workflow_key(self, workflow_id: str) -> str:
        """Get Redis key for workflow"""
        return f"{self.prefix}{workflow_id}"

    def save_workflow(self, workflow: WorkflowDefinition) -> None:
        """Persist workflow definition"""
        key = self._get_workflow_key(workflow.workflow_id)
        data = json.dumps(workflow.to_dict())
        # Keep workflow for 30 days
        self.redis.setex(key, 2592000, data)
        logger.info(f"Saved workflow: {workflow.name} ({workflow.workflow_id})")

    def load_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Load workflow definition"""
        key = self._get_workflow_key(workflow_id)
        data = self.redis.get(key)
        if data:
            try:
                workflow_dict = json.loads(data)
                # Reconstruct workflow
                workflow = WorkflowDefinition(
                    workflow_id=workflow_dict["workflow_id"],
                    name=workflow_dict["name"],
                    description=workflow_dict["description"],
                    created_at=workflow_dict["created_at"],
                    status=workflow_dict["status"],
                )
                for node_id, node_dict in workflow_dict["nodes"].items():
                    # Reconstruct task node
                    node = TaskNode(**node_dict)
                    workflow.nodes[node_id] = node
                return workflow
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Failed to load workflow {workflow_id}: {e}")
        return None

    def _build_celery_workflow(self, workflow: WorkflowDefinition) -> Any:
        """Build Celery task signature from workflow"""
        nodes = workflow.nodes

        # Group tasks by dependency level (topological sort)
        levels = self._topological_sort(nodes)

        if not levels:
            logger.warning(f"Empty workflow: {workflow.name}")
            return None

        # Build Celery task graph
        task_sigs = {}
        for node_id, node in nodes.items():
            from src.kortana.celery_app import app as celery_app

            sig = celery_app.signature(
                node.task_name,
                args=node.task_args,
                kwargs=node.task_kwargs,
                options={"max_retries": node.max_retries, "time_limit": node.timeout},
            )
            task_sigs[node_id] = sig

        # Handle different dependency patterns
        if len(levels) == 1 and len(levels[0]) == 1:
            # Single task
            single_node_id = levels[0][0]
            return task_sigs[single_node_id]

        if len(levels) == 1:
            # All tasks parallel (group)
            return group(task_sigs[node_id] for node_id in levels[0])

        # Mixed: chains of groups (sequential groups of parallel tasks)
        workflow_sig = None
        for level_nodes in levels:
            if len(level_nodes) == 1:
                level_sig = task_sigs[level_nodes[0]]
            else:
                level_sig = group(task_sigs[node_id] for node_id in level_nodes)

            if workflow_sig is None:
                workflow_sig = level_sig
            else:
                workflow_sig = workflow_sig | level_sig  # Chain

        return workflow_sig

    def _topological_sort(self, nodes: dict[str, TaskNode]) -> list[list[str]]:
        """
        Sort tasks by dependency level
        Returns list of levels, where each level contains nodes that can run in parallel
        Raises KortanaException on circular dependency
        """
        # Build adjacency info
        in_degree = {node_id: len(node.dependencies) for node_id, node in nodes.items()}
        levels = []
        processed: set[str] = set()

        while len(processed) < len(nodes):
            # Find all nodes with no unprocessed dependencies
            current_level = [
                node_id
                for node_id, degree in in_degree.items()
                if degree == 0 and node_id not in processed
            ]

            if not current_level:
                # Circular dependency detected
                logger.error("Circular dependency detected in workflow DAG")
                raise KortanaException(
                    message="The workflow graph contains cycles and cannot be executed.",
                    status_code=400,
                    error_code="CIRCULAR_DEPENDENCY",
                )

            levels.append(current_level)
            processed.update(current_level)

            # Reduce in-degree for dependent nodes
            for node_id in current_level:
                # Find all nodes that depend on this one
                for other_id, other_node in nodes.items():
                    if node_id in other_node.dependencies:
                        in_degree[other_id] -= 1

        return levels

    def execute(self, workflow: WorkflowDefinition) -> tuple[str, Optional[dict]]:
        """
        Execute workflow with dependency management and sharded locking.

        Args:
            workflow: WorkflowDefinition to execute

        Returns:
            Tuple of (task_id, initial_result)
        """
        # Shard the lock namespace for workflows to prevent collision with individual tasks
        lock_name = f"workflow:lock:{workflow.workflow_id}"

        with DistributedLock(self.redis, lock_name, timeout=600):
            try:
                # Save workflow
                workflow.status = "active"
                self.save_workflow(workflow)

                # Build Celery task graph (triggers topological sort + DAG validation)
                celery_task = self._build_celery_workflow(workflow)

                if celery_task is None:
                    logger.error(f"Failed to build workflow: {workflow.name}")
                    return workflow.workflow_id, None

                # Submit to Celery
                result = celery_task.apply_async()
                logger.info(
                    f"Executing active workflow: {workflow.name} (task_id={result.id})"
                )

                return result.id, {"workflow_id": workflow.workflow_id}

            except KortanaException:
                # Re-raise architectural exceptions
                workflow.status = "failed"
                self.save_workflow(workflow)
                raise
            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                workflow.status = "failed"
                self.save_workflow(workflow)
                raise


def create_autonomous_review_workflow() -> WorkflowDefinition:
    """Example: Code review workflow with dependencies"""
    workflow = WorkflowDefinition(
        workflow_id=str(uuid.uuid4()),
        name="Autonomous Code Review Workflow",
        description="Fetch issues → Analyze code → Generate review → Create PR",
    )

    # Task 1: Fetch GitHub issues
    fetch_id = workflow.add_task(
        "src.kortana.tasks.fetch_github_issues",
        task_kwargs={"max_issues": 10},
    )

    # Task 2: Analyze code (depends on fetch)
    analyze_id = workflow.add_task(
        "src.kortana.tasks.analyze_code_batch",
        task_kwargs={"analysis_type": "security"},
        dependencies=[fetch_id],
    )

    # Task 3: Generate review (depends on analyze)
    review_id = workflow.add_task(
        "src.kortana.tasks.generate_code_review",
        task_kwargs={"review_format": "detailed"},
        dependencies=[analyze_id],
    )

    # Task 4: Create PR (depends on review)
    workflow.add_task(
        "src.kortana.tasks.create_pr_from_review",
        task_kwargs={"auto_merge": False},
        dependencies=[review_id],
    )

    return workflow


def create_parallel_autonomy_workflow() -> WorkflowDefinition:
    """Example: Parallel autonomy checks (GitHub monitor + Health check + Cache cleanup)"""
    workflow = WorkflowDefinition(
        workflow_id=str(uuid.uuid4()),
        name="Parallel Autonomy Checks",
        description="Run monitoring tasks in parallel, then aggregate results",
    )

    # Three parallel tasks (no dependencies)
    github_id = workflow.add_task(
        "src.kortana.tasks.monitor_github_issues",
        task_kwargs={"timeout": 30},
    )

    health_id = workflow.add_task(
        "src.kortana.tasks.check_system_health",
        task_kwargs={"check_type": "full"},
    )

    cache_id = workflow.add_task(
        "src.kortana.tasks.cleanup_expired_cache",
        task_kwargs={"dry_run": False},
    )

    # Task 4: Aggregate results (depends on all three)
    workflow.add_task(
        "src.kortana.tasks.aggregate_autonomy_results",
        dependencies=[github_id, health_id, cache_id],
    )

    return workflow
