"""
Kor'tana Main FastAPI Application
"""

from contextlib import asynccontextmanager  # For lifespan events

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.kortana.adapters.copilotkit_adapter import router as copilotkit_router
from src.kortana.api.routers import core_router, goal_router
from src.kortana.core.scheduler import (
    get_scheduler_status,
    start_scheduler,
    stop_scheduler,
)
from src.kortana.modules.memory_core.routers.memory_router import (
    router as memory_router,
)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("INFO:     Starting Kor'tana's autonomous scheduler...")
    start_scheduler()
    print("INFO:     Kor'tana's autonomous scheduler started.")
    yield
    # Shutdown
    print("INFO:     Stopping Kor'tana's autonomous scheduler...")
    stop_scheduler()
    print("INFO:     Kor'tana's autonomous scheduler stopped.")


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
app.include_router(copilotkit_router)


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
async def chat(message: dict):
    try:
        user_message = message.get("message", "")
        response = f"Kor'tana received: {user_message}"
        return {"response": response, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        response = f"Kor'tana (via LobeChat): {user_message}"

        return {"choices": [{"message": {"role": "assistant", "content": response}}]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
