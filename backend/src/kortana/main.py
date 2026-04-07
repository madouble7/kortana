"""
Kor'tana Backend - FastAPI Application
Multimodal AI constellation API with autonomous capabilities
"""

import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

# Add backend directory to path
backend_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import configuration and utilities
# noqa: E402 — these must follow the sys.path.insert block above
from src.kortana.config import get_settings  # noqa: E402
from src.kortana.exceptions import KortanaException  # noqa: E402
from src.kortana.logger import log_error, log_request, setup_logging  # noqa: E402
from src.kortana.middleware.cache import (  # noqa: E402
    DEFAULT_CACHE_EXCLUDE_PATHS,
    CacheStrategy,
    ResponseCacheMiddleware,
)

# Import security middleware
from src.kortana.middleware.security import (  # noqa: E402
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)

try:
    from redis import Redis as RedisClient
except ImportError:
    RedisClient = None  # type: ignore[assignment,misc]

try:
    from src.kortana.human_only_protocol import router as hop_router

    HOP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Human Only Protocol: {e}")
    HOP_AVAILABLE = False
    hop_router = APIRouter()  # Provide empty router as fallback

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
        consciousness,
        gemini,
        github,
        health,
        knowledge,
        live_exerciser,
        matrix_ws,
        memory,
        optimization,
        orchestration_advanced,
        orchestration_meta,
        orchestrator,
        pr_creation,
        prayer,
        rclone,
        singularity_bridge,
        songwriting,
        system,
        task_queue,
        test_orchestrator,
    )
    from src.kortana.routers import consensus as consensus_router
    from src.kortana.routers import daemon as daemon_router
    from src.kortana.routers import intelligence as intelligence_router
    from src.kortana.routers.adapters import (
        autogen_adapter,
        copilotkit_adapter,
        lobechat_adapter,
        openwebui_adapter,
    )
except ImportError as e:
    print(f"Error importing routers: {e}")
    raise


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
        print(
            f"   - Discord Bot: {'[OK]' if settings.DISCORD_BOT_TOKEN else '[MISSING]'}"
        )
        ok_missing = lambda k: "[OK]" if k else "[MISSING]"  # noqa: E731
        print(f"   - OpenAI Key: {ok_missing(settings.OPENAI_API_KEY)}")
        print(f"   - Anthropic Key: {ok_missing(settings.ANTHROPIC_API_KEY)}")
        print(f"   - Pinecone Key: {ok_missing(settings.PINECONE_API_KEY)}")
        print(
            f"   - Stripe Keys: {'[OK]' if settings.STRIPE_SECRET_KEY else '[MISSING]'}"
        )
        print(f"{'=' * 60}\n")
    except ValueError as e:
        log_error("config", f"Configuration validation failed: {e}")
        print(f"[ERROR] Configuration Error: {e}")
        raise

    # Create database tables if they don't exist
    try:
        from src.kortana.database import get_db_manager
        from src.kortana.models import Base

        db_manager = get_db_manager()
        await db_manager.initialize()
        assert db_manager.engine is not None, "DB engine not initialized"
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[*] Database tables verified/created")
    except Exception as e:
        print(f"[WARN] Database table creation: {e}")

    log_request("system", f"Kor'tana API starting in {settings.ENVIRONMENT} mode")
    print(f"[*] Kor'tana API starting in {settings.ENVIRONMENT} mode")

    # Start autonomy daemon only when this process is explicitly the daemon host.
    # In the default decoupled deployment the daemon runs as a separate process
    # (Procfile `daemon:` / Railway daemon service); set
    # KORTANA_DAEMON_IN_PROCESS=true to opt back in to the embedded model.
    if os.getenv("KORTANA_DAEMON_IN_PROCESS", "false").lower() == "true":
        try:
            from src.kortana.services.autonomy_daemon import get_autonomy_daemon

            daemon = get_autonomy_daemon()
            await daemon.start()
            print("[*] Autonomy daemon started (in-process)")
        except Exception as e:
            print(f"[WARN] Autonomy daemon startup: {e}")
    else:
        print(
            "[*] Autonomy daemon skipped in web process "
            "(dedicated daemon service expected)"
        )

    try:
        from src.kortana.services.workspace_bridge_service import get_workspace_bridge

        workspace_status = get_workspace_bridge().get_status()
        if workspace_status.get("canonical_warning"):
            print(
                f"[WARN] Workspace root drift: {workspace_status['canonical_warning']}"
            )
        else:
            print(f"[*] Workspace root verified: {workspace_status['repo_root']}")
    except Exception as e:
        print(f"[WARN] Workspace root verification: {e}")

    # Start Discord bot (non-blocking) only when explicitly enabled.
    if settings.DISCORD_ENABLED:
        try:
            from src.kortana.services.discord_service import (
                get_discord_bot,
                start_discord_bot,
            )

            await start_discord_bot()
            bot = get_discord_bot()
            if bot:
                daemon = get_autonomy_daemon()
                daemon.on_event(lambda evt: bot.relay_event(evt.type, evt.data))
                print("[*] Discord bot spawned")
            else:
                print("[*] Discord bot disabled (no token)")
        except Exception as e:
            print(f"[WARN] Discord bot startup: {e}")
    else:
        print("[*] Discord integration disabled by configuration")

    # Bootstrap intelligence systems (Self-Awareness, Learner, Goals)
    try:
        from src.kortana.services.adaptive_learner import get_adaptive_learner
        from src.kortana.services.goal_manager import get_goal_manager
        from src.kortana.services.self_awareness import get_self_awareness

        sa = get_self_awareness()
        learner = await get_adaptive_learner()
        gm = get_goal_manager()
        await gm.load_from_db()
        status_line = (
            f"[*] Intelligence online — SA:{sa._state.value} "
            f" Goals:{gm.get_status()['total_goals']} "
            f" Learner:{learner.get_status()['outcomes_recorded']} outcomes"
        )
        print(status_line)
    except Exception as e:
        print(f"[WARN] Intelligence systems startup: {e}")

    yield

    # Shutdown
    try:
        from src.kortana.services.autonomy_daemon import (
            get_autonomy_daemon as _get_daemon,
        )

        await _get_daemon().stop()
    except Exception:
        pass
    if settings.DISCORD_ENABLED:
        try:
            from src.kortana.services.discord_service import get_discord_bot as _get_bot

            b = _get_bot()
            if b:
                await b.close()
        except Exception:
            pass
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

    # Probe Redis reachability once at startup so we don't spam errors
    # on every request when Redis is absent (e.g. Render free tier).
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    _redis_available = False
    if RedisClient is not None and settings.ENVIRONMENT != "testing":
        try:
            _probe = RedisClient.from_url(redis_url, socket_connect_timeout=2)
            _probe.ping()
            _probe.close()
            _redis_available = True
        except Exception:
            print("[WARN] Redis not reachable — rate limiting and caching disabled")

    # Response caching middleware for optimization
    if _redis_available:
        try:
            redis_client = RedisClient.from_url(redis_url)
            cache_strategy = CacheStrategy(
                ttl=300,  # 5 minutes
                key_prefix="api_cache:",
                exclude_paths=[
                    *DEFAULT_CACHE_EXCLUDE_PATHS,
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

    # Security middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    if settings.ENVIRONMENT != "testing":
        if settings.RATE_LIMIT_ENABLED and _redis_available:
            app.add_middleware(
                RateLimitMiddleware,
                requests_per_minute=settings.RATE_LIMIT_REQUESTS,
                period_seconds=settings.RATE_LIMIT_PERIOD,
                redis_url=redis_url,
                proxy_mode=settings.RATE_LIMIT_PROXY_MODE,
                trusted_proxies=tuple(settings.RATE_LIMIT_TRUSTED_PROXIES),
            )
        elif not settings.RATE_LIMIT_ENABLED:
            print("[*] RateLimitMiddleware disabled by configuration")
        else:
            print("[WARN] RateLimitMiddleware skipped — no Redis")

    # Exception handlers
    @app.exception_handler(KortanaException)
    async def kortana_exception_handler(
        request: Request, exc: KortanaException
    ) -> JSONResponse:
        """Handle custom Kortana exceptions"""
        log_error(
            exc.error_code,
            f"{exc.message} - Path: {request.url.path}",
            details=exc.details,
        )
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
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
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
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
        app.include_router(
            autonomous_systems.router, prefix="/api/autonomous", tags=["autonomous"]
        )
        app.include_router(
            knowledge.router, prefix="/api/knowledge", tags=["knowledge"]
        )
        app.include_router(
            task_queue.router, prefix="/api/task-queue", tags=["task-queue"]
        )
        app.include_router(rclone.router, prefix="/api/rclone", tags=["rclone"])
        app.include_router(songwriting.router)
        app.include_router(system.router, prefix="/api/system", tags=["system"])
        app.include_router(
            always_on.router, prefix="/api/always-on", tags=["always-on"]
        )

        # Phase 2: PR Creation, Testing, and Code Review
        app.include_router(pr_creation.router, prefix="/api/pr", tags=["pr-creation"])
        app.include_router(
            test_orchestrator.router, prefix="/api/testing", tags=["testing"]
        )
        app.include_router(
            code_reviewer.router, prefix="/api/code-review", tags=["code-review"]
        )

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
        app.include_router(
            singularity_bridge.router,
            prefix="/api/singularity",
            tags=["singularity-bridge"],
        )

        # Phase 8: Consciousness Persistence & Self-Repair
        app.include_router(consciousness.router)
        app.include_router(matrix_ws.router, prefix="/api/matrix", tags=["matrix"])

        # Live Exerciser: Real API calls + PostgreSQL integration
        app.include_router(live_exerciser.router)

        # Billing management
        app.include_router(billing.router)

        # AI Consensus Engine
        app.include_router(consensus_router.router)

        # Autonomy Daemon control
        app.include_router(daemon_router.router)

        # Intelligence systems (Self-Awareness, Learner, Goals)
        app.include_router(intelligence_router.router)

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

        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

        def render_frontend_index() -> Response | None:
            """Serve the SPA shell with runtime config injection."""
            index_path = os.path.join(static_dir, "index.html")
            if not os.path.exists(index_path):
                return None

            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()

            runtime_config = {
                "VITE_API_URL": "",  # Empty for relative paths in unified mode
                "ENVIRONMENT": settings.ENVIRONMENT,
                "VERSION": settings.API_VERSION,
            }
            import json

            config_script = (
                f"<script>window.__KORTANA__ = {json.dumps(runtime_config)};</script>"
            )

            if "window.__KORTANA__ =" not in content and "</head>" in content:
                content = content.replace("</head>", f"{config_script}\n</head>")

            from fastapi.responses import HTMLResponse

            return HTMLResponse(content=content)

        # Basic API endpoints (defined before catch-all)
        @app.get("/api/health", tags=["system"])
        async def api_health() -> dict[str, Any]:
            """Health check endpoint for the frontend"""
            return {
                "status": "alive",
                "message": "Kor'tana backend is breathing",
                "version": get_settings().API_VERSION,
                "environment": get_settings().ENVIRONMENT,
                "timestamp": datetime.now().isoformat(),
            }

        @app.get("/", tags=["system"], response_model=None)
        async def root(request: Request):
            """Serve the SPA shell for browsers and JSON info for API callers."""
            accepts = request.headers.get("accept", "")
            if "text/html" in accepts:
                frontend = render_frontend_index()
                if frontend is not None:
                    return frontend

            return {
                "name": settings.API_TITLE,
                "version": settings.API_VERSION,
                "status": "running",
                "environment": settings.ENVIRONMENT,
            }

        @app.head("/", tags=["system"])
        async def root_head() -> Response:
            return Response(status_code=200)

        @app.get("/api/info", tags=["system"])
        async def api_info() -> dict[str, Any]:
            """Basic API information"""
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
        if os.path.exists(static_dir):
            app.mount(
                "/assets",
                StaticFiles(directory=os.path.join(static_dir, "assets")),
                name="assets",
            )

            @app.get("/{full_path:path}")
            async def serve_frontend(request: Request, full_path: str) -> Response:
                """Serve the frontend SPA for unmatched routes."""
                # Don't intercept /api routes
                if full_path.startswith("api"):
                    return JSONResponse(
                        status_code=404,
                        content={
                            "error": "Not Found",
                            "message": "API route not found",
                        },
                    )

                normalized_path = full_path.strip("/")
                if normalized_path in ("", "index.html"):
                    frontend = render_frontend_index()
                    if frontend is not None:
                        return frontend

                file_path = os.path.join(static_dir, normalized_path)

                # Check if it's a direct asset; otherwise, serve the SPA shell.
                if not os.path.isfile(file_path):
                    frontend = render_frontend_index()
                    if frontend is not None:
                        return frontend

                if os.path.isfile(file_path):
                    return FileResponse(file_path)

                frontend = render_frontend_index()
                if frontend is not None:
                    return frontend

                return JSONResponse(
                    status_code=404,
                    content={"error": "Not Found", "message": "Frontend not built"},
                )

    except Exception as e:
        log_error("router_error", f"Error including routers: {e}")
        raise

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.kortana.main:app", host="0.0.0.0", port=8000, reload=True)
