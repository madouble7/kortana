"""
Circuit Breaker Pattern for Autonomous Cycles
Prevents cascade failures when Beat scheduler cycles fail repeatedly
Uses Redis for distributed state across multiple workers
"""

import json
import time
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Optional

from redis import Redis
from src.kortana.logger import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation, allowing tasks
    OPEN = "open"  # Failing, blocking tasks
    HALF_OPEN = "half_open"  # Testing if healthy, allowing limited tasks


@dataclass
class CircuitMetrics:
    """Metrics for a circuit breaker"""

    task_name: str
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state: str = CircuitState.CLOSED.value
    opened_at: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CircuitMetrics":
        """Create from dictionary"""
        return cls(**data)


class AutonomyCircuitBreaker:
    """
    Distributed circuit breaker for autonomous cycles
    Monitors Beat scheduler cycles and prevents cascading failures
    """

    def __init__(
        self,
        redis_client: Redis,
        failure_threshold: int = 3,
        recovery_timeout: int = 300,  # 5 minutes
        half_open_max_tasks: int = 1,
    ):
        """
        Initialize circuit breaker

        Args:
            redis_client: Redis connection for distributed state
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            half_open_max_tasks: Max tasks allowed in half-open state
        """
        self.redis = redis_client
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_tasks = half_open_max_tasks
        self.prefix = "hop:cb:"  # Circuit breaker key prefix

    def _get_metrics_key(self, task_name: str) -> str:
        """Get Redis key for task metrics"""
        return f"{self.prefix}metrics:{task_name}"

    def _get_metrics(self, task_name: str) -> CircuitMetrics:
        """Retrieve metrics from Redis"""
        key = self._get_metrics_key(task_name)
        data = self.redis.get(key)
        if data:
            try:
                metrics_dict = json.loads(data)
                return CircuitMetrics.from_dict(metrics_dict)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse metrics for {task_name}")
        return CircuitMetrics(task_name=task_name)

    def _save_metrics(self, metrics: CircuitMetrics) -> None:
        """Save metrics to Redis with TTL"""
        key = self._get_metrics_key(metrics.task_name)
        data = json.dumps(metrics.to_dict())
        # Keep metrics for 24 hours
        self.redis.setex(key, 86400, data)

    def can_execute(self, task_name: str) -> tuple[bool, Optional[str]]:
        """
        Check if task can be executed

        Args:
            task_name: Name of autonomous cycle task

        Returns:
            Tuple of (can_execute, reason)
        """
        metrics = self._get_metrics(task_name)
        state = CircuitState(metrics.state)

        if state == CircuitState.CLOSED:
            return True, None

        if state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if metrics.opened_at is None:
                return False, "Circuit open indefinitely"

            time_since_opened = time.time() - metrics.opened_at
            if time_since_opened > self.recovery_timeout:
                # Try recovery
                logger.info(f"Circuit breaker for {task_name}: attempting recovery")
                metrics.state = CircuitState.HALF_OPEN.value
                metrics.failure_count = 0
                self._save_metrics(metrics)
                return True, "Attempting recovery (half-open)"
            else:
                remaining = self.recovery_timeout - time_since_opened
                return (
                    False,
                    f"Circuit open, will retry in {int(remaining)}s",
                )

        if state == CircuitState.HALF_OPEN:
            # Allow limited tasks to test recovery
            if metrics.success_count >= self.half_open_max_tasks:
                logger.info(f"Circuit breaker for {task_name}: recovered successfully")
                metrics.state = CircuitState.CLOSED.value
                metrics.failure_count = 0
                metrics.success_count = 0
                self._save_metrics(metrics)
                return True, None

            # Allow if haven't exceeded half-open limit
            if metrics.failure_count == 0:
                return True, "Testing recovery (half-open)"
            else:
                return False, "Recovery test failed, reopening circuit"

        return False, f"Unknown circuit state: {state}"

    def record_success(self, task_name: str) -> None:
        """Record successful task execution"""
        metrics = self._get_metrics(task_name)
        metrics.success_count += 1
        metrics.last_success_time = time.time()

        # Transition from half-open to closed on success
        if CircuitState(metrics.state) == CircuitState.HALF_OPEN:
            metrics.state = CircuitState.CLOSED.value
            metrics.failure_count = 0
            logger.info(f"Circuit breaker for {task_name}: closed (healthy)")

        self._save_metrics(metrics)

    def record_failure(self, task_name: str, error: str = "") -> None:
        """Record failed task execution"""
        metrics = self._get_metrics(task_name)
        metrics.failure_count += 1
        metrics.last_failure_time = time.time()

        # Check if threshold exceeded
        if metrics.failure_count >= self.failure_threshold:
            metrics.state = CircuitState.OPEN.value
            metrics.opened_at = time.time()
            logger.error(
                f"Circuit breaker for {task_name}: opened after {metrics.failure_count} failures"
            )
            if error:
                logger.error(f"  Last error: {error}")

        # Half-open failure goes back to open
        elif CircuitState(metrics.state) == CircuitState.HALF_OPEN:
            metrics.state = CircuitState.OPEN.value
            metrics.opened_at = time.time()
            logger.warning(f"Circuit breaker for {task_name}: recovery failed, reopening")

        self._save_metrics(metrics)

    def get_status(self, task_name: str) -> dict[str, Any]:
        """Get current status of circuit breaker"""
        metrics = self._get_metrics(task_name)
        return {
            "task_name": task_name,
            "state": metrics.state,
            "failure_count": metrics.failure_count,
            "success_count": metrics.success_count,
            "last_failure_time": metrics.last_failure_time,
            "last_success_time": metrics.last_success_time,
            "opened_at": metrics.opened_at,
        }

    def get_all_statuses(self) -> list[dict[str, Any]]:
        """Get status of all monitored circuits"""
        statuses = []
        try:
            # Find all circuit metrics keys
            pattern = f"{self.prefix}metrics:*"
            for key in self.redis.scan_iter(match=pattern):
                task_name = key.decode().replace(f"{self.prefix}metrics:", "")
                statuses.append(self.get_status(task_name))
        except Exception as e:
            logger.error(f"Failed to get all circuit statuses: {e}")
        return statuses

    def reset(self, task_name: str) -> None:
        """Reset circuit breaker to closed state"""
        metrics = CircuitMetrics(task_name=task_name, state=CircuitState.CLOSED.value)
        self._save_metrics(metrics)
        logger.info(f"Circuit breaker for {task_name}: manually reset")


def create_circuit_breaker(redis_url: str) -> AutonomyCircuitBreaker:
    """Factory function to create circuit breaker with Redis connection"""
    import os

    from redis import Redis

    redis_client = Redis.from_url(redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    return AutonomyCircuitBreaker(redis_client)
