"""
Celery Configuration and Beat Scheduler
Autonomous task scheduling with health-aware scheduling
"""

import os
from celery import Celery, Task
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from kombu import Exchange, Queue

from config import get_settings

settings = get_settings()

# Create Celery app
app = Celery(
    "kortana",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)

# Configure Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    result_expires=3600,  # Expire results after 1 hour
    task_acks_late=True,  # Only ack after task completes
    task_reject_on_worker_lost=True,  # Re-queue if worker crashes
)

# Define queues for different task types
app.conf.task_queues = (
    Queue(
        "high_priority",
        Exchange("high_priority", type="direct"),
        routing_key="high_priority",
    ),
    Queue(
        "default", Exchange("default", type="direct"), routing_key="default"
    ),
    Queue(
        "low_priority",
        Exchange("low_priority", type="direct"),
        routing_key="low_priority",
    ),
    Queue(
        "scheduled",
        Exchange("scheduled", type="direct"),
        routing_key="scheduled",
    ),
)

# Task routing
app.conf.task_routes = {
    "tasks.process_github_issue": {"queue": "high_priority"},
    "tasks.create_pr": {"queue": "high_priority"},
    "tasks.run_tests": {"queue": "default"},
    "tasks.analyze_code": {"queue": "default"},
    "tasks.health_check": {"queue": "low_priority"},
    "tasks.cleanup_old_data": {"queue": "low_priority"},
}

# Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Health checks every 5 minutes
    "health-check": {
        "task": "tasks.health_check",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "low_priority"},
    },
    # Process GitHub issues every minute
    "process-github-issues": {
        "task": "tasks.process_pending_github_issues",
        "schedule": crontab(minute="*/1"),
        "options": {"queue": "default"},
    },
    # Cleanup old data daily at 2 AM
    "cleanup-old-data": {
        "task": "tasks.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "low_priority"},
    },
    # Sync GitHub repo every 30 minutes
    "sync-github-repo": {
        "task": "tasks.sync_github_repo",
        "schedule": crontab(minute="*/30"),
        "options": {"queue": "default"},
    },
    # Analyze code quality every 6 hours
    "analyze-code-quality": {
        "task": "tasks.analyze_code_quality",
        "schedule": crontab(hour="*/6"),
        "options": {"queue": "default"},
    },
}

logger = get_task_logger(__name__)


class CallbackTask(Task):
    """Task base class with callbacks"""

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(f"Task {task_id} retried: {exc}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"Task {task_id} failed: {exc}")

    def on_success(self, result, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"Task {task_id} succeeded")


app.Task = CallbackTask


@app.task(bind=True, max_retries=3, queue="default")
def health_check(self):
    """Periodic health check"""
    try:
        from database import get_db
        import redis

        # Check PostgreSQL
        db = next(get_db())
        db.execute("SELECT 1")

        # Check Redis
        r = redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True
        )
        r.ping()

        logger.info("Health check passed")
        return {"status": "healthy", "database": "ok", "cache": "ok"}

    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@app.task(bind=True, max_retries=3, queue="high_priority")
def process_github_issue(self, issue_number: int, repo: str):
    """Process a single GitHub issue"""
    try:
        from github_automation import get_github_engine
        import asyncio

        engine = get_github_engine()
        result = asyncio.run(
            engine.analyze_issue(
                issue_number=issue_number,
                repo=repo,
            )
        )

        logger.info(f"Processed GitHub issue #{issue_number}")
        return {"issue_number": issue_number, "status": "processed"}

    except Exception as exc:
        logger.error(f"Failed to process issue #{issue_number}: {exc}")
        raise self.retry(exc=exc, countdown=120)  # Retry after 2 minutes


@app.task(bind=True, max_retries=3, queue="high_priority")
def create_pr(self, issue_number: int, branch_name: str, title: str):
    """Create a pull request"""
    try:
        from github_automation import get_github_engine
        import asyncio

        engine = get_github_engine()
        result = asyncio.run(
            engine.create_pull_request(
                issue_number=issue_number,
                branch_name=branch_name,
                title=title,
                description="",
            )
        )

        logger.info(f"Created PR for issue #{issue_number}")
        return {"issue_number": issue_number, "pr_number": result.get("number")}

    except Exception as exc:
        logger.error(f"Failed to create PR for issue #{issue_number}: {exc}")
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


@app.task(bind=True, queue="default")
def process_pending_github_issues(self):
    """Process all pending GitHub issues"""
    try:
        logger.info("Processing pending GitHub issues")
        # This would query the database for pending issues
        # and dispatch individual process_github_issue tasks
        return {"status": "started"}
    except Exception as exc:
        logger.error(f"Failed to process pending issues: {exc}")


@app.task(bind=True, queue="default")
def sync_github_repo(self):
    """Sync with GitHub repository"""
    try:
        from github_automation import get_github_engine

        engine = get_github_engine()
        logger.info("Syncing with GitHub repository")
        # Fetch new issues, PRs, and events
        return {"status": "synced"}

    except Exception as exc:
        logger.error(f"Failed to sync GitHub repo: {exc}")


@app.task(bind=True, queue="default")
def analyze_code_quality(self):
    """Analyze code quality across the repo"""
    try:
        logger.info("Analyzing code quality")
        # Run linting, type checking, complexity analysis
        return {"status": "analyzed"}

    except Exception as exc:
        logger.error(f"Failed to analyze code quality: {exc}")


@app.task(bind=True, queue="low_priority")
def cleanup_old_data(self):
    """Clean up old execution records and logs"""
    try:
        from database import get_db
        from datetime import datetime, timedelta

        db = next(get_db())
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        # Delete old execution records
        db.execute(
            "DELETE FROM agent_executions WHERE completed_at < :cutoff",
            {"cutoff": cutoff_date},
        )

        logger.info("Cleaned up old data")
        return {"status": "cleaned"}

    except Exception as exc:
        logger.error(f"Failed to cleanup old data: {exc}")
