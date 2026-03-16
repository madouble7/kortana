"""
Prometheus Metrics for Kor'tana Backend

Provides metrics endpoint for Prometheus scraping.
Includes custom business metrics, performance counters, and error tracking.

Author: Kor'tana Team
Date: January 14, 2026
"""

import time
from collections import defaultdict

from fastapi import APIRouter, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
    CollectorRegistry,
)

# Create a custom registry for multiprocess mode
registry = CollectorRegistry()

# ==================== HTTP Request Metrics ====================

# Count of HTTP requests
http_requests_total = Counter(
    "kortana_http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)

# Duration of HTTP requests
http_request_duration_seconds = Histogram(
    "kortana_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
    registry=registry,
)

# Active connections (in-flight requests)
http_requests_in_progress = Gauge(
    "kortana_http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method", "endpoint"],
    registry=registry,
)

# ==================== Business Metrics ====================

# Agent executions counter
agent_executions_total = Counter(
    "kortana_agent_executions_total",
    "Total number of agent executions",
    ["agent_id", "status"],
    registry=registry,
)

# Agent execution duration
agent_execution_duration_seconds = Histogram(
    "kortana_agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_id"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    registry=registry,
)

# API key usage
api_key_requests_total = Counter(
    "kortana_api_key_requests_total",
    "Total number of API key requests",
    ["api_key_id"],
    registry=registry,
)

# Memory operations
memory_operations_total = Counter(
    "kortana_memory_operations_total",
    "Total number of memory operations",
    ["operation", "status"],
    registry=registry,
)

# Task queue operations
task_queue_operations_total = Counter(
    "kortana_task_queue_operations_total",
    "Total number of task queue operations",
    ["operation", "status"],
    registry=registry,
)

# GitHub API calls
github_api_calls_total = Counter(
    "kortana_github_api_calls_total",
    "Total number of GitHub API calls",
    ["endpoint", "status"],
    registry=registry,
)

# LLM provider calls
llm_provider_calls_total = Counter(
    "kortana_llm_provider_calls_total",
    "Total number of LLM provider calls",
    ["provider", "model", "status"],
    registry=registry,
)

# LLM token usage
llm_tokens_used_total = Counter(
    "kortana_llm_tokens_used_total",
    "Total number of LLM tokens used",
    ["provider", "model", "token_type"],
    registry=registry,
)

# ==================== System Metrics ====================

# Database connection pool
db_connections_active = Gauge(
    "kortana_db_connections_active",
    "Number of active database connections",
    registry=registry,
)

db_connections_idle = Gauge(
    "kortana_db_connections_idle",
    "Number of idle database connections",
    registry=registry,
)

# Redis connection status
redis_connections_active = Gauge(
    "kortana_redis_connections_active",
    "Number of active Redis connections",
    registry=registry,
)

# Cache hit/miss ratio
cache_hits_total = Counter(
    "kortana_cache_hits_total",
    "Total number of cache hits",
    registry=registry,
)

cache_misses_total = Counter(
    "kortana_cache_misses_total",
    "Total number of cache misses",
    registry=registry,
)

# ==================== Error Metrics ====================

# Error counter by type
errors_total = Counter(
    "kortana_errors_total",
    "Total number of errors",
    ["error_type", "endpoint"],
    registry=registry,
)

# Authentication failures
auth_failures_total = Counter(
    "kortana_auth_failures_total",
    "Total number of authentication failures",
    ["reason"],
    registry=registry,
)

# Rate limit hits
rate_limit_hits_total = Counter(
    "kortana_rate_limit_hits_total",
    "Total number of rate limit hits",
    ["endpoint", "tier"],
    registry=registry,
)

# ==================== Application Info ====================

app_info = Info(
    "kortana_app",
    "Application information",
    registry=registry,
)

# ==================== APM Tracing Metrics ====================

# Trace spans created
trace_spans_total = Counter(
    "kortana_trace_spans_total",
    "Total number of trace spans created",
    ["service_name", "operation", "status"],
    registry=registry,
)

# Active trace spans
active_trace_spans = Gauge(
    "kortana_active_trace_spans",
    "Number of currently active trace spans",
    ["service_name"],
    registry=registry,
)

# Trace span duration
trace_span_duration_seconds = Histogram(
    "kortana_trace_span_duration_seconds",
    "Trace span duration in seconds",
    ["service_name", "operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry,
)

# ==================== Performance Tracking ====================

# Store start times for in-progress requests
_request_start_times: dict = defaultdict(float)


def track_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record metrics for a completed request"""
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code),
    ).inc()

    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint,
    ).observe(duration)


def track_agent_execution(agent_id: str, status: str, duration: float):
    """Record metrics for an agent execution"""
    agent_executions_total.labels(agent_id=agent_id, status=status).inc()

    agent_execution_duration_seconds.labels(agent_id=agent_id).observe(duration)


def track_llm_call(provider: str, model: str, status: str, tokens: int = 0):
    """Record metrics for an LLM call"""
    llm_provider_calls_total.labels(
        provider=provider,
        model=model,
        status=status,
    ).inc()

    if tokens > 0:
        llm_tokens_used_total.labels(
            provider=provider,
            model=model,
            token_type="total",
        ).inc(tokens)


def track_cache_hit(hit: bool):
    """Record cache hit or miss"""
    if hit:
        cache_hits_total.inc()
    else:
        cache_misses_total.inc()


def track_error(error_type: str, endpoint: str):
    """Record an error occurrence"""
    errors_total.labels(error_type=error_type, endpoint=endpoint).inc()


def track_auth_failure(reason: str):
    """Record an authentication failure"""
    auth_failures_total.labels(reason=reason).inc()


def track_rate_limit_hit(endpoint: str, tier: str):
    """Record a rate limit hit"""
    rate_limit_hits_total.labels(endpoint=endpoint, tier=tier).inc()


def track_trace_span(service_name: str, operation: str, status: str, duration: float):
    """Record metrics for a trace span"""
    trace_spans_total.labels(service_name=service_name, operation=operation, status=status).inc()
    trace_span_duration_seconds.labels(service_name=service_name, operation=operation).observe(duration)


def track_active_trace_span(service_name: str, delta: int = 1):
    """Update active trace span count"""
    active_trace_spans.labels(service_name=service_name).inc(delta)


# ==================== Metrics Endpoint ====================

router = APIRouter(prefix="/metrics", tags=["monitoring"])


@router.get("", response_class=Response)
async def metrics() -> Response:
    """
    Prometheus metrics endpoint

    Returns all metrics in Prometheus format for scraping.
    """
    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST,
    )


@router.get("/health")
async def metrics_health():
    """Health check for metrics endpoint"""
    return {"status": "healthy", "registry": "active"}


# ==================== Application Info Helper ====================

def set_app_info(version: str = "0.1.0", environment: str = "development"):
    """Set application info metrics"""
    app_info.info({
        "version": version,
        "environment": environment,
        "python_version": "3.11+",
    })


# ==================== Middleware Integration ====================

async def metrics_middleware(request, call_next):
    """Middleware to track request metrics"""
    method = request.method
    endpoint = request.url.path

    # Track in-progress
    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

    start_time = time.time()

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        track_error(error_type=type(e).__name__, endpoint=endpoint)
        raise
    finally:
        duration = time.time() - start_time
        track_request(method, endpoint, status_code or 500, duration)
        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

    return response


# ==================== Export ====================

__all__ = [
    "registry",
    "router",
    "track_request",
    "track_agent_execution",
    "track_llm_call",
    "track_cache_hit",
    "track_error",
    "track_auth_failure",
    "track_rate_limit_hit",
    "track_trace_span",
    "track_active_trace_span",
    "set_app_info",
    "metrics_middleware",
]
