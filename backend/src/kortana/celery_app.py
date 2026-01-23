"""
Celery Application Configuration for Kor'tana
Background task processing using Redis as broker
"""

import os

from celery import Celery
from celery.schedules import crontab
from src.kortana.config import get_settings

settings = get_settings()

# Redis URL for broker and result backend
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
app = Celery(
    "kortana",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"],  # Import tasks module
)

# Configure Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,  # Results expire after 1 hour
)

# Optional: Configure task routes
app.conf.task_routes = {
    "tasks.process_chat": {"queue": "chat"},
    "tasks.analyze_image": {"queue": "analysis"},
    "tasks.run_autonomy_cycle": {"queue": "autonomy"},
    "tasks.execute_hop_task": {"queue": "hop"},
    "tasks.run_github_autonomy_cycle": {"queue": "autonomy"},
}

# Celery Beat Schedule
app.conf.beat_schedule = {
    "github-autonomy-every-10-minutes": {
        "task": "tasks.run_github_autonomy_cycle",
        "schedule": 600.0,  # 10 minutes
    },
    "hop-cycle-every-hour": {
        "task": "tasks.run_autonomy_cycle",
        "schedule": crontab(minute=0),  # Every hour at top of hour
    },
}

if __name__ == "__main__":
    app.start()
