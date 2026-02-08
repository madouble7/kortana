"""Speech-to-text utilities for Kor'tana voice chat."""

from __future__ import annotations

import io
import logging
import os
import time
import wave
from dataclasses import dataclass
from typing import Any

from .errors import VoiceProcessingError

logger = logging.getLogger(__name__)


@dataclass
class STTConfig:
    max_audio_bytes: int = 10 * 1024 * 1024
    min_audio_seconds: float = 0.15
    silence_ratio_threshold: float = 0.98
    provider: str = "openai"
    fallback_provider: str = "heuristic"
    openai_model: str = "whisper-1"


class STTService:
    """Lightweight STT abstraction with validation and latency metrics."""

    def __init__(self, config: STTConfig | None = None):
        self.config = config or STTConfig()

    def transcribe(self, audio_bytes: bytes) -> dict[str, Any]:
        start = time.perf_counter()
        self._validate_audio(audio_bytes)

        duration_seconds = self._estimate_duration_seconds(audio_bytes)
        if (
            duration_seconds is not None
            and duration_seconds < self.config.min_audio_seconds
        ):
            raise VoiceProcessingError(
                code="audio_too_short",
                message="Audio is too short to transcribe reliably.",
                details={"duration_seconds": duration_seconds},
                status_code=422,
            )

        if self._is_mostly_silence(audio_bytes):
            raise VoiceProcessingError(
                code="silence_detected",
                message="No speech detected in audio.",
                status_code=422,
            )

        transcript, provider_used = self._transcribe_with_provider(audio_bytes)
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "text": transcript,
            "metrics": {
                "stt_ms": round(elapsed_ms, 2),
                "audio_bytes": len(audio_bytes),
                "duration_seconds": duration_seconds,
                "stt_provider": provider_used,
            },
        }

    def _transcribe_with_provider(self, audio_bytes: bytes) -> tuple[str, str]:
        provider = (self.config.provider or "heuristic").lower()

        if provider == "openai":
            try:
                return self._openai_transcription(audio_bytes), "openai"
            except Exception as exc:
                logger.warning("OpenAI STT failed; attempting fallback: %s", exc)
                fallback = (self.config.fallback_provider or "heuristic").lower()
                if fallback == "heuristic":
                    return self._heuristic_transcription(audio_bytes), "heuristic_fallback"
                raise VoiceProcessingError(
                    code="stt_provider_failed",
                    message="Primary and fallback STT providers failed.",
                    details={"provider": provider, "fallback": fallback},
                    status_code=502,
                ) from exc

        return self._heuristic_transcription(audio_bytes), "heuristic"

    def _openai_transcription(self, audio_bytes: bytes) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise VoiceProcessingError(
                code="openai_key_missing",
                message="OPENAI_API_KEY is required for OpenAI STT provider.",
                status_code=503,
            )

        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "voice.wav"
            response = client.audio.transcriptions.create(
                model=self.config.openai_model,
                file=audio_file,
            )
            text = getattr(response, "text", None) or ""
            text = text.strip()
            if not text:
                raise VoiceProcessingError(
                    code="empty_transcript",
                    message="STT provider returned an empty transcript.",
                    status_code=502,
                )
            return text
        except VoiceProcessingError:
            raise
        except Exception as exc:
            raise VoiceProcessingError(
                code="openai_stt_error",
                message="OpenAI STT request failed.",
                details={"error": str(exc)},
                status_code=502,
            ) from exc

    def _validate_audio(self, audio_bytes: bytes) -> None:
        if not audio_bytes:
            raise VoiceProcessingError(
                code="empty_audio",
                message="No audio payload was provided.",
                status_code=400,
            )
        if len(audio_bytes) > self.config.max_audio_bytes:
            raise VoiceProcessingError(
                code="audio_too_large",
                message="Audio payload exceeds size limit.",
                details={"max_audio_bytes": self.config.max_audio_bytes},
                status_code=413,
            )

    def _estimate_duration_seconds(self, audio_bytes: bytes) -> float | None:
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate() or 1
                return frames / float(rate)
        except Exception:
            return None

    def _is_mostly_silence(self, audio_bytes: bytes) -> bool:
        if not audio_bytes:
            return True
        zero_like = sum(1 for b in audio_bytes if b in (0, 127, 128, 255))
        return (zero_like / len(audio_bytes)) >= self.config.silence_ratio_threshold

    def _heuristic_transcription(self, audio_bytes: bytes) -> str:
        """Fallback transcription when no external STT model is configured."""
        try:
            decoded = audio_bytes.decode("utf-8", errors="ignore").strip()
            if decoded.startswith("TEXT:"):
                text = decoded[5:].strip()
                return text or "I shared a voice note."
            if decoded and len(decoded.split()) >= 2:
                return decoded[:500]
        except Exception as exc:
            logger.debug("Heuristic decode failed: %s", exc)

        return "I shared a voice message."
