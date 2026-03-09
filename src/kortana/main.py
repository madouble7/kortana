"""
Kor'tana Main FastAPI Application
"""

from contextlib import asynccontextmanager  # For lifespan events

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.kortana.api.routers import core_router, goal_router
from src.kortana.api.routers.conversation_router import router as conversation_router
from src.kortana.brain import ChatEngine
from src.kortana.config import load_kortana_config
from src.kortana.core.scheduler import (
    get_scheduler_status,
    start_scheduler,
    stop_scheduler,
)
from src.kortana.modules.content_generation.router import router as content_router
from src.kortana.modules.emotional_intelligence.router import (
    router as emotional_intelligence_router,
)
from src.kortana.modules.ethical_transparency.router import router as ethics_router
from src.kortana.modules.gaming.router import router as gaming_router
from src.kortana.modules.marketplace.router import router as marketplace_router
from src.kortana.modules.memory_core.routers.memory_router import (
    router as memory_router,
)
from src.kortana.modules.security.routers.security_router import (
    router as security_router,
)

# Import new module routers
from src.kortana.modules.multilingual.router import router as multilingual_router
from src.kortana.modules.plugin_framework.router import router as plugin_router

# Global configuration and engine
settings = load_kortana_config()
chat_engine = ChatEngine(settings=settings)


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
app.include_router(core_router.openai_adapter_router)
app.include_router(goal_router.router)
app.include_router(conversation_router)  # Add conversation history router

# Include module routers
app.include_router(security_router)
app.include_router(multilingual_router)
app.include_router(emotional_intelligence_router)
app.include_router(content_router)
app.include_router(plugin_router)
app.include_router(ethics_router)
app.include_router(gaming_router)
app.include_router(marketplace_router)


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
        # Use simple get_response from ChatEngine
        response = chat_engine.get_response(user_message)
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

        response = chat_engine.get_response(user_message)

        return {"choices": [{"message": {"role": "assistant", "content": response}}]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
