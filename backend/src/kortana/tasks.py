"""
Celery Task Definitions for Kor'tana
Background tasks for chat processing, image analysis, and autonomy cycles
"""

from datetime import datetime
from typing import Any

from src.kortana.celery_app import app
from src.kortana.database import SessionLocal
from src.kortana.logger import log_error, log_request
from src.kortana.models import Task
from src.kortana.services.gemini import gemini_service
from src.kortana.services.github_autonomy_service import GitHubAutonomyService


@app.task(bind=True, max_retries=3)
def process_chat(self, message: str, conversation_id: str | None = None) -> dict[str, Any]:
    """
    Process chat message with Gemini AI

    Args:
        message: User message text
        conversation_id: Optional conversation ID for context

    Returns:
        dict with response text and metadata
    """
    try:
        log_request("celery_task", f"Processing chat: {message[:50]}...")

        # Use sync version of Gemini service for better performance
        response = gemini_service.analyze_text_sync(message)

        return {
            "response": response,
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed",
        }
    except Exception as exc:
        log_error("celery_task", f"Chat processing failed: {str(exc)}")
        self.retry(exc=exc, countdown=60)


@app.task(bind=True, max_retries=3)
def analyze_image(self, image_url: str, prompt: str = "Analyze this image") -> dict[str, Any]:
    """
    Analyze image using Gemini Vision

    Args:
        image_url: URL or path to image
        prompt: Analysis prompt

    Returns:
        dict with analysis results
    """
    try:
        log_request("celery_task", f"Analyzing image: {image_url}")

        from io import BytesIO

        import PIL.Image
        import requests

        # Download image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        image = PIL.Image.open(BytesIO(response.content))

        # Analyze with Gemini (using sync version for performance)
        analysis = gemini_service.analyze_multimodal_sync(prompt, [image])

        return {
            "analysis": analysis,
            "image_url": image_url,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed",
        }
    except Exception as exc:
        log_error("celery_task", f"Image analysis failed: {str(exc)}")
        self.retry(exc=exc, countdown=120)


@app.task(bind=True)
def run_autonomy_cycle() -> dict[str, Any]:
    """
    Run HOP autonomy cycle - classify and execute tasks

    Returns:
        dict with cycle results and statistics
    """
    try:
        log_request("celery_task", "Starting autonomy cycle")

        db = SessionLocal()
        try:
            # Get all pending HOP-capable tasks
            pending_tasks = (
                db.query(Task)
                .filter(Task.status == "pending", Task.classification == "auto")
                .limit(10)
                .all()
            )

            executed_count = 0
            failed_count = 0

            for task in pending_tasks:
                try:
                    # Classify task
                    classification = _classify_task(task)
                    task.classification = classification

                    if classification == "auto":
                        # Execute automatically
                        result = _execute_task(task)
                        task.status = "completed"
                        task.result = result
                        task.completed_at = datetime.utcnow()
                        executed_count += 1
                    elif classification == "ho":
                        # Requires human oversight
                        task.status = "waiting_for_ho"
                        task.ho_scaffold = _generate_scaffold(task)

                    task.updated_at = datetime.utcnow()
                    db.commit()

                except Exception as e:
                    log_error("celery_task", f"Task {task.id} execution failed: {str(e)}")
                    task.status = "failed"
                    task.error = str(e)
                    task.updated_at = datetime.utcnow()
                    db.commit()
                    failed_count += 1

            return {
                "total_processed": len(pending_tasks),
                "executed": executed_count,
                "failed": failed_count,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed",
            }

        finally:
            db.close()

    except Exception as exc:
        log_error("celery_task", f"Autonomy cycle failed: {str(exc)}")
        raise


@app.task(name="tasks.run_github_autonomy_cycle")
def run_github_autonomy_cycle() -> dict[str, Any]:
    """
    Run GitHub autonomous development cycle.
    Fetches issues, analyzes them, plans fixes, and executes if in autonomous mode.
    """
    try:
        log_request("celery_task", "Starting GitHub autonomy cycle")

        # We don't use async here because Celery workers are usually sync
        # but the service might use async httpx.
        # For simplicity, we'll use a temporary event loop if needed,
        # or just make the service operations sync where possible.
        # Since the service uses 'await', we need to run it in a loop.

        import asyncio

        loop = asyncio.get_event_loop()

        service = GitHubAutonomyService()
        try:
            # 1. Fetch and queue new issues
            new_tasks = loop.run_until_complete(service.fetch_and_queue_issues())

            # 2. Process tasks through the pipeline
            loop.run_until_complete(service.process_next_tasks(limit=3))

            return {
                "new_tasks_found": len(new_tasks),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed",
            }
        finally:
            service.close()

    except Exception as exc:
        log_error("celery_task", f"GitHub autonomy cycle failed: {str(exc)}")
        return {"status": "failed", "error": str(exc)}


@app.task(bind=True, max_retries=3)
def execute_hop_task(self, task_id: str) -> dict[str, Any]:
    """
    Execute a specific HOP task

    Args:
        task_id: Task ID to execute

    Returns:
        dict with execution results
    """
    try:
        log_request("celery_task", f"Executing HOP task: {task_id}")

        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")

            # Update status
            task.status = "running"
            task.started_at = datetime.utcnow()
            db.commit()

            # Execute task
            result = _execute_task(task)

            # Update with results
            task.status = "completed"
            task.result = result
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            db.commit()

            return {
                "task_id": task_id,
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed",
            }

        finally:
            db.close()

    except Exception as exc:
        log_error("celery_task", f"HOP task {task_id} execution failed: {str(exc)}")

        # Update task status
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = "failed"
                task.error = str(exc)
                task.updated_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()

        self.retry(exc=exc, countdown=300)


def _classify_task(task: Task) -> str:
    """
    Classify task as auto, ho, or approval

    Args:
        task: Task to classify

    Returns:
        Classification string
    """

    # Use Gemini to classify
    prompt = f"""
Classify this task for autonomous execution:

Title: {task.title}
Description: {task.description}

Classify as one of:
- auto: Can be executed autonomously without human oversight
- ho: Requires human oversight or approval
- approval: Requires explicit human approval before execution

Respond with only the classification.
"""

    classification = gemini_service.analyze_text_sync(prompt)
    classification = classification.strip().lower()

    if classification not in ["auto", "ho", "approval"]:
        return "ho"  # Default to human oversight if unclear

    return classification


def _execute_task(task: Task) -> str:
    """
    Execute a task using Gemini

    Args:
        task: Task to execute

    Returns:
        Execution result string
    """

    prompt = f"""
Execute this task:

Title: {task.title}
Description: {task.description}
Command: {task.command or 'Not specified'}

Provide a detailed execution result or implementation.
"""

    result = gemini_service.analyze_text_sync(prompt)
    return result


def _generate_scaffold(task: Task) -> str:
    """
    Generate human oversight scaffold for task

    Args:
        task: Task needing HO

    Returns:
        Scaffold instructions
    """

    prompt = f"""
Generate a human oversight scaffold for this task:

Title: {task.title}
Description: {task.description}

Provide:
1. What needs human review
2. Approval criteria
3. Risk factors
4. Recommended next steps
"""

    scaffold = gemini_service.analyze_text_sync(prompt)
    return scaffold
