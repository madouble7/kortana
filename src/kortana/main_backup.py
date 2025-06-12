try:
    from fastapi import FastAPI, Depends

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("⚠️  FastAPI not available - running in minimal mode")

try:
    from .config.settings import settings

    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    print("⚠️  Settings module not available")

try:
    from .core.scheduler import get_scheduler_status, start_scheduler, stop_scheduler

    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("⚠️  Scheduler not available")

if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Kor'tana AI System",
        description="kor'tana: context-aware ethical ai system.",
        version="0.1.0",
    )
else:
    app = None


@app.on_event("startup")
async def startup_event():
    """
    Initialize Kor'tana's autonomous capabilities on startup.
    This is where she transitions from dormant to active autonomous agent.
    """
    print(f"🚀 Starting up {settings.APP_NAME}...")
    print("🧠 Initializing autonomous scheduler...")

    try:
        start_scheduler()
        print("✅ Kor'tana's autonomous agent is now ACTIVE")
        print("🔄 Self-directed tasks will begin running automatically")
    except Exception as e:
        print(f"❌ Failed to start autonomous scheduler: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Gracefully stop Kor'tana's autonomous capabilities on shutdown.
    """
    print(f"🛑 Shutting down {settings.APP_NAME}...")
    print("🧠 Stopping autonomous scheduler...")

    try:
        stop_scheduler()
        print("✅ Autonomous agent shutdown complete")
    except Exception as e:
        print(f"❌ Error during autonomous scheduler shutdown: {e}")


@app.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "message": "kor'tana is awakening...",
    }


@app.get("/autonomous/status", tags=["system"])
async def autonomous_status():
    """
    Check the status of Kor'tana's autonomous agent scheduler.
    This endpoint shows whether she is actively running autonomous tasks.
    """
    try:
        status = get_scheduler_status()
        return {
            "autonomous_agent": "active" if status["running"] else "inactive",
            "scheduler_running": status["running"],
            "active_jobs": status["jobs"],
            "message": "Kor'tana is operating autonomously"
            if status["running"]
            else "Autonomous agent is dormant",
        }
    except Exception as e:
        return {
            "autonomous_agent": "error",
            "scheduler_running": False,
            "error": str(e),
            "message": "Failed to check autonomous agent status",
        }


@app.get("/test-db", tags=["system"])
def test_db_connection(db: Session = Depends(database.get_db_sync)):
    try:
        from sqlalchemy import text

        result = db.execute(text("SELECT 1")).scalar_one()
        return {"db_connection": "ok", "result": result}
    except Exception as e:
        return {"db_connection": "error", "detail": str(e)}


# --- Include Routers ---
app.include_router(memory_router)
app.include_router(core_router.router)
app.include_router(
    openai_adapter_router.router
)  # Assuming this was intended to be included
app.include_router(adapter_router)  # Added the new adapter_router for LobeChat etc.
