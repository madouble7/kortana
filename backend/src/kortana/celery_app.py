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
}

# Celery Beat Schedule - Autonomous self-sustaining cycles
app.conf.beat_schedule = {
    # Phase 5: Autonomous Systems Self-Triggering
    "always-on-monitor-every-5-minutes": {
        "task": "src.kortana.tasks.run_always_on_monitor",
        "schedule": 300.0,  # Every 5 minutes
    },
    "autonomous-review-every-10-minutes": {
        "task": "src.kortana.tasks.trigger_autonomous_review_cycle",
        "schedule": 600.0,  # Every 10 minutes
    },
    "autonomous-agent-every-15-minutes": {
        "task": "src.kortana.tasks.trigger_autonomous_agent_cycle",
        "schedule": 900.0,  # Every 15 minutes
    },
    "master-autonomy-loop-every-20-minutes": {
        "task": "src.kortana.tasks.autonomous_self_improvement_loop",
        "schedule": 1200.0,  # Every 20 minutes - master self-improvement cycle
    },
}

if __name__ == "__main__":
    app.start()
