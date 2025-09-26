"""Kor'tana Main FastAPI Application."""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.kortana.api.routers import core_router, goal_router
from src.kortana.config import load_config
from src.kortana.core.scheduler import (
    get_scheduler_status,
    start_scheduler,
    stop_scheduler,
)
from src.kortana.core.services import (
    get_chat_engine,
    initialize_services,
    reset_services,
)
from src.kortana.modules.memory_core.routers.memory_router import (
    router as memory_router,
)

logger = logging.getLogger(__name__)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_config()
    initialize_services(settings)
    app.state.settings = settings

    scheduler_started = False
    try:
        logger.info("Starting Kor'tana scheduler...")
        start_scheduler()
        scheduler_started = True
        logger.info("Kor'tana scheduler started.")
        yield
    finally:
        if scheduler_started:
            logger.info("Stopping Kor'tana scheduler...")
            stop_scheduler()
            logger.info("Kor'tana scheduler stopped.")
        reset_services()


app = FastAPI(
    title="Kor'tana AI System",
    description="The Warchief's AI Companion",
    version="1.0.0",
    lifespan=lifespan,  # Add lifespan manager
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(memory_router)
app.include_router(core_router.router)
app.include_router(goal_router.router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Kor'tana",
        "version": "1.0.0",
        "message": "The Warchief's companion is ready",
    }


@app.get("/test-db")
def test_db():
    try:
        import os
        import sqlite3

        db_path = "kortana.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            return {"db_connection": "ok", "result": result[0] if result else None}
        else:
            return {
                "db_connection": "no_database",
                "message": "Run init_db.py to create",
            }
    except Exception as e:
        return {"db_connection": "error", "detail": str(e)}


@app.post("/chat")
async def chat(message: dict[str, Any]):
    user_message = (message.get("message") or "").strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        chat_engine = get_chat_engine()
        response_text = await chat_engine.process_message(user_message)
        return {"response": response_text, "status": "success"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Error processing chat request")
        raise HTTPException(
            status_code=500,
            detail="Kor'tana encountered an unexpected issue while thinking.",
        ) from exc


@app.get("/status")
def system_status():
    scheduler_info = get_scheduler_status()
    return {
        "autonomous_agent": "ready",
        "scheduler_running": scheduler_info.get("running", False),
        "scheduler_jobs": scheduler_info.get("jobs", []),
        "message": "Kor'tana system operational",
    }


@app.post("/adapters/lobechat/chat")
async def lobechat_adapter(request: dict):
    try:
        messages = request.get("messages", [])
        user_message = messages[-1].get("content", "") if messages else "Hello"
        chat_engine = get_chat_engine()
        response_text = await chat_engine.process_message(user_message)

        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                    }
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
