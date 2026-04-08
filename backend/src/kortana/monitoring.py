"""
Monitoring, Observability, and Health Check System
Prometheus metrics, structured logging, health checks, and error recovery
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel

from src.kortana.config import get_settings
from src.kortana.logger import log_error, log_request

settings = get_settings()

# ============================================================================
# Metrics Definitions
# ============================================================================

# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# LLM metrics
llm_requests_total = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["provider", "model", "status"],
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM request latency",
    ["provider", "model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)

llm_tokens_used = Counter(
    "llm_tokens_used",
    "LLM tokens consumed",
    ["provider", "model"],
)

# Task metrics
task_duration_seconds = Histogram(
    "task_duration_seconds",
    "Task execution duration",
    ["task_name", "status"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0),
)

task_total = Counter(
    "task_total",
    "Total tasks processed",
    ["task_name", "status"],
)

# Database metrics
db_connection_pool_size = Gauge(
    "db_connection_pool_size",
    "Database connection pool size",
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query latency",
    ["query_type"],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0),
)

# Cache metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Cache hits",
    ["cache_type"],
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Cache misses",
    ["cache_type"],
)

# Error metrics
errors_total = Counter(
    "errors_total",
    "Total errors",
    ["error_type", "severity"],
)

# GitHub metrics
github_api_calls_total = Counter(
    "github_api_calls_total",
    "Total GitHub API calls",
    ["endpoint", "status"],
)

github_issues_processed = Counter(
    "github_issues_processed",
    "GitHub issues processed",
    ["status"],
)

# System metrics
active_tasks = Gauge(
    "active_tasks",
    "Number of active tasks",
)

active_connections = Gauge(
    "active_connections",
    "Number of active connections",
)


class HealthStatus(BaseModel):
    """Health check response"""

    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    checks: dict[str, bool]
    details: dict[str, str]


class MetricsCollector:
    """Central metrics collection and recording"""

    @staticmethod
    def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).inc()
        http_request_duration_seconds.labels(
            method=method, endpoint=endpoint
        ).observe(duration)

    @staticmethod
    def record_llm_request(
        provider: str,
        model: str,
        status: str,
        duration: float,
        tokens_used: Optional[int] = None,
    ):
        """Record LLM API call metrics"""
        llm_requests_total.labels(provider=provider, model=model, status=status).inc()
        llm_request_duration_seconds.labels(provider=provider, model=model).observe(
            duration
        )
        if tokens_used:
            llm_tokens_used.labels(provider=provider, model=model).inc(tokens_used)

    @staticmethod
    def record_task(task_name: str, duration: float, status: str):
        """Record task execution metrics"""
        task_total.labels(task_name=task_name, status=status).inc()
        task_duration_seconds.labels(task_name=task_name, status=status).observe(
            duration
        )

    @staticmethod
    def record_db_query(query_type: str, duration: float):
        """Record database query metrics"""
        db_query_duration_seconds.labels(query_type=query_type).observe(duration)

    @staticmethod
    def record_cache_hit(cache_type: str):
        """Record cache hit"""
        cache_hits_total.labels(cache_type=cache_type).inc()

    @staticmethod
    def record_cache_miss(cache_type: str):
        """Record cache miss"""
        cache_misses_total.labels(cache_type=cache_type).inc()

    @staticmethod
    def record_error(error_type: str, severity: str):
        """Record error"""
        errors_total.labels(error_type=error_type, severity=severity).inc()

    @staticmethod
    def record_github_api_call(endpoint: str, status: str):
        """Record GitHub API call"""
        github_api_calls_total.labels(endpoint=endpoint, status=status).inc()

    @staticmethod
    def record_issue_processed(status: str):
        """Record processed GitHub issue"""
        github_issues_processed.labels(status=status).inc()

    @staticmethod
    def set_active_tasks(count: int):
        """Set number of active tasks"""
        active_tasks.set(count)

    @staticmethod
    def set_active_connections(count: int):
        """Set number of active connections"""
        active_connections.set(count)


class HealthChecker:
    """Comprehensive health check system"""

    @staticmethod
    async def check_database() -> tuple[bool, str]:
        """Check database connectivity"""
        try:
            from src.kortana.database import get_db

            db = next(get_db())
            db.execute("SELECT 1")
            return True, "Connected"
        except Exception as e:
            log_error("health_check", f"Database check failed: {str(e)}")
            return False, str(e)

    @staticmethod
    async def check_redis() -> tuple[bool, str]:
        """Check Redis connectivity"""
        try:
            import redis
            import os

            r = redis.from_url(
                os.getenv("REDIS_URL", "redis://redis:6379/0"), socket_connect_timeout=2
            )
            r.ping()
            return True, "Connected"
        except Exception as e:
            log_error("health_check", f"Redis check failed: {str(e)}")
            return False, str(e)

    @staticmethod
    async def check_llm_models() -> tuple[bool, str]:
        """Check LLM model availability"""
        try:
            from llm_router import get_llm_router

            router = get_llm_router()
            available = router.available_models()
            if available:
                return True, f"{len(available)} models available"
            return False, "No models available"
        except Exception as e:
            log_error("health_check", f"LLM check failed: {str(e)}")
            return False, str(e)

    @staticmethod
    async def check_github_api() -> tuple[bool, str]:
        """Check GitHub API connectivity"""
        try:
            from github_automation import get_github_engine

            engine = get_github_engine()
            if engine.gh:
                # Try a simple API call
                rate_limit = engine.gh.get_user().get_repos().totalCount
                return True, f"Connected (rate limit: {rate_limit})"
            return False, "GitHub client not initialized"
        except Exception as e:
            log_error("health_check", f"GitHub check failed: {str(e)}")
            return False, str(e)

    @staticmethod
    async def check_celery_workers() -> tuple[bool, str]:
        """Check Celery worker availability"""
        try:
            from celery_config import app

            active_tasks = app.control.inspect().active()
            if active_tasks:
                worker_count = len(active_tasks)
                return True, f"{worker_count} workers active"
            return False, "No workers available"
        except Exception as e:
            log_error("health_check", f"Celery check failed: {str(e)}")
            return False, str(e)

    @classmethod
    async def full_health_check(cls) -> HealthStatus:
        """Perform complete system health check"""
        checks = {}
        details = {}

        # Run all checks in parallel
        import asyncio

        results = await asyncio.gather(
            cls.check_database(),
            cls.check_redis(),
            cls.check_llm_models(),
            cls.check_github_api(),
            cls.check_celery_workers(),
            return_exceptions=True,
        )

        check_names = [
            "database",
            "redis",
            "llm_models",
            "github_api",
            "celery_workers",
        ]

        for name, result in zip(check_names, results):
            if isinstance(result, Exception):
                checks[name] = False
                details[name] = str(result)
            else:
                is_healthy, message = result
                checks[name] = is_healthy
                details[name] = message

        # Determine overall status
        if all(checks.values()):
            status = "healthy"
        elif sum(checks.values()) >= len(checks) / 2:
            status = "degraded"
        else:
            status = "unhealthy"

        return HealthStatus(
            status=status,
            timestamp=datetime.utcnow(),
            checks=checks,
            details=details,
        )


@asynccontextmanager
async def time_operation(operation_name: str, record_metric=None):
    """Context manager to time operations and record metrics"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        log_request(
            "timing",
            f"{operation_name} completed",
            details={"duration_ms": int(duration * 1000)},
        )
        if record_metric:
            record_metric(duration)


def get_metrics_data() -> bytes:
    """Get Prometheus metrics in text format"""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Get content type for Prometheus metrics"""
    return CONTENT_TYPE_LATEST
