"""
Kor'tana Backend - FastAPI Application
Multimodal AI constellation API with autonomous capabilities
"""

import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import configuration and utilities
from src.kortana.config import get_settings
from src.kortana.exceptions import KortanaException
from src.kortana.logger import log_error, log_request, setup_logging

# Import Redis for caching
try:
    from redis import Redis
except ImportError:
    Redis = None

# Import middleware
from src.kortana.middleware.cache import CacheStrategy, ResponseCacheMiddleware
from src.kortana.middleware.security import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)

# Import routers
try:
    from src.kortana.routers import (
        agents,
        always_on,
        auth,
        autonomous_systems,
        autonomy,
        billing,
        code_reviewer,
        gemini,
        github,
        health,
        knowledge,
        memory,
        optimization,
        orchestration_advanced,
        orchestration_meta,
        orchestrator,
        pr_creation,
        prayer,
        rclone,
        system,
        task_queue,
        test_orchestrator,
    )
    from src.kortana.routers.adapters import (
        autogen_adapter,
        copilotkit_adapter,
        lobechat_adapter,
        openwebui_adapter,
    )
except ImportError as e:
    print(f"Error importing routers: {e}")
    raise

# Billing router currently lives in the root backend router stack.
try:
    from routers import billing as root_billing
except ImportError:
    root_billing = None

# Import Human Only Protocol (HOP) for autonomy
try:
    from src.kortana.human_only_protocol import router as hop_router

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
        print("--- Secrets Validation: COMPLETE ---")
        print(f"Environment: {settings.ENVIRONMENT}")
        print("API Keys Loaded:")
        print(f"   - Gemini API: {'[OK]' if settings.GEMINI_API_KEY else '[MISSING]'}")
        print(f"   - GitHub Token: {'[OK]' if settings.GITHUB_TOKEN else '[MISSING]'}")
        print(f"   - Discord Bot: {'[OK]' if settings.DISCORD_BOT_TOKEN else '[MISSING]'}")
        print(f"   - Discord Bot: {'[OK]' if settings.DISCORD_BOT_TOKEN else '[MISSING]'}")
        print(f"   - OpenAI Key: {'[OK]' if settings.OPENAI_API_KEY else '[MISSING]'}")
        print(f"   - Anthropic Key: {'[OK]' if settings.ANTHROPIC_API_KEY else '[MISSING]'}")
        print(f"   - Pinecone Key: {'[OK]' if settings.PINECONE_API_KEY else '[MISSING]'}")
        print(f"   - Stripe Keys: {'[OK]' if settings.STRIPE_SECRET_KEY else '[MISSING]'}")
        print(f"   - Anthropic Key: {'[OK]' if settings.ANTHROPIC_API_KEY else '[MISSING]'}")
        print(f"   - Pinecone Key: {'[OK]' if settings.PINECONE_API_KEY else '[MISSING]'}")
        print(f"   - Stripe Keys: {'[OK]' if settings.STRIPE_SECRET_KEY else '[MISSING]'}")
        print(f"{'=' * 60}\n")
    except ValueError as e:
        log_error("config", f"Configuration validation failed: {e}")
        print(f"[ERROR] Configuration Error: {e}")
        raise

    log_request("system", f"Kor'tana API starting in {settings.ENVIRONMENT} mode")
    print(f"[*] Kor'tana API starting in {settings.ENVIRONMENT} mode")

    yield

    # Shutdown
    log_request("system", "Kor'tana API shutting down")
    print("[-] Kor'tana API shutting down")


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

    # Response caching middleware for optimization
    # Initialize Redis for caching if available
    if Redis is not None:
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            redis_client = Redis.from_url(redis_url)
            cache_strategy = CacheStrategy(
                ttl=300,  # 5 minutes
                key_prefix="api_cache:",
                exclude_paths=[
                    "/health",
                    "/docs",
                    "/openapi.json",
                    "/protocol/auto/execute",
                    "/api/optimization",
                ],
            )
            app.add_middleware(
                ResponseCacheMiddleware,
                redis_client=redis_client,
                strategy=cache_strategy,
            )
        except Exception as e:
            log_error("CACHE_INIT", f"Failed to initialize response caching: {e}")
    # Note: caching gracefully disabled if Redis unavailable

    # Security middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    if settings.ENVIRONMENT != "testing":
        app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

    # Exception handlers
    @app.exception_handler(KortanaException)
    async def kortana_exception_handler(request: Request, exc: KortanaException) -> JSONResponse:
        """Handle custom Kortana exceptions"""
        log_error(
            exc.error_code,
            f"{exc.message} - Path: {request.url.path}",
            details=exc.details,
        )
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
                "detail": str(exc.detail) if exc.detail else "An error occurred",
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
        app.include_router(health.router, prefix="/api/system/health", tags=["health"])
        app.include_router(prayer.router)
        app.include_router(gemini.router, prefix="/api/gemini", tags=["gemini"])
        app.include_router(
            orchestrator.router, prefix="/api/orchestrator", tags=["ai-orchestrator"]
        )
        app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
        app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
        app.include_router(github.router, prefix="/api/github", tags=["github"])
        app.include_router(autonomy.router, prefix="/api/autonomy", tags=["autonomy"])
        app.include_router(autonomous_systems.router, prefix="/api/autonomous", tags=["autonomous"])
        app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
        app.include_router(task_queue.router, prefix="/api/task-queue", tags=["task-queue"])
        app.include_router(rclone.router, prefix="/api/rclone", tags=["rclone"])
        app.include_router(system.router, prefix="/api/system", tags=["system"])
        app.include_router(always_on.router, prefix="/api/always-on", tags=["always-on"])

        # Phase 2: PR Creation, Testing, and Code Review
        app.include_router(pr_creation.router, prefix="/api/pr", tags=["pr-creation"])
        app.include_router(test_orchestrator.router, prefix="/api/testing", tags=["testing"])
        app.include_router(code_reviewer.router, prefix="/api/code-review", tags=["code-review"])

        # Optimization monitoring and control
        app.include_router(
            optimization.router, prefix="/api/optimization", tags=["optimization"]
        )
        app.include_router(
            orchestration_advanced.router,
            prefix="/api/orchestration/advanced",
            tags=["advanced-orchestration"],
        )
        app.include_router(
            orchestration_meta.router,
            prefix="/api/orchestration/meta",
            tags=["meta-coordination"],
        )

        # Billing management
        app.include_router(billing.router)

        # Frontend Adapters
        app.include_router(
            autogen_adapter.router,
            prefix="/api/adapters/autogen",
            tags=["adapters", "autogen"],
        )
        app.include_router(
            copilotkit_adapter.router,
            prefix="/api/adapters/copilotkit",
            tags=["adapters", "copilotkit"],
        )
        app.include_router(
            openwebui_adapter.router,
            prefix="/api/adapters/openwebui",
            tags=["adapters", "openwebui"],
        )
        app.include_router(
            lobechat_adapter.router,
            prefix="/api/adapters/lobechat",
            tags=["adapters", "lobechat"],
        )

        # Basic API endpoints (defined before catch-all)
        @app.get("/api/health", tags=["system"])
        async def api_health():
            """Health check endpoint for the frontend"""
            return {
                "status": "alive",
                "message": "Kor'tana backend is breathing",
                "version": get_settings().API_VERSION,
                "environment": get_settings().ENVIRONMENT,
                "timestamp": datetime.now().isoformat(),
            }

        @app.get("/", tags=["system"])
        @app.get("/api/info", tags=["system"])
        async def api_info():
            """Basic API information"""
            settings = get_settings()
            return {
                "name": settings.API_TITLE,
                "version": settings.API_VERSION,
                "status": "running",
                "environment": settings.ENVIRONMENT,
            }

        # Human Only Protocol (HOP)
        if HOP_AVAILABLE:
            app.include_router(hop_router, prefix="/api", tags=["protocol"])

        # Mount static files for frontend in production
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
        if os.path.exists(static_dir):
            app.mount(
                "/assets",
                StaticFiles(directory=os.path.join(static_dir, "assets")),
                name="assets",
            )

            @app.get("/{full_path:path}")
            async def serve_frontend(request: Request, full_path: str):
                """Serve the frontend SPA for any unmatched routes with runtime config injection"""
                # Don't intercept /api routes
                if full_path.startswith("api"):
                    return JSONResponse(
                        status_code=404,
                        content={
                            "error": "Not Found",
                            "message": "API route not found",
                        },
                    )

                file_path = os.path.join(static_dir, full_path)

                # Check if it's the index.html or a directory (which serves index.html)
                if not os.path.isfile(file_path):
                    index_path = os.path.join(static_dir, "index.html")
                    if os.path.exists(index_path):
                        with open(index_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Inject runtime configuration
                        settings = get_settings()
                        runtime_config = {
                            "VITE_API_URL": "",  # Empty for relative paths in unified mode
                            "ENVIRONMENT": settings.ENVIRONMENT,
                            "VERSION": settings.API_VERSION,
                        }
                        import json

                        config_script = (
                            f"<script>window.__KORTANA__ = {json.dumps(runtime_config)};</script>"
                        )
                        config_script = (
                            f"<script>window.__KORTANA__ = {json.dumps(runtime_config)};</script>"
                        )

                        # Insert before the first script tag or head end
                        if "</head>" in content:
                            content = content.replace("</head>", f"{config_script}\n</head>")
                            content = content.replace("</head>", f"{config_script}\n</head>")

                        from fastapi.responses import HTMLResponse

                        return HTMLResponse(content=content)

                if os.path.isfile(file_path):
                    return FileResponse(file_path)

                return FileResponse(os.path.join(static_dir, "index.html"))

    except Exception as e:
        log_error("router_error", f"Error including routers: {e}")
        raise

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.kortana.main:app", host="0.0.0.0", port=8000, reload=True)
