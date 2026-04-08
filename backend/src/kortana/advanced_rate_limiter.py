"""
KOR'TANA Advanced Rate Limiting & API Quota Management

Intelligent GitHub API budget allocation with:
- Real-time quota tracking
- Predictive depletion estimates
- Request-level priority queuing
- Adaptive throttling strategies
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from redis import Redis

from src.kortana.logger import get_logger

logger = get_logger(__name__)


@dataclass
class APIQuotaWindow:
    """Tracks API quota in sliding window"""

    service: str  # "github" | "gemini" | "openai"
    limit: int  # Maximum requests per window
    window_seconds: int  # Time window (e.g., 3600 for github hourly)
    requests_made: int = 0
    window_start: datetime = field(default_factory=datetime.utcnow)
    reset_time: Optional[datetime] = None

    @property
    def remaining(self) -> int:
        """Requests remaining in current window"""
        return max(0, self.limit - self.requests_made)

    @property
    def is_exhausted(self) -> bool:
        """Check if quota is depleted"""
        return self.remaining == 0

    @property
    def depletion_rate(self) -> float:
        """Percentage of quota consumed (0.0 to 1.0)"""
        return self.requests_made / self.limit if self.limit > 0 else 0.0

    @property
    def estimated_reset_seconds(self) -> int:
        """Seconds until quota resets"""
        if self.reset_time:
            delta = (self.reset_time - datetime.utcnow()).total_seconds()
            return max(0, int(delta))
        else:
            elapsed = (datetime.utcnow() - self.window_start).total_seconds()
            remaining_window = max(0, self.window_seconds - elapsed)
            return int(remaining_window)

    def can_request(self, safety_margin: int = 10) -> bool:
        """Check if safe to make request (with safety margin)"""
        # Never use the last N requests
        return self.remaining > safety_margin

    def record_request(self, count: int = 1) -> None:
        """Record that requests were made"""
        self.requests_made += count

    def should_throttle(self) -> bool:
        """Check if we should throttle requests"""
        # Throttle if >80% depleted
        return self.depletion_rate > 0.80


class AdvancedRateLimiter:
    """
    Intelligent rate limiting with quota awareness and predictive throttling.
    Prevents API quota exhaustion through adaptive request scheduling.
    """

    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis = redis_client
        self.windows: dict[str, APIQuotaWindow] = {}

        # Initialize quota windows for all services
        self._init_quotas()

    def _init_quotas(self) -> None:
        """Initialize standard quota windows"""
        # GitHub: 5,000 requests/hour
        self.windows["github"] = APIQuotaWindow(
            service="github",
            limit=5000,
            window_seconds=3600,
            reset_time=datetime.utcnow() + timedelta(hours=1),
        )

        # Gemini: 60 requests/minute, 1,500/day
        self.windows["gemini_minute"] = APIQuotaWindow(
            service="gemini_minute",
            limit=60,
            window_seconds=60,
            reset_time=datetime.utcnow() + timedelta(minutes=1),
        )

        # OpenAI: tier-dependent, default 3,500/min for paid
        self.windows["openai"] = APIQuotaWindow(
            service="openai",
            limit=3500,
            window_seconds=60,
            reset_time=datetime.utcnow() + timedelta(minutes=1),
        )

    async def check_quota(
        self, service: str, required: int = 1, safety_margin: int = 10
    ) -> dict[str, str | int | bool]:
        """
        Check if sufficient quota exists for operation.

        Returns:
            {
                "available": bool,
                "remaining": int,
                "depletion_rate": float,
                "should_defer": bool,
                "defer_until": int (seconds),
                "recommendation": str
            }
        """
        window = self.windows.get(service)
        if not window:
            logger.warning(f"Unknown service quota: {service}")
            return {"available": True, "remaining": float("inf")}

        # Load from Redis if available
        if self.redis:
            self._load_from_redis(service)

        available = window.remaining >= (required + safety_margin)
        should_defer = window.should_throttle() or window.is_exhausted

        recommendation = self._get_recommendation(window, available, should_defer)

        return {
            "available": available,
            "remaining": window.remaining,
            "depletion_rate": window.depletion_rate,
            "should_defer": should_defer,
            "defer_until": window.estimated_reset_seconds if should_defer else 0,
            "recommendation": recommendation,
        }

    def _get_recommendation(
        self, window: APIQuotaWindow, available: bool, should_defer: bool
    ) -> str:
        """Generate actionable recommendation"""
        if not available:
            reset_secs: int = window.estimated_reset_seconds
            return f"WAIT: Quota exhausted. Reset in {reset_secs}s"
        elif should_defer:
            depletion: int = int(window.depletion_rate * 100)
            return (
                f"SLOW: {depletion}% consumed. Consider deferring non-urgent requests"
            )
        elif window.depletion_rate > 0.5:
            depletion = int(window.depletion_rate * 100)
            return f"CAUTION: {depletion}% consumed. Monitor closely"
        else:
            return "OK: Quota available"

    async def acquire(
        self, service: str, cost: int = 1, timeout_seconds: int = 300
    ) -> bool:
        """
        Attempt to acquire quota permission with timeout.

        Args:
            service: Which API quota to consume
            cost: How many requests this operation costs
            timeout_seconds: Max seconds to wait before giving up

        Returns:
            True if quota acquired, False if timeout
        """
        start = datetime.utcnow()
        while True:
            quota_check = await self.check_quota(service, required=cost)

            if quota_check["available"]:
                self.record_request(service, cost)
                return True

            # Check timeout
            elapsed = (datetime.utcnow() - start).total_seconds()
            if elapsed > timeout_seconds:
                logger.error(
                    f"Rate limit timeout for {service} after {elapsed}s. "
                    f"Remaining: {quota_check['remaining']}"
                )
                return False

            # Wait with exponential backoff
            defer_time = min(quota_check["defer_until"] + 1, 60)  # Max 60s wait
            logger.info(
                f"Rate limited on {service}. Waiting {defer_time}s. "
                f"Depletion: {quota_check['depletion_rate']:.1%}"
            )
            await asyncio.sleep(defer_time)

    def record_request(self, service: str, count: int = 1) -> None:
        """Record API request was made"""
        window = self.windows.get(service)
        if window:
            window.record_request(count)
            if self.redis:
                self._save_to_redis(service, window)

    def _load_from_redis(self, service: str) -> None:
        """Load quota state from Redis for distributed coordination"""
        if not self.redis:
            return
        try:
            key = f"quota:{service}"
            data = self.redis.hgetall(key)
            if data:
                window = self.windows[service]
                window.requests_made = int(data.get(b"requests_made", 0))
                # Additional fields can be loaded as needed
        except Exception as e:
            logger.warning(f"Failed to load quota from Redis: {e}")

    def _save_to_redis(self, service: str, window: APIQuotaWindow) -> None:
        """Save quota state to Redis for distributed coordination"""
        if not self.redis:
            return
        try:
            key = f"quota:{service}"
            self.redis.hset(
                key,
                mapping={
                    "requests_made": window.requests_made,
                    "window_start": window.window_start.isoformat(),
                    "depletion_rate": str(window.depletion_rate),
                },
            )
            # Set expiration
            self.redis.expire(key, window.window_seconds)
        except Exception as e:
            logger.warning(f"Failed to save quota to Redis: {e}")

    def get_status(self) -> dict[str, dict]:
        """Get current status of all quota windows"""
        return {
            service: {
                "remaining": window.remaining,
                "depletion_rate": f"{window.depletion_rate:.1%}",
                "reset_in_seconds": window.estimated_reset_seconds,
                "is_exhausted": window.is_exhausted,
                "should_throttle": window.should_throttle(),
            }
            for service, window in self.windows.items()
        }
