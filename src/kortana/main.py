"""Kor'tana Main FastAPI Application."""

from __future__ import annotations

import base64
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from kortana.api.routers import core_router, goal_router
from kortana.api.routers.conversation_router import router as conversation_router
from kortana.brain import ChatEngine
from kortana.config import load_kortana_config
from kortana.core.scheduler import get_scheduler_status, start_scheduler, stop_scheduler
from kortana.modules.content_generation.router import router as content_router
from kortana.modules.emotional_intelligence.router import (
    router as emotional_intelligence_router,
)
from kortana.modules.ethical_transparency.router import router as ethics_router
from kortana.modules.gaming.router import router as gaming_router
from kortana.modules.marketplace.router import router as marketplace_router
from kortana.modules.memory_core.routers.memory_router import router as memory_router
from kortana.modules.multilingual.router import router as multilingual_router
from kortana.modules.plugin_framework.router import router as plugin_router
from kortana.modules.security.routers.security_router import router as security_router
from kortana.voice import VoiceChatOrchestrator, VoiceProcessingError, VoiceSessionManager
from kortana.voice.stt_service import STTConfig, STTService
from kortana.voice.tts_service import TTSConfig, TTSService

settings = load_kortana_config()
chat_engine = ChatEngine(settings=settings)
voice_session_manager = VoiceSessionManager()
voice_orchestrator = VoiceChatOrchestrator(
    chat_engine=chat_engine,
    stt_service=STTService(
        STTConfig(
            max_audio_bytes=settings.voice.max_audio_bytes,
            min_audio_seconds=settings.voice.min_audio_seconds,
            provider=settings.voice.stt_provider,
            fallback_provider=settings.voice.stt_fallback_provider,
            openai_model=settings.voice.openai_stt_model,
        )
    ),
    tts_service=TTSService(
        TTSConfig(
            provider=settings.voice.tts_provider,
            fallback_provider=settings.voice.tts_fallback_provider,
            voice_name=settings.voice.tts_voice_name,
            rate=settings.voice.tts_rate,
            volume=settings.voice.tts_volume,
        )
    ),
    session_manager=voice_session_manager,
    session_idle_seconds=settings.voice.session_idle_seconds,
    max_active_sessions=settings.voice.max_active_sessions,
)


class VoiceChatRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64-encoded WAV/PCM audio payload")
    session_id: str | None = None
    user_id: str | None = "default"
    user_name: str | None = None
    return_audio: bool | None = None


class VoiceTranscribeRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64-encoded WAV/PCM audio payload")
    session_id: str | None = None
    user_id: str | None = "default"


class VoiceInterruptRequest(BaseModel):
    interrupted: bool = True


def _decode_audio_payload(audio_base64: str) -> bytes:
    if not audio_base64 or not audio_base64.strip():
        raise HTTPException(status_code=400, detail="Audio payload cannot be empty")

    normalized = audio_base64.strip()
    if normalized.lower().startswith("data:"):
        if "," not in normalized:
            raise HTTPException(status_code=400, detail="Invalid audio data URI format")
        header, normalized = normalized.split(",", 1)
        if ";base64" not in header.lower():
            raise HTTPException(
                status_code=400,
                detail="Audio data URI must be base64 encoded",
            )

    compact = "".join(normalized.split())
    if not compact:
        raise HTTPException(status_code=400, detail="Audio payload cannot be empty")

    max_audio_bytes = settings.voice.max_audio_bytes
    max_base64_len = ((max_audio_bytes + 2) // 3) * 4
    if len(compact) > max_base64_len + 4:
        raise HTTPException(status_code=413, detail="Audio payload exceeds size limit")

    try:
        decoded = base64.b64decode(compact, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 audio payload") from exc
    if len(decoded) > max_audio_bytes:
        raise HTTPException(status_code=413, detail="Audio payload exceeds size limit")
    return decoded


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("INFO:     Starting Kor'tana's autonomous scheduler...")
    start_scheduler()
    print("INFO:     Kor'tana's autonomous scheduler started.")
    yield
    print("INFO:     Stopping Kor'tana's autonomous scheduler...")
    stop_scheduler()
    print("INFO:     Kor'tana's autonomous scheduler stopped.")


app = FastAPI(
    title="Kor'tana AI System",
    description="The Warchief's AI Companion",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(memory_router)
app.include_router(conversation_router)
app.include_router(core_router.router)
app.include_router(core_router.openai_adapter_router)
app.include_router(goal_router.router)
app.include_router(security_router)
app.include_router(multilingual_router)
app.include_router(emotional_intelligence_router)
app.include_router(content_router)
app.include_router(plugin_router)
app.include_router(ethics_router)
app.include_router(gaming_router)
app.include_router(marketplace_router)


@app.get("/health")
def health_check() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": "Kor'tana",
        "version": "1.0.0",
        "message": "The Warchief's companion is ready",
    }


@app.post("/chat")
async def chat(message: dict[str, Any]) -> dict[str, Any]:
    try:
        user_message = message.get("message", "")
        response = chat_engine.get_response(user_message)
        return {"response": response, "status": "success"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/voice/transcribe")
async def voice_transcribe(payload: VoiceTranscribeRequest) -> dict[str, Any]:
    if not settings.voice.enabled:
        raise HTTPException(status_code=503, detail="Voice chat is disabled")

    audio_bytes = _decode_audio_payload(payload.audio_base64)
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
    if not settings.voice.enabled:
        raise HTTPException(status_code=503, detail="Voice chat is disabled")

    audio_bytes = _decode_audio_payload(payload.audio_base64)
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


@app.get("/voice/sessions/{session_id}")
async def get_voice_session(session_id: str) -> dict[str, Any]:
    if not settings.voice.enabled:
        raise HTTPException(status_code=503, detail="Voice chat is disabled")

    snapshot = voice_session_manager.get_snapshot(session_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Voice session not found")
    return {"status": "success", "session": snapshot}


@app.post("/voice/sessions/{session_id}/interrupt")
async def interrupt_voice_session(
    session_id: str,
    payload: VoiceInterruptRequest | None = None,
) -> dict[str, Any]:
    if not settings.voice.enabled:
        raise HTTPException(status_code=503, detail="Voice chat is disabled")

    if voice_session_manager.get_snapshot(session_id) is None:
        raise HTTPException(status_code=404, detail="Voice session not found")

    interrupted = payload.interrupted if payload else True
    voice_session_manager.mark_interrupted(session_id, interrupted=interrupted)
    snapshot = voice_session_manager.get_snapshot(session_id)
    return {"status": "success", "session": snapshot}


@app.delete("/voice/sessions/{session_id}")
async def end_voice_session(session_id: str) -> dict[str, Any]:
    if not settings.voice.enabled:
        raise HTTPException(status_code=503, detail="Voice chat is disabled")

    ended = voice_session_manager.end_session(session_id)
    if not ended:
        raise HTTPException(status_code=404, detail="Voice session not found")
    return {"status": "success", "session_id": session_id, "ended": True}


@app.get("/status")
def system_status() -> dict[str, Any]:
    scheduler_info = get_scheduler_status()
    return {
        "autonomous_agent": "ready",
        "scheduler_running": scheduler_info.get("running", False),
        "scheduler_jobs": scheduler_info.get("jobs", []),
        "message": "Kor'tana system operational",
    }


@app.post("/adapters/lobechat/chat")
async def lobechat_adapter(request: dict[str, Any]) -> dict[str, Any]:
    try:
        messages = request.get("messages", [])
        user_message = messages[-1].get("content", "") if messages else "Hello"
        response = chat_engine.get_response(user_message)
        return {"choices": [{"message": {"role": "assistant", "content": response}}]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
