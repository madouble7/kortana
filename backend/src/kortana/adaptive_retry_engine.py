"""
KOR'TANA Adaptive Retry Strategy Engine

Intelligent retry logic that adapts based on error type:
- Network errors: Exponential backoff (2^n)
- Rate limits: Defer to quota reset time
- Transient errors: Immediate retry with jitter
- Permanent errors: One-time retry only
- Cascade failures: All-or-nothing with circuit breaker
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from src.kortana.logger import get_logger

logger = get_logger(__name__)


class ErrorCategory(Enum):
    """Categorization of errors for retry strategy"""

    TRANSIENT = "transient"  # Temporary, safe to immediately retry
    NETWORK = "network"  # Connection/timeout, use exponential backoff
    RATE_LIMIT = "rate_limit"  # API quota, wait for reset
    AUTHENTICATION = "auth"  # Token/credentials invalid, don't retry
    LOGIC_ERROR = "logic"  # Bug in code, manual intervention needed
    DEPRECATED = "deprecated"  # API endpoint no longer available
    CONCURRENT = "concurrent"  # Race condition, can retry
    RESOURCE = "resource"  # Disk/memory full, exponential backoff
    UNKNOWN = "unknown"  # Unknown error, conservative retry


@dataclass
class RetryPolicy:
    """Policy governing retry behavior for specific error type"""

    error_category: ErrorCategory
    max_retries: int = 3
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 300.0
    backoff_multiplier: float = 2.0
    jitter_enabled: bool = True
    jitter_range: float = 0.1  # ±10% of delay
    retry_on_timeout: bool = True

    def calculate_delay(self, retry_attempt: int) -> float:
        """Calculate delay for given retry attempt"""
        if self.error_category == ErrorCategory.RATE_LIMIT:
            # Rate limits should wait for quota reset
            return self.max_delay_seconds

        if self.error_category == ErrorCategory.TRANSIENT:
            # Transient errors retry immediately with small jitter
            base_delay = self.initial_delay_seconds
        else:
            # Network/resource errors use exponential backoff
            base_delay = self.initial_delay_seconds * (
                self.backoff_multiplier**retry_attempt
            )

        # Cap at maximum
        base_delay = min(base_delay, self.max_delay_seconds)

        # Apply jitter
        if self.jitter_enabled:
            jitter_amount = base_delay * self.jitter_range
            base_delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0.1, base_delay)  # Minimum 100ms

    def should_retry(self, attempt_number: int) -> bool:
        """Check if should retry based on attempt number"""
        return attempt_number < self.max_retries


class AdaptiveRetryEngine:
    """
    Intelligently retries failed operations with category-specific strategies.
    """

    # Define standard retry policies for each error category
    POLICIES: dict[ErrorCategory, RetryPolicy] = {
        ErrorCategory.TRANSIENT: RetryPolicy(
            error_category=ErrorCategory.TRANSIENT,
            max_retries=5,
            initial_delay_seconds=0.1,
            max_delay_seconds=10.0,
            backoff_multiplier=1.5,
            jitter_enabled=True,
        ),
        ErrorCategory.NETWORK: RetryPolicy(
            error_category=ErrorCategory.NETWORK,
            max_retries=4,
            initial_delay_seconds=1.0,
            max_delay_seconds=60.0,
            backoff_multiplier=2.0,
            jitter_enabled=True,
        ),
        ErrorCategory.RATE_LIMIT: RetryPolicy(
            error_category=ErrorCategory.RATE_LIMIT,
            max_retries=2,
            initial_delay_seconds=60.0,
            max_delay_seconds=3600.0,
            backoff_multiplier=1.0,  # Don't multiply for rate limits
            jitter_enabled=False,
        ),
        ErrorCategory.CONCURRENT: RetryPolicy(
            error_category=ErrorCategory.CONCURRENT,
            max_retries=3,
            initial_delay_seconds=0.05,
            max_delay_seconds=5.0,
            backoff_multiplier=2.0,
            jitter_enabled=True,
        ),
        ErrorCategory.RESOURCE: RetryPolicy(
            error_category=ErrorCategory.RESOURCE,
            max_retries=3,
            initial_delay_seconds=5.0,
            max_delay_seconds=300.0,
            backoff_multiplier=3.0,
            jitter_enabled=True,
        ),
        ErrorCategory.AUTHENTICATION: RetryPolicy(
            error_category=ErrorCategory.AUTHENTICATION,
            max_retries=0,  # No automatic retry
            retry_on_timeout=False,
        ),
        ErrorCategory.LOGIC_ERROR: RetryPolicy(
            error_category=ErrorCategory.LOGIC_ERROR,
            max_retries=1,  # One human-supervised retry
            retry_on_timeout=False,
        ),
        ErrorCategory.DEPRECATED: RetryPolicy(
            error_category=ErrorCategory.DEPRECATED,
            max_retries=0,
            retry_on_timeout=False,
        ),
        ErrorCategory.UNKNOWN: RetryPolicy(
            error_category=ErrorCategory.UNKNOWN,
            max_retries=2,
            initial_delay_seconds=2.0,
            max_delay_seconds=30.0,
            backoff_multiplier=2.0,
            jitter_enabled=True,
        ),
    }

    def __init__(self):
        self.retry_history: list[dict] = []

    def categorize_error(
        self, exception: Exception, status_code: Optional[int] = None
    ) -> ErrorCategory:
        """Determine error category from exception type and status code"""
        error_msg = str(exception).lower()

        # HTTP status code-based categorization
        if status_code:
            if status_code == 429:
                return ErrorCategory.RATE_LIMIT
            elif status_code in (401, 403):
                return ErrorCategory.AUTHENTICATION
            elif status_code in (410, 404):
                return ErrorCategory.DEPRECATED
            elif status_code >= 500:
                return ErrorCategory.TRANSIENT
            elif status_code in (408, 504):
                return ErrorCategory.NETWORK

        # Exception type-based categorization
        if "timeout" in error_msg or "timed out" in error_msg:
            return ErrorCategory.NETWORK
        elif "connection" in error_msg or "refused" in error_msg:
            return ErrorCategory.NETWORK
        elif "quota" in error_msg or "rate" in error_msg:
            return ErrorCategory.RATE_LIMIT
        elif "token" in error_msg or "unauthorized" in error_msg:
            return ErrorCategory.AUTHENTICATION
        elif "permission" in error_msg or "forbidden" in error_msg:
            return ErrorCategory.AUTHENTICATION
        elif "disk" in error_msg or "memory" in error_msg or "space" in error_msg:
            return ErrorCategory.RESOURCE
        elif "race" in error_msg or "concurrent" in error_msg:
            return ErrorCategory.CONCURRENT
        elif "assertion" in error_msg or "logic" in error_msg:
            return ErrorCategory.LOGIC_ERROR
        else:
            return ErrorCategory.UNKNOWN

    def should_retry(
        self,
        exception: Exception,
        attempt_number: int,
        status_code: Optional[int] = None,
    ) -> bool:
        """Determine if operation should be retried"""
        category = self.categorize_error(exception, status_code)
        policy = self.POLICIES.get(category, self.POLICIES[ErrorCategory.UNKNOWN])

        should = policy.should_retry(attempt_number)

        logger.info(
            f"Retry decision for {exception.__class__.__name__}: "
            f"category={category.value}, attempt={attempt_number}, "
            f"should_retry={should}"
        )

        return should

    def get_retry_delay(
        self,
        exception: Exception,
        attempt_number: int,
        status_code: Optional[int] = None,
        quota_reset_time: Optional[datetime] = None,
    ) -> float:
        """Calculate delay before retry"""
        category = self.categorize_error(exception, status_code)
        policy = self.POLICIES.get(category, self.POLICIES[ErrorCategory.UNKNOWN])

        # Special handling for rate limits with known reset time
        if category == ErrorCategory.RATE_LIMIT and quota_reset_time:
            now = datetime.utcnow()
            if quota_reset_time > now:
                delay = (quota_reset_time - now).total_seconds()
                logger.info(f"Rate limited. Waiting until quota reset: {delay:.0f}s")
                return delay

        delay = policy.calculate_delay(attempt_number)
        logger.info(
            f"Retry {exception.__class__.__name__} in {delay:.1f}s "
            f"(attempt {attempt_number + 1}/{policy.max_retries})"
        )

        return delay

    def record_retry(
        self,
        operation_id: str,
        exception: Exception,
        attempt_number: int,
        will_retry: bool,
    ) -> None:
        """Record retry attempt for analytics"""
        category = self.categorize_error(exception)
        self.retry_history.append(
            {
                "operation_id": operation_id,
                "error_category": category.value,
                "error_type": exception.__class__.__name__,
                "attempt": attempt_number,
                "will_retry": will_retry,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def get_retry_stats(self) -> dict:
        """Get statistics about retry patterns"""
        if not self.retry_history:
            return {"total_retries": 0, "categories": {}}

        total = len(self.retry_history)
        by_category: dict[str, int] = {}
        for entry in self.retry_history:
            cat = entry["error_category"]
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total_retries": total,
            "by_category": by_category,
            "success_rate": sum(1 for e in self.retry_history if e["will_retry"])
            / total
            if total > 0
            else 0,
        }
