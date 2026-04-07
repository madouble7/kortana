"""
Enhanced Celery Configuration with Circuit Breaker Integration
Health-aware Beat scheduler that prevents cascading task failures
"""

import os

from celery import Celery
from celery.beat import Scheduler
from src.kortana.logger import get_logger

logger = get_logger(__name__)


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


class HealthAwareScheduler(Scheduler):
    """
    Custom Scheduler that respects circuit breaker state
    Skips cycles if circuit breaker is open (preventing cascade failures)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._circuit_breaker = None
        self._task_lock_manager = None
        self._health_check_cache = {}
        self._last_health_check = 0
        self._health_check_interval = 10  # seconds

    def _get_circuit_breaker(self):
        """Lazy load circuit breaker"""
        if self._circuit_breaker is None:
            try:
                from src.kortana.circuit_breaker import create_circuit_breaker

                self._circuit_breaker = create_circuit_breaker(REDIS_URL)
            except Exception as e:
                logger.warning(f"Failed to initialize circuit breaker: {e}")
        return self._circuit_breaker

    def _get_task_lock_manager(self):
        """Lazy load task lock manager"""
        if self._task_lock_manager is None:
            try:
                from src.kortana.distributed_lock import create_task_lock_manager

                self._task_lock_manager = create_task_lock_manager(REDIS_URL)
            except Exception as e:
                logger.warning(f"Failed to initialize lock manager: {e}")
        return self._task_lock_manager

    def is_due(self, entry):
        """Override is_due to check circuit breaker"""
        # Get base is_due result
        is_due, next_run_seconds = entry.is_due()

        if not is_due:
            return is_due, next_run_seconds

        task_name = entry.task

        # Check circuit breaker if available
        cb = self._get_circuit_breaker()
        if cb:
            can_execute, reason = cb.can_execute(task_name)
            if not can_execute:
                logger.warning(f"Task {task_name} skipped: circuit breaker {reason}")
                # Not due now, check again in 60 seconds
                return False, 60

        # Check distributed lock if available
        lock_mgr = self._get_task_lock_manager()
        if lock_mgr:
            if lock_mgr.is_locked(task_name):
                logger.debug(f"Task {task_name} skipped: already running on another instance")
                # Not due now, check again in 30 seconds
                return False, 30

        return is_due, next_run_seconds

    def apply_async(self, entry, producer=None, advance=True, **kwargs):
        """Override apply_async to record execution"""
        task_name = entry.task

        # Attempt to acquire lock
        lock_mgr = self._get_task_lock_manager()
        if lock_mgr:
            if not lock_mgr.acquire_for_task(task_name, blocking=False):
                logger.warning(f"Could not acquire lock for {task_name}, skipping execution")
                return

        try:
            # Apply the task
            result = super().apply_async(entry, producer=producer, advance=advance, **kwargs)

            # Record success in circuit breaker
            cb = self._get_circuit_breaker()
            if cb:
                cb.record_success(task_name)
                logger.debug(f"Task {task_name} scheduled successfully")

            return result

        except Exception as e:
            logger.error(f"Task {task_name} scheduling failed: {e}")

            # Record failure in circuit breaker
            cb = self._get_circuit_breaker()
            if cb:
                cb.record_failure(task_name, str(e))

            raise

        finally:
            # Release lock
            if lock_mgr:
                lock_mgr.release_for_task(task_name)


# Celery Beat Schedule - Autonomous self-sustaining cycles
app.conf.beat_schedule = {
    # Phase 5: Autonomous Systems Self-Triggering
    "always-on-monitor-every-5-minutes": {
        "task": "src.kortana.tasks.run_always_on_monitor",
        "schedule": 300.0,  # Every 5 minutes
        "options": {
            "queue": "autonomy",
            "time_limit": 240,  # 4 minutes max
        },
    },
    "autonomous-review-every-10-minutes": {
        "task": "src.kortana.tasks.trigger_autonomous_review_cycle",
        "schedule": 600.0,  # Every 10 minutes
        "options": {
            "queue": "autonomy",
            "time_limit": 480,  # 8 minutes max
        },
    },
    "autonomous-agent-every-15-minutes": {
        "task": "src.kortana.tasks.trigger_autonomous_agent_cycle",
        "schedule": 900.0,  # Every 15 minutes
        "options": {
            "queue": "autonomy",
            "time_limit": 600,  # 10 minutes max
        },
    },
    "master-autonomy-loop-every-20-minutes": {
        "task": "src.kortana.tasks.autonomous_self_improvement_loop",
        "schedule": 1200.0,  # Every 20 minutes
        "options": {
            "queue": "autonomy",
            "time_limit": 900,  # 15 minutes max
        },
    },
    "autonomous-system-monitor-every-30-minutes": {
        "task": "src.kortana.tasks.autonomous_system_monitor_task",
        "schedule": 1800.0,  # Every 30 minutes
        "options": {
            "queue": "autonomy",
            "time_limit": 1200,  # 20 minutes max
        },
    },
    # OPTIMIZATION: New health-monitoring cycle
    "health-check-every-2-minutes": {
        "task": "src.kortana.tasks.health_check_cycle",
        "schedule": 120.0,  # Every 2 minutes
        "options": {
            "queue": "autonomy",
            "time_limit": 60,  # 1 minute max
        },
    },
}

# Use custom scheduler if available
BEAT_SCHEDULER = os.getenv("CELERY_BEAT_SCHEDULER", "celery.beat.PersistentScheduler")
if BEAT_SCHEDULER == "health_aware":
    app.conf.beat_scheduler = HealthAwareScheduler


if __name__ == "__main__":
    app.start()
