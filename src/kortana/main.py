"""
Kor'tana Main FastAPI Application
"""

from contextlib import asynccontextmanager  # For lifespan events
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.kortana.api.routers import core_router, goal_router
from src.kortana.api.routers.core_router import openai_adapter_router
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
app.include_router(openai_adapter_router)

# Mount static files
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def read_root():
    """Serve the chat interface."""
    static_file = static_dir / "chat.html"
    if static_file.exists():
        return FileResponse(static_file)
    return {"message": "Kor'tana API is running. Use /docs for API documentation."}


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
    """Enhanced chat endpoint using full orchestrator capabilities."""
    try:
        from src.kortana.services.database import get_db_sync
        from src.kortana.core.orchestrator import KorOrchestrator
        
        user_message = message.get("message", "")
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Use a database session for this request
        db = next(get_db_sync())
        try:
            orchestrator = KorOrchestrator(db=db)
            result = await orchestrator.process_query(query=user_message)
            
            # Extract the final response
            final_response = result.get("final_kortana_response", 
                                      result.get("response", 
                                                "I'm having trouble processing that right now."))
            
            return {
                "response": final_response,
                "status": "success",
                "conversation_id": message.get("conversation_id"),
                "metadata": {
                    "model": result.get("llm_metadata", {}).get("model"),
                    "context_used": len(result.get("context_from_memory", [])) > 0
                }
            }
        finally:
            db.close()
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
    """LobeChat adapter endpoint using full orchestrator capabilities."""
    try:
        from src.kortana.services.database import get_db_sync
        from src.kortana.core.orchestrator import KorOrchestrator
        
        messages = request.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Extract the last user message
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Use a database session for this request
        db = next(get_db_sync())
        try:
            orchestrator = KorOrchestrator(db=db)
            result = await orchestrator.process_query(query=user_message)
            
            # Extract the final response
            final_response = result.get("final_kortana_response", 
                                      result.get("response", 
                                                "I'm having trouble processing that right now."))
            
            # Return in OpenAI-compatible format
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": final_response
                    },
                    "finish_reason": "stop",
                    "index": 0
                }],
                "model": result.get("llm_metadata", {}).get("model", "kortana-custom"),
                "usage": result.get("llm_metadata", {}).get("usage", {})
            }
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
