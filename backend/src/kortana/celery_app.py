"""
Celery Application Configuration for Kor'tana
Background task processing using Redis as broker
"""

import os

from celery import Celery

from src.kortana.config import get_settings

settings = get_settings()

# Redis URL for broker and result backend
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
app = Celery(
    "kortana",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.kortana.tasks"],  # Import tasks module
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
    "src.kortana.tasks.process_chat": {"queue": "chat"},
    "src.kortana.tasks.analyze_image": {"queue": "analysis"},
    "src.kortana.tasks.run_autonomy_cycle": {"queue": "autonomy"},
    "src.kortana.tasks.execute_hop_task": {"queue": "hop"},
    "src.kortana.tasks.run_github_autonomy_cycle": {"queue": "autonomy"},
    "src.kortana.tasks.create_pr_for_task": {"queue": "autonomy"},
    "src.kortana.tasks.review_code": {"queue": "autonomy"},
    "src.kortana.tasks.execute_agent": {"queue": "autonomy"},
}

# Celery Beat Schedule - Streamlined Autonomous Cycles
# Reduced from 5 excessive cycles to 2 essential cycles for better performance
app.conf.beat_schedule = {
    # Essential autonomous cycles only
    "always-on-monitor-every-5-minutes": {
        "task": "src.kortana.tasks.run_always_on_monitor",
        "schedule": 300.0,  # Every 5 minutes - monitor for issues
    },
    "github-autonomy-every-10-minutes": {
        "task": "src.kortana.tasks.run_github_autonomy_cycle",
        "schedule": 600.0,  # Every 10 minutes - manage code repository
    },
    "hop-cycle-every-hour": {
        "task": "src.kortana.tasks.run_autonomy_cycle",
        "schedule": 3600.0,  # Every hour - evaluate Human Only Protocol tasks
    },
    "autonomous-system-monitor-every-30-minutes": {
        "task": "src.kortana.tasks.autonomous_system_monitor_task",
        "schedule": 1800.0,  # Every 30 minutes - self-awareness and optimization
    },
}

if __name__ == "__main__":
    app.start()
