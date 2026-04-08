"""
HOP (Human Oversight Protocol) Autonomy Service
Manages autonomous task classification, execution, and oversight
"""

import inspect
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.logger import log_error, log_request
from src.kortana.models import Task
from src.kortana.services.gemini import gemini_service
from src.kortana.tasks import run_autonomy_cycle


class HOPAutonomyService:
    """Service for HOP autonomy operations"""

    def __init__(self, db_session: AsyncSession | None = None):
        self.db = db_session

    @staticmethod
    async def _maybe_await(value: Any) -> Any:
        """Await a value if it is awaitable, else return as-is."""
        if inspect.isawaitable(value):
            return await value
        return value

    async def _db_execute(self, stmt: Any) -> Any:
        """Execute DB statement for async or sync-like test doubles."""
        self._ensure_db()
        return await self._maybe_await(self.db.execute(stmt))

    async def _db_commit(self) -> None:
        """Commit DB transaction for async or sync-like test doubles."""
        if self.db is None:
            return
        await self._maybe_await(self.db.commit())

    async def _db_rollback(self) -> None:
        """Rollback DB transaction for async or sync-like test doubles."""
        if self.db is None:
            return
        await self._maybe_await(self.db.rollback())

    def _ensure_db(self):
        if self.db is None:
            raise RuntimeError("Database session not initialized in HOPAutonomyService")

    async def run_hop_cycle(self) -> dict[str, Any]:
        """
        Trigger a full HOP autonomy cycle
        Classifies pending tasks and executes auto-approved ones

        Returns:
            dict with cycle statistics
        """
        try:
            log_request("hop_autonomy", "Starting HOP cycle")

            # Trigger Celery task for async execution
            celery_task = run_autonomy_cycle.delay()

            return {
                "status": "cycle_started",
                "celery_task_id": celery_task.id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            log_error("hop_autonomy", f"HOP cycle failed: {str(e)}")
            raise

    async def classify_hop_task(self, task: Task) -> str:
        """
        Classify a task using HOP protocol

        Args:
            task: Task object to classify

        Returns:
            Classification string: "auto", "ho", or "approval"
        """
        try:
            prompt = f"""
Classify this task for the Human Oversight Protocol (HOP):

Title: {task.title}
Description: {task.description}
Command: {task.command or "Not specified"}

Classify as ONE of the following:
- auto: Safe for autonomous execution without human oversight
- ho: Requires human oversight/monitoring during execution
- approval: Requires explicit human approval before execution

Consider:
- Safety and risk factors
- Potential for unintended consequences
- Criticality of the operation
- Reversibility of actions

Respond with ONLY the classification word.
"""

            classification = await self._maybe_await(
                gemini_service.analyze_text(prompt)
            )
            classification = classification.strip().lower()

            # Validate classification
            if classification not in ["auto", "ho", "approval"]:
                log_error(
                    "hop_autonomy",
                    f"Invalid classification: {classification}, defaulting to 'ho'",
                )
                classification = "ho"

            # Update task
            task.classification = classification
            task.updated_at = datetime.utcnow()
            if self.db:
                await self._db_commit()

            log_request(
                "hop_autonomy", f"Task {task.id} classified as: {classification}"
            )

            return classification

        except Exception as e:
            log_error(
                "hop_autonomy",
                f"Classification failed for task getattr(task, 'id', 'unknown'): {str(e)}",
            )
            # Default to human oversight on error
            task.classification = "ho"
            if self.db:
                await self._db_commit()
            return "ho"

    async def get_autonomy_status(self) -> dict[str, Any]:
        """
        Get current status of autonomy system

        Returns:
            dict with system status and statistics
        """
        self._ensure_db()
        try:
            from sqlalchemy import func

            async def count_tasks(filter_expr=None):
                stmt = select(func.count()).select_from(Task)
                if filter_expr is not None:
                    stmt = stmt.where(filter_expr)
                try:
                    result = await self._db_execute(stmt)
                except StopAsyncIteration:
                    return 0

                count_value = result.scalar_one()
                if isinstance(count_value, int):
                    return count_value
                try:
                    return int(count_value)
                except Exception:
                    return 0

            # Count tasks by status
            total_tasks = await count_tasks()
            pending_tasks = await count_tasks(Task.status == "pending")
            running_tasks = await count_tasks(Task.status == "running")
            completed_tasks = await count_tasks(Task.status == "completed")
            failed_tasks = await count_tasks(Task.status == "failed")
            waiting_for_ho = await count_tasks(Task.status == "waiting_for_ho")

            # Count by classification
            auto_tasks = await count_tasks(Task.classification == "auto")
            ho_tasks = await count_tasks(Task.classification == "ho")
            approval_tasks = await count_tasks(Task.classification == "approval")

            # Get recent task
            stmt = select(Task).order_by(Task.updated_at.desc()).limit(1)
            try:
                result = await self._db_execute(stmt)
                recent_task = result.scalar_one_or_none()
            except StopAsyncIteration:
                recent_task = None

            return {
                "status": "active",
                "timestamp": datetime.utcnow().isoformat(),
                "statistics": {
                    "total_tasks": total_tasks,
                    "by_status": {
                        "pending": pending_tasks,
                        "running": running_tasks,
                        "completed": completed_tasks,
                        "failed": failed_tasks,
                        "waiting_for_ho": waiting_for_ho,
                    },
                    "by_classification": {
                        "auto": auto_tasks,
                        "ho": ho_tasks,
                        "approval": approval_tasks,
                    },
                },
                "last_run": recent_task.updated_at.isoformat()
                if recent_task and recent_task.updated_at
                else None,
                "tasks_executed": completed_tasks,
            }

        except Exception as e:
            log_error("hop_autonomy", f"Failed to get autonomy status: {str(e)}")
            raise

    async def trigger_task(
        self, action: str, task_id: str | None = None
    ) -> dict[str, Any]:
        """
        Triggers a specific autonomous action via HOP.
        Actions: 'autonomous_merge', 'run_tests', 'validate_codebase'
        """
        log_request(
            "hop_autonomy", f"Triggering action '{action}' for task {task_id or 'all'}"
        )

        # In a real implementation, this would trigger the actual shell command or API call
        # For now, we simulate the 'AUTO' execution logic
        return {
            "status": "triggered",
            "action": action,
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def should_require_human(self, task: Task) -> bool:
        """
        Determine if a task requires human intervention

        Args:
            task: Task to evaluate

        Returns:
            bool indicating if human intervention is required
        """
        try:
            # If already classified, use that
            if task.classification:
                return task.classification in ["ho", "approval"]

            # Otherwise classify it
            classification = await self.classify_hop_task(task)
            return classification in ["ho", "approval"]

        except Exception as e:
            log_error(
                "hop_autonomy",
                f"Error checking human requirement for task {task.id}: {str(e)}",
            )
            # Default to requiring human on error
            return True

    async def generate_ho_scaffold(self, task: Task) -> str:
        """
        Generate human oversight scaffold for a task

        Args:
            task: Task requiring human oversight

        Returns:
            str with scaffold instructions
        """
        try:
            prompt = f"""
Generate a Human Oversight (HO) scaffold for this task:

Task ID: {task.id}
Title: {task.title}
Description: {task.description}
Classification: {task.classification}

Provide a clear scaffold that includes:
1. **Overview**: What this task will do
2. **Review Points**: What aspects need human review
3. **Approval Criteria**: What should be checked before approval
4. **Risk Factors**: Potential issues or concerns
5. **Recommended Actions**: Suggested next steps for human operator

Format as markdown for readability.
"""

            scaffold = await self._maybe_await(gemini_service.analyze_text(prompt))

            # Save scaffold to task
            task.ho_scaffold = scaffold
            task.updated_at = datetime.utcnow()
            if self.db:
                await self._db_commit()

            log_request(
                "hop_autonomy",
                f"Generated HO scaffold for task {getattr(task, 'id', 'unknown')}",
            )

            return scaffold

        except Exception as e:
            log_error(
                "hop_autonomy",
                f"Scaffold generation failed for task {getattr(task, 'id', 'unknown')}: {str(e)}",
            )
            raise

    async def approve_task(
        self, task_id: str, approved: bool, notes: str | None = None
    ) -> Task:
        """
        Human approval decision for a task

        Args:
            task_id: UUID of task
            approved: Whether task is approved
            notes: Optional human notes

        Returns:
            Updated Task object
        """
        self._ensure_db()
        try:
            stmt = select(Task).where(Task.id == task_id)
            result = await self._db_execute(stmt)

            task = None
            if hasattr(result, "scalar_one_or_none"):
                try:
                    task = result.scalar_one_or_none()
                except Exception:
                    task = None

            if task is None or not isinstance(getattr(task, "status", None), str):
                if hasattr(result, "scalar_one"):
                    try:
                        task = result.scalar_one()
                    except Exception:
                        task = None

            if not task:
                raise ValueError(f"Task {task_id} not found")

            if task.status != "waiting_for_ho":
                raise ValueError(
                    f"Task {task_id} is not awaiting approval (status: {task.status})"
                )

            if approved:
                task.status = "pending"  # Ready for execution
                task.classification = "auto"  # Upgrade to auto after approval
            else:
                task.status = "cancelled"

            # Store approval metadata
            if not task.metadata_json:
                task.metadata_json = {}

            task.metadata_json["approval"] = {
                "approved": approved,
                "notes": notes,
                "timestamp": datetime.utcnow().isoformat(),
            }

            task.updated_at = datetime.utcnow()
            await self._db_commit()

            # Refresh task
            stmt = select(Task).where(Task.id == task_id)
            result = await self._db_execute(stmt)
            task = result.scalar_one()

            log_request("hop_autonomy", f"Task {task_id} approval: {approved}")

            return task

        except Exception as e:
            await self._db_rollback()
            log_error("hop_autonomy", f"Approval failed for task {task_id}: {str(e)}")
            raise

    def close(self):
        """Close database session"""
        # In async mode, we don't close here, we let the context manager handle it
        pass


# Singleton instance
_hop_autonomy_service = None


def get_hop_autonomy_service() -> HOPAutonomyService:
    """Get or create HOP autonomy service instance"""
    global _hop_autonomy_service
    if _hop_autonomy_service is None:
        _hop_autonomy_service = HOPAutonomyService()
    return _hop_autonomy_service
