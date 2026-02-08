"""
Kor'tana Main FastAPI Application
"""

import base64
from contextlib import asynccontextmanager  # For lifespan events
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from kortana.api.routers import core_router, goal_router
from kortana.api.routers.conversation_router import router as conversation_router
from kortana.brain import ChatEngine
from kortana.config import load_kortana_config
from kortana.core.scheduler import (
    get_scheduler_status,
    start_scheduler,
    stop_scheduler,
)
from kortana.modules.content_generation.router import router as content_router
from kortana.modules.emotional_intelligence.router import (
    router as emotional_intelligence_router,
)
from kortana.modules.ethical_transparency.router import router as ethics_router
from kortana.modules.gaming.router import router as gaming_router
from kortana.modules.marketplace.router import router as marketplace_router
from kortana.modules.memory_core.routers.memory_router import (
    router as memory_router,
)

# Import new module routers
from kortana.modules.multilingual.router import router as multilingual_router
from kortana.modules.plugin_framework.router import router as plugin_router
from kortana.modules.security.routers.security_router import (
    router as security_router,
)
from kortana.voice import VoiceChatOrchestrator, VoiceProcessingError

# Global configuration and engine
settings = load_kortana_config()
chat_engine = ChatEngine(settings=settings)
voice_orchestrator = VoiceChatOrchestrator(chat_engine=chat_engine)


class VoiceChatRequest(BaseModel):
    """Voice chat request payload."""

    audio_base64: str = Field(..., description="Base64-encoded WAV/PCM audio payload")
    session_id: str | None = Field(default=None)
    user_id: str | None = Field(default="default")
    user_name: str | None = Field(default=None)
    return_audio: bool | None = Field(default=None)


class VoiceTranscribeRequest(BaseModel):
    """Voice transcription request payload."""

    audio_base64: str = Field(..., description="Base64-encoded WAV/PCM audio payload")
    session_id: str | None = Field(default=None)
    user_id: str | None = Field(default="default")


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
app.include_router(conversation_router)  # Add conversation history router
app.include_router(core_router.router)
app.include_router(core_router.openai_adapter_router)
app.include_router(goal_router.router)
app.include_router(security_router)

# Include new module routers
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


@app.post("/voice/transcribe")
async def voice_transcribe(payload: VoiceTranscribeRequest) -> dict[str, Any]:
    """Transcribe voice payload into text with session context."""
    if not settings.voice.enabled:
        raise HTTPException(status_code=503, detail="Voice chat is disabled")

    try:
        audio_bytes = base64.b64decode(payload.audio_base64, validate=True)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail="Invalid base64 audio payload"
        ) from exc

    try:
        result = await voice_orchestrator.transcribe_only(
            audio_bytes=audio_bytes,
            session_id=payload.session_id,
            user_id=payload.user_id,
        )
        return {"status": "success", **result}
    except VoiceProcessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict()) from exc


@app.post("/voice/chat")
async def voice_chat(payload: VoiceChatRequest) -> dict[str, Any]:
    """Process a complete voice turn (STT -> LLM -> optional TTS)."""
    if not settings.voice.enabled:
        raise HTTPException(status_code=503, detail="Voice chat is disabled")

    try:
        audio_bytes = base64.b64decode(payload.audio_base64, validate=True)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail="Invalid base64 audio payload"
        ) from exc

    return_audio = (
        payload.return_audio
        if payload.return_audio is not None
        else settings.voice.return_audio_by_default
    )

    try:
        result = await voice_orchestrator.process_voice_turn(
            audio_bytes=audio_bytes,
            session_id=payload.session_id,
            user_id=payload.user_id,
            user_name=payload.user_name,
            return_audio=return_audio,
        )
        return {"status": "success", **result}
    except VoiceProcessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict()) from exc


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
