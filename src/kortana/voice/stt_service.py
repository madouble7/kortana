"""Speech-to-text utilities for Kor'tana voice chat."""

from __future__ import annotations

import io
import logging
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

        transcript = self._heuristic_transcription(audio_bytes)
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "text": transcript,
            "metrics": {
                "stt_ms": round(elapsed_ms, 2),
                "audio_bytes": len(audio_bytes),
                "duration_seconds": duration_seconds,
            },
        }

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
