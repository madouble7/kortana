"""
HTTP Client with Connection Pooling and Circuit Breaker Integration
Provides resilient HTTP communication for external API calls
"""

from typing import Any, Dict, Optional

import httpx
from redis import Redis

from src.kortana.circuit_breaker import AutonomyCircuitBreaker
from src.kortana.config import get_settings
from src.kortana.logger import get_logger

logger = get_logger(__name__)


class ResilientHTTPClient:
    """
    HTTP client with connection pooling and circuit breaker protection
    """

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        pool_limits: httpx.Limits = httpx.Limits(
            max_keepalive_connections=20, max_connections=100
        ),
        timeout: httpx.Timeout = httpx.Timeout(30.0),
        circuit_breaker_failure_threshold: int = 5,
        circuit_breaker_recovery_timeout: int = 60,
    ):
        """
        Initialize resilient HTTP client

        Args:
            redis_client: Redis client for circuit breaker state (optional)
            pool_limits: Connection pool limits
            timeout: Default timeout for requests
            circuit_breaker_failure_threshold: Failures before opening circuit
            circuit_breaker_recovery_timeout: Seconds before recovery attempt
        """
        self.pool_limits = pool_limits
        self.timeout = timeout
        self.redis_client = redis_client

        # Circuit breaker for different API endpoints
        self.circuit_breakers: Dict[str, AutonomyCircuitBreaker] = {}

        if redis_client:
            # Create circuit breakers for common APIs
            self._init_circuit_breakers()

    def _init_circuit_breakers(self) -> None:
        """Initialize circuit breakers for common external APIs"""
        if not self.redis_client:
            return

        apis = [
            "github_api",
            "gemini_api",
            "stripe_api",
            "anthropic_api",
            "openai_api",
        ]

        for api in apis:
            self.circuit_breakers[api] = AutonomyCircuitBreaker(
                redis_client=self.redis_client,
                failure_threshold=5,
                recovery_timeout=60,  # 1 minute recovery
                half_open_max_tasks=2,
            )

    def _get_circuit_breaker(self, api_name: str) -> Optional[AutonomyCircuitBreaker]:
        """Get circuit breaker for API, creating if needed"""
        if not self.redis_client:
            return None

        if api_name not in self.circuit_breakers:
            self.circuit_breakers[api_name] = AutonomyCircuitBreaker(
                redis_client=self.redis_client,
                failure_threshold=5,
                recovery_timeout=60,
                half_open_max_tasks=2,
            )

        return self.circuit_breakers[api_name]

    async def request(
        self, method: str, url: str, api_name: str = "external_api", **kwargs: Any
    ) -> httpx.Response:
        """
        Make HTTP request with circuit breaker protection

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            api_name: Name of the API for circuit breaker tracking
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response

        Raises:
            Exception: If circuit is open or request fails
        """
        # Check circuit breaker
        circuit_breaker = self._get_circuit_breaker(api_name)
        if circuit_breaker:
            can_execute, reason = circuit_breaker.can_execute(api_name)
            if not can_execute:
                logger.warning(
                    f"Circuit breaker blocked request to {api_name}: {reason}"
                )
                raise Exception(f"Circuit breaker open: {reason}")

        # Set default timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        try:
            async with httpx.AsyncClient(limits=self.pool_limits) as client:
                response = await client.request(method, url, **kwargs)

                # Don't raise on 422 - allow callers to handle idempotent operations
                # (branch already exists, etc.)
                if response.status_code >= 400 and response.status_code != 422:
                    response.raise_for_status()

                # Record success
                if circuit_breaker:
                    circuit_breaker.record_success(api_name)

                return response

        except Exception as e:
            # Record failure
            if circuit_breaker:
                circuit_breaker.record_failure(api_name, str(e))

            logger.error(f"HTTP request failed for {api_name} ({url}): {str(e)}")
            raise

    async def get(
        self, url: str, api_name: str = "external_api", **kwargs: Any
    ) -> httpx.Response:
        """GET request with circuit breaker protection"""
        return await self.request("GET", url, api_name, **kwargs)

    async def post(
        self, url: str, api_name: str = "external_api", **kwargs: Any
    ) -> httpx.Response:
        """POST request with circuit breaker protection"""
        return await self.request("POST", url, api_name, **kwargs)

    async def put(
        self, url: str, api_name: str = "external_api", **kwargs: Any
    ) -> httpx.Response:
        """PUT request with circuit breaker protection"""
        return await self.request("PUT", url, api_name, **kwargs)

    async def delete(
        self, url: str, api_name: str = "external_api", **kwargs: Any
    ) -> httpx.Response:
        """DELETE request with circuit breaker protection"""
        return await self.request("DELETE", url, api_name, **kwargs)

    def get_circuit_status(self, api_name: str) -> Optional[Dict[str, Any]]:
        """Get circuit breaker status for an API"""
        circuit_breaker = self._get_circuit_breaker(api_name)
        if circuit_breaker:
            return circuit_breaker.get_status(api_name)
        return None

    def get_all_circuit_statuses(self) -> Dict[str, Any]:
        """Get status of all circuit breakers"""
        if not self.redis_client:
            return {"circuit_breakers": "disabled"}

        statuses = {}
        for api_name, circuit_breaker in self.circuit_breakers.items():
            statuses[api_name] = circuit_breaker.get_status(api_name)

        return {"circuit_breakers": statuses}


# Global instance
_http_client: Optional[ResilientHTTPClient] = None


def get_http_client() -> ResilientHTTPClient:
    """Get global HTTP client instance"""
    global _http_client

    if _http_client is None:
        # Try to get Redis client for circuit breaker
        try:
            import redis

            redis_client = redis.Redis.from_url(
                get_settings().INTERNAL_REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            # Test connection
            redis_client.ping()
        except Exception:
            logger.warning("Redis not available, circuit breakers disabled")
            redis_client = None

        _http_client = ResilientHTTPClient(redis_client=redis_client)

    return _http_client


# Convenience functions for backward compatibility
async def resilient_get(
    url: str, api_name: str = "external_api", **kwargs: Any
) -> httpx.Response:
    """Convenience function for GET requests"""
    client = get_http_client()
    return await client.get(url, api_name, **kwargs)


async def resilient_post(
    url: str, api_name: str = "external_api", **kwargs: Any
) -> httpx.Response:
    """Convenience function for POST requests"""
    client = get_http_client()
    return await client.post(url, api_name, **kwargs)
