"""
Circuit Breaker and Resilience Patterns
Prevents cascading failures, implements exponential backoff, and graceful degradation
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

from pydantic import BaseModel

from src.kortana.logger import log_error, log_request

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker"""

    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: int = 60  # Seconds before trying again
    expected_exception: type = Exception
    name: str = "circuit_breaker"


class CircuitBreaker:
    """Circuit breaker pattern implementation"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None

    async def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                log_request(
                    "circuit_breaker",
                    f"{self.config.name} entering HALF_OPEN state",
                )
            else:
                raise RuntimeError(
                    f"Circuit breaker {self.config.name} is OPEN - request rejected"
                )

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= 2:
                    self._close()
            else:
                self.failure_count = 0

            return result

        except self.config.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            if self.state == CircuitState.HALF_OPEN:
                self._open()
                log_error(
                    "circuit_breaker",
                    f"{self.config.name} failed during recovery - opening circuit",
                    details={"error": str(e)},
                )
            elif self.failure_count >= self.config.failure_threshold:
                self._open()
                log_error(
                    "circuit_breaker",
                    f"{self.config.name} reached failure threshold - opening circuit",
                    details={"failures": self.failure_count},
                )

            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return True
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.recovery_timeout

    def _open(self):
        """Open the circuit"""
        self.state = CircuitState.OPEN
        self.opened_at = datetime.utcnow()
        log_request("circuit_breaker", f"{self.config.name} opened", details={"failures": self.failure_count})

    def _close(self):
        """Close the circuit"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        log_request("circuit_breaker", f"{self.config.name} closed")

    def get_state(self) -> dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "name": self.config.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
        }


class RetryConfig(BaseModel):
    """Configuration for retry logic"""

    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True


class RetryWithBackoff:
    """Exponential backoff with jitter"""

    def __init__(self, config: RetryConfig):
        self.config = config

    async def execute(
        self,
        func: Callable[..., Any],
        *args,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        **kwargs
    ) -> Any:
        """Execute function with exponential backoff retry"""

        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                if attempt > 0:
                    log_request(
                        "retry",
                        f"Operation succeeded after {attempt} retries",
                    )
                return result

            except Exception as e:
                last_exception = e

                if attempt < self.config.max_retries:
                    delay = self._calculate_delay(attempt)

                    if on_retry:
                        on_retry(attempt, e)

                    log_request(
                        "retry",
                        f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s",
                        details={"error": str(e), "attempt": attempt + 1},
                    )

                    await asyncio.sleep(delay)
                else:
                    log_error(
                        "retry_exhausted",
                        f"All {self.config.max_retries + 1} attempts failed",
                        details={"last_error": str(e)},
                    )

        raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter"""
        delay = self.config.base_delay * (
            self.config.exponential_base ** attempt
        )
        delay = min(delay, self.config.max_delay)

        if self.config.jitter:
            import random

            jitter = random.uniform(0, delay * 0.1)
            delay += jitter

        return delay


class BulkheadConfig(BaseModel):
    """Configuration for bulkhead pattern"""

    max_concurrent: int = 10
    name: str = "bulkhead"


class Bulkhead:
    """Bulkhead pattern - limit concurrent requests"""

    def __init__(self, config: BulkheadConfig):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        self.active_count = 0

    async def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute function with concurrency limit"""

        async with self.semaphore:
            self.active_count += 1

            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                return result
            finally:
                self.active_count -= 1

    def get_state(self) -> dict[str, Any]:
        """Get bulkhead state"""
        return {
            "name": self.config.name,
            "active": self.active_count,
            "max_concurrent": self.config.max_concurrent,
            "available_slots": self.config.max_concurrent - self.active_count,
        }


class ResilientExecutor:
    """Combines circuit breaker, retry, and bulkhead patterns"""

    def __init__(
        self,
        name: str,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        bulkhead_config: Optional[BulkheadConfig] = None,
    ):
        self.name = name
        self.circuit_breaker = CircuitBreaker(
            circuit_breaker_config or CircuitBreakerConfig(name=name)
        )
        self.retry = RetryWithBackoff(retry_config or RetryConfig())
        self.bulkhead = Bulkhead(
            bulkhead_config or BulkheadConfig(name=name)
        )

    async def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute function with full resilience pattern"""

        async def retry_with_circuit():
            return await self.circuit_breaker.call(
                self.retry.execute, func, *args, **kwargs
            )

        return await self.bulkhead.execute(retry_with_circuit)

    def get_state(self) -> dict[str, Any]:
        """Get executor state"""
        return {
            "name": self.name,
            "circuit_breaker": self.circuit_breaker.get_state(),
            "bulkhead": self.bulkhead.get_state(),
        }


# Predefined resilient executors for common operations
llm_executor = ResilientExecutor(
    "llm_api",
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60,
        name="llm_circuit_breaker",
    ),
    retry_config=RetryConfig(max_retries=3),
    bulkhead_config=BulkheadConfig(max_concurrent=10, name="llm_bulkhead"),
)

github_executor = ResilientExecutor(
    "github_api",
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=120,
        name="github_circuit_breaker",
    ),
    retry_config=RetryConfig(max_retries=3),
    bulkhead_config=BulkheadConfig(max_concurrent=5, name="github_bulkhead"),
)

database_executor = ResilientExecutor(
    "database",
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=10,
        recovery_timeout=30,
        name="database_circuit_breaker",
    ),
    retry_config=RetryConfig(max_retries=3),
    bulkhead_config=BulkheadConfig(max_concurrent=20, name="database_bulkhead"),
)


def get_resilient_executor(operation_type: str) -> ResilientExecutor:
    """Get resilient executor for operation type"""
    executors = {
        "llm": llm_executor,
        "github": github_executor,
        "database": database_executor,
    }
    return executors.get(operation_type, llm_executor)
