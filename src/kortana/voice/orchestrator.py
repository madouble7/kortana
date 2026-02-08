"""Voice chat orchestration pipeline."""

from __future__ import annotations

import base64
import time
from typing import Any, Protocol

from .errors import VoiceProcessingError
from .stt_service import STTService
from .tts_service import TTSService
from .voice_session import VoiceSessionManager


class ChatEngineProtocol(Protocol):
    async def process_message(
        self,
        user_message: str,
        user_id: str | None = None,
        user_name: str | None = None,
        channel: str = "default",
    ) -> str: ...


class VoiceChatOrchestrator:
    """Coordinates STT -> ChatEngine -> TTS for voice conversations."""

    def __init__(
        self,
        chat_engine: ChatEngineProtocol,
        stt_service: STTService | None = None,
        tts_service: TTSService | None = None,
        session_manager: VoiceSessionManager | None = None,
        session_idle_seconds: int = 1800,
        max_active_sessions: int = 1000,
    ):
        self.chat_engine = chat_engine
        self.stt = stt_service or STTService()
        self.tts = tts_service or TTSService()
        self.sessions = session_manager or VoiceSessionManager()
        self.session_idle_seconds = session_idle_seconds
        self.max_active_sessions = max_active_sessions

    def _prune_sessions(self) -> int:
        return self.sessions.cleanup_inactive(
            max_idle_seconds=self.session_idle_seconds,
            max_active_sessions=self.max_active_sessions,
        )

    async def transcribe_only(
        self,
        audio_bytes: bytes,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        sessions_reaped = self._prune_sessions()
        session = self.sessions.get_or_create(session_id=session_id, user_id=user_id)
        stt_result = self.stt.transcribe(audio_bytes)
        self.sessions.mark_turn(session.session_id)
        session_snapshot = self.sessions.get_snapshot(session.session_id)

        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "session": session_snapshot,
            "transcript": stt_result["text"],
            "metrics": {**stt_result["metrics"], "sessions_reaped": sessions_reaped},
        }

    async def process_voice_turn(
        self,
        audio_bytes: bytes,
        session_id: str | None = None,
        user_id: str | None = None,
        user_name: str | None = None,
        return_audio: bool = True,
    ) -> dict[str, Any]:
        total_start = time.perf_counter()
        sessions_reaped = self._prune_sessions()
        session = self.sessions.get_or_create(session_id=session_id, user_id=user_id)

        stt_result = self.stt.transcribe(audio_bytes)
        transcript = stt_result["text"]

        llm_start = time.perf_counter()
        response_text = await self.chat_engine.process_message(
            transcript,
            user_id=session.user_id,
            user_name=user_name,
            channel="voice",
        )
        llm_ms = (time.perf_counter() - llm_start) * 1000

        tts_metrics: dict[str, Any] = {}
        response_audio_b64 = None
        if return_audio:
            try:
                tts_result = self.tts.synthesize(response_text)
                tts_metrics = tts_result["metrics"]
                response_audio_b64 = base64.b64encode(tts_result["audio_bytes"]).decode(
                    "utf-8"
                )
            except VoiceProcessingError:
                raise
            except Exception as exc:
                # Graceful fallback to text response if synthesis fails.
                tts_metrics = {
                    "tts_fallback": True,
                    "tts_error": str(exc),
                }

        self.sessions.mark_turn(session.session_id)
        session_snapshot = self.sessions.get_snapshot(session.session_id)
        total_ms = (time.perf_counter() - total_start) * 1000

        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "session": session_snapshot,
            "transcript": transcript,
            "response": response_text,
            "response_audio_base64": response_audio_b64,
            "metrics": {
                **stt_result["metrics"],
                **tts_metrics,
                "sessions_reaped": sessions_reaped,
                "llm_ms": round(llm_ms, 2),
                "total_ms": round(total_ms, 2),
            },
        }
