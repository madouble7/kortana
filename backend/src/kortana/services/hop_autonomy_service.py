"""
HOP (Human Oversight Protocol) Autonomy Service
Manages autonomous task classification, execution, and oversight
"""

from datetime import datetime
from typing import Any

from src.kortana.database import SessionLocal
from src.kortana.logger import log_error, log_request
from src.kortana.models import Task
from src.kortana.services.gemini import gemini_service
from src.kortana.tasks import run_autonomy_cycle


class HOPAutonomyService:
    """Service for HOP autonomy operations"""

    def __init__(self):
        self.db = SessionLocal()

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
Command: {task.command or 'Not specified'}

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

            classification = await gemini_service.analyze_text(prompt)
            classification = classification.strip().lower()

            # Validate classification
            if classification not in ["auto", "ho", "approval"]:
                log_error(
                    "hop_autonomy", f"Invalid classification: {classification}, defaulting to 'ho'"
                )
                classification = "ho"

            # Update task
            task.classification = classification
            task.updated_at = datetime.utcnow()
            self.db.commit()

            log_request("hop_autonomy", f"Task {task.id} classified as: {classification}")

            return classification

        except Exception as e:
            log_error("hop_autonomy", f"Classification failed for task {task.id}: {str(e)}")
            # Default to human oversight on error
            task.classification = "ho"
            self.db.commit()
            return "ho"

    async def get_autonomy_status(self) -> dict[str, Any]:
        """
        Get current status of autonomy system

        Returns:
            dict with system status and statistics
        """
        try:
            # Count tasks by status
            total_tasks = self.db.query(Task).count()
            pending_tasks = self.db.query(Task).filter(Task.status == "pending").count()
            running_tasks = self.db.query(Task).filter(Task.status == "running").count()
            completed_tasks = self.db.query(Task).filter(Task.status == "completed").count()
            failed_tasks = self.db.query(Task).filter(Task.status == "failed").count()
            waiting_for_ho = self.db.query(Task).filter(Task.status == "waiting_for_ho").count()

            # Count by classification
            auto_tasks = self.db.query(Task).filter(Task.classification == "auto").count()
            ho_tasks = self.db.query(Task).filter(Task.classification == "ho").count()
            approval_tasks = self.db.query(Task).filter(Task.classification == "approval").count()

            # Get recent task
            recent_task = self.db.query(Task).order_by(Task.updated_at.desc()).first()

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
                "hop_autonomy", f"Error checking human requirement for task {task.id}: {str(e)}"
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

            scaffold = await gemini_service.analyze_text(prompt)

            # Save scaffold to task
            task.ho_scaffold = scaffold
            task.updated_at = datetime.utcnow()
            self.db.commit()

            log_request("hop_autonomy", f"Generated HO scaffold for task {task.id}")

            return scaffold

        except Exception as e:
            log_error("hop_autonomy", f"Scaffold generation failed for task {task.id}: {str(e)}")
            raise

    async def approve_task(self, task_id: str, approved: bool, notes: str | None = None) -> Task:
        """
        Human approval decision for a task

        Args:
            task_id: UUID of task
            approved: Whether task is approved
            notes: Optional human notes

        Returns:
            Updated Task object
        """
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")

            if task.status != "waiting_for_ho":
                raise ValueError(f"Task {task_id} is not awaiting approval (status: {task.status})")

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
            self.db.commit()
            self.db.refresh(task)

            log_request("hop_autonomy", f"Task {task_id} approval: {approved}")

            return task

        except Exception as e:
            self.db.rollback()
            log_error("hop_autonomy", f"Approval failed for task {task_id}: {str(e)}")
            raise

    def close(self):
        """Close database session"""
        self.db.close()


# Singleton instance
_hop_autonomy_service = None


def get_hop_autonomy_service() -> HOPAutonomyService:
    """Get or create HOP autonomy service instance"""
    global _hop_autonomy_service
    if _hop_autonomy_service is None:
        _hop_autonomy_service = HOPAutonomyService()
    return _hop_autonomy_service
