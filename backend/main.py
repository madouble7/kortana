"""
Kor'tana Backend - FastAPI Application
Multimodal AI constellation API with autonomous capabilities
"""

import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import configuration and utilities
from config import get_settings
from exceptions import KortanaException
from logger import log_error, log_request, setup_logging

# Import middleware
from middleware.security import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)

# Import routers
try:
    from routers import (
        agents,
        auth,
        autonomy,
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
    print(f"Error importing routers: {e}")
    raise

# Import Human Only Protocol (HOP) for autonomy
try:
    from human_only_protocol import router as hop_router

    HOP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Human Only Protocol: {e}")
    HOP_AVAILABLE = False
    hop_router = APIRouter()  # Provide empty router as fallback


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events"""
    # Startup
    settings = get_settings()

    # Validate configuration and secrets
    try:
        settings.validate()
        print(f"\n{'=' * 60}")
        print("🔐 Secrets Validation: COMPLETE")
        print(f"📦 Environment: {settings.ENVIRONMENT}")
        print("🔗 API Keys Loaded:")
        print(f"   ✓ Gemini API: {'✅' if settings.GEMINI_API_KEY else '❌'}")
        print(f"   ✓ GitHub Token: {'✅' if settings.GITHUB_TOKEN else '❌'}")
        print(f"   ✓ Discord Bot: {'✅' if settings.DISCORD_BOT_TOKEN else '❌'}")
        print(f"   ✓ OpenAI Key: {'✅' if settings.OPENAI_API_KEY else '❌'}")
        print(f"   ✓ Anthropic Key: {'✅' if settings.ANTHROPIC_API_KEY else '❌'}")
        print(f"   ✓ Pinecone Key: {'✅' if settings.PINECONE_API_KEY else '❌'}")
        print(f"   ✓ Stripe Keys: {'✅' if settings.STRIPE_SECRET_KEY else '❌'}")
        print(f"{'=' * 60}\n")
    except ValueError as e:
        log_error("config", f"Configuration validation failed: {e}")
        print(f"❌ Configuration Error: {e}")
        raise

    log_request("system", f"Kor'tana API starting in {settings.ENVIRONMENT} mode")
    print(f"🚀 Kor'tana API starting in {settings.ENVIRONMENT} mode")

    yield

    # Shutdown
    log_request("system", "Kor'tana API shutting down")
    print("👋 Kor'tana API shutting down")


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
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

    # Exception handlers
    @app.exception_handler(KortanaException)
    async def kortana_exception_handler(request: Request, exc: KortanaException) -> JSONResponse:
        """Handle custom Kortana exceptions"""
        log_error(exc.error_code, f"{exc.message} - Path: {request.url.path}", details=exc.details)
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
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
                "message": str(exc.detail) if exc.detail else "An error occurred",
                "status_code": exc.status_code,
                "details": {},
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
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
        app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
        app.include_router(task_queue.router, prefix="/api/task-queue", tags=["task-queue"])

        # Phase 2: PR Creation, Testing, and Code Review
        app.include_router(pr_creation.router, prefix="/api/pr", tags=["pr-creation"])
        app.include_router(test_orchestrator.router, prefix="/api/testing", tags=["testing"])
        app.include_router(code_reviewer.router, prefix="/api/code-review", tags=["code-review"])

        # Human Only Protocol (HOP)
        if HOP_AVAILABLE:
            app.include_router(hop_router, prefix="/api", tags=["protocol"])
    except Exception as e:
        log_error("router_error", f"Error including routers: {e}")
        raise

    return app


# Create the application instance
app = create_app()


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next: Any) -> Any:
    """Middleware to log all requests"""
    log_request(
        "http",
        f"{request.method} {request.url.path}",
        details={"query_params": dict(request.query_params)},
    )
    response = await call_next(request)
    return response


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint"""
    settings = get_settings()
    return {
        "status": "alive",
        "message": "Kor'tana backend is breathing",
        "environment": settings.ENVIRONMENT,
        "version": settings.API_VERSION,
    }


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint with API information"""
    settings = get_settings()
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
    }
