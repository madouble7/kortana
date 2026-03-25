"""
Kor'tana Backend - FastAPI Application
Multimodal AI constellation API with autonomous capabilities
"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add backend directory to path FIRST (before any local imports)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration and utilities
from config import get_settings
from exceptions import KortanaException
from logger import log_error, log_request, setup_logging

# Middleware
from middleware.security import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)

# Optimization modules (optional - graceful degradation)
OPTIMIZATION_AVAILABLE = False
optimization_router = None
try:
    from src.kortana.celery_app_enhanced import HealthAwareScheduler  # noqa: F401
    from src.kortana.circuit_breaker import AutonomyCircuitBreaker  # noqa: F401
    from src.kortana.distributed_lock import DistributedLock  # noqa: F401
    from src.kortana.middleware.cache import CacheStrategy, ResponseCacheMiddleware
    from src.kortana.routers.optimization import router as optimization_router
    from src.kortana.workflow_executor import WorkflowExecutor  # noqa: F401

    OPTIMIZATION_AVAILABLE = True
except ImportError as e:
    log_error("optimization", f"Could not import optimization modules: {e}")

# Intelligence systems (optional - graceful degradation)
INTELLIGENCE_AVAILABLE = False
intelligence_router = None
try:
    from src.kortana.routers import intelligence as intelligence_router

    INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    log_error("intelligence", f"Could not import intelligence systems: {e}")

# Live Exerciser (optional - real API + PostgreSQL integration)
LIVE_EXERCISER_AVAILABLE = False
live_exerciser_router = None
try:
    from src.kortana.routers import live_exerciser as live_exerciser_router

    LIVE_EXERCISER_AVAILABLE = True
except ImportError as e:
    log_error("live_exerciser", f"Could not import live exerciser: {e}")

# Import routers
try:
    from routers import (
        agents,
        auth,
        autonomy,
        billing,
        code_reviewer,
        gemini,
        github,
        knowledge,
        memory,
        pr_creation,
        task_queue,
        test_orchestrator,
    )
except ImportError as e:
    log_error("routers", f"Error importing routers: {e}")
    raise

# Import Human Only Protocol (HOP) for autonomy
try:
    from human_only_protocol import router as hop_router

    HOP_AVAILABLE = True
except ImportError as e:
    log_error("hop", f"Could not import Human Only Protocol: {e}")
    HOP_AVAILABLE = False
    hop_router = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events"""
    # Startup
    settings = get_settings()

    # Validate configuration and secrets
    try:
        settings.validate()
        log_request(
            "config",
            f"Secrets validation complete. Environment: {settings.ENVIRONMENT}, API Keys: "
            f"Gemini={bool(settings.GEMINI_API_KEY)}, GitHub={bool(settings.GITHUB_TOKEN)}, "
            f"Discord={bool(settings.DISCORD_BOT_TOKEN)}, OpenAI={bool(settings.OPENAI_API_KEY)}",
        )
    except ValueError as e:
        log_error("config", f"Configuration validation failed: {e}")
        raise

    log_request("system", f"Kor'tana API starting in {settings.ENVIRONMENT} mode")

    yield

    # Shutdown
    log_request("system", "Kor'tana API shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()

    # Initialize logging
    setup_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)

    # Create FastAPI app with configuration
    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=settings.API_DESCRIPTION,
        lifespan=lifespan,
        debug=settings.DEBUG,
    )

    # CORS middleware with configured origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
    )

    # Security middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Probe Redis once at startup to avoid per-request error spam
    _redis_available = False
    try:
        import redis as _redis_mod

        try:
            _redis_url = (
                getattr(settings, "REDIS_URL", None) or "redis://localhost:6379/0"
            )
        except (AttributeError, TypeError):
            _redis_url = "redis://localhost:6379/0"
        _probe = _redis_mod.from_url(_redis_url, socket_connect_timeout=2)
        _probe.ping()
        _probe.close()
        _redis_available = True
    except Exception:
        print("[WARN] Redis not reachable — rate limiting and caching disabled")

    if settings.ENVIRONMENT != "testing" and _redis_available:
        app.add_middleware(
            RateLimitMiddleware, requests_per_minute=100
        )

    # Response caching middleware (optimization)
    if OPTIMIZATION_AVAILABLE and _redis_available:
        try:
            redis_client = _redis_mod.from_url(_redis_url, decode_responses=True)
            cache_strategy = CacheStrategy(
                ttl=300,
                exclude_paths=[
                    "/api/auth",
                    "/api/billing",
                    "/health",
                    "/docs",
                    "/openapi.json",
                ],
            )
            app.add_middleware(
                ResponseCacheMiddleware,
                redis_client=redis_client,
                strategy=cache_strategy,
            )
            log_request("middleware", "Response caching middleware enabled")
        except Exception as e:
            log_error("middleware", f"Response caching middleware disabled: {e}")

    # Exception handlers
    @app.exception_handler(KortanaException)
    async def kortana_exception_handler(request: Request, exc: KortanaException):
        """Handle custom Kortana exceptions"""
        log_error(
            exc.error_code,
            f"{exc.message} - Path: {request.url.path}",
            details=exc.details,
        )
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions"""
        log_error(
            "HTTP_ERROR",
            f"Status {exc.status_code} - Path: {request.url.path}",
            details={"detail": exc.detail},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": f"HTTP_{exc.status_code}",
                "detail": str(exc.detail) if exc.detail else "An error occurred",
                "message": str(exc.detail) if exc.detail else "An error occurred",
                "status_code": exc.status_code,
                "details": {},
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        log_error(
            "UNHANDLED_ERROR",
            f"Unexpected error: {str(exc)}",
            details={"path": request.url.path, "method": request.method},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "status_code": 500,
                "details": {},
            },
        )

    # Mount routers
    try:
        # Authentication router (public - no auth required)
        app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])

        # Protected API routers
        app.include_router(gemini.router, prefix="/api/gemini", tags=["gemini"])
        app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
        app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
        app.include_router(github.router, prefix="/api/github", tags=["github"])
        app.include_router(autonomy.router, prefix="/api/autonomy", tags=["autonomy"])
        app.include_router(
            knowledge.router, prefix="/api/knowledge", tags=["knowledge"]
        )
        app.include_router(
            task_queue.router, prefix="/api/task-queue", tags=["task-queue"]
        )

        # Phase 2: PR Creation, Testing, and Code Review
        app.include_router(pr_creation.router, prefix="/api/pr", tags=["pr-creation"])
        app.include_router(
            test_orchestrator.router, prefix="/api/testing", tags=["testing"]
        )
        app.include_router(
            code_reviewer.router, prefix="/api/code-review", tags=["code-review"]
        )

        # Billing router
        app.include_router(billing.router, prefix="/api/billing", tags=["billing"])

        # Human Only Protocol router (if available)
        if HOP_AVAILABLE and hop_router:
            app.include_router(
                hop_router, prefix="/api/autonomy/hop", tags=["human-only-protocol"]
            )
            print("[OK] Human Only Protocol router mounted")

        # Optimization router (if available)
        if OPTIMIZATION_AVAILABLE and optimization_router:
            app.include_router(
                optimization_router, prefix="/api/optimization", tags=["optimization"]
            )
            log_request("router", "Optimization monitoring router mounted")

        # Intelligence systems router (if available)
        if INTELLIGENCE_AVAILABLE and intelligence_router:
            app.include_router(intelligence_router.router)

        # Live Exerciser router (if available)
        if LIVE_EXERCISER_AVAILABLE and live_exerciser_router:
            app.include_router(live_exerciser_router.router)
            log_request("router", "Intelligence systems router mounted")
    except Exception as e:
        log_error("router_error", f"Error including routers: {e}")
        raise

    return app


# Create the application instance
app = create_app()


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Middleware to log all requests"""
    log_request(
        "http",
        f"{request.method} {request.url.path}",
        details={"query_params": dict(request.query_params)},
    )
    response = await call_next(request)
    return response


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    settings = get_settings()
    return {
        "status": "alive",
        "message": "Kor'tana backend is breathing",
        "environment": settings.ENVIRONMENT,
        "version": settings.API_VERSION,
    }


@app.head("/")
@app.get("/")
async def root():
    """Root endpoint with API information"""
    settings = get_settings()
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
    }
