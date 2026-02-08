"""Text-to-speech utilities for Kor'tana voice chat."""

from __future__ import annotations

import io
import math
import struct
import time
import wave
from dataclasses import dataclass
from typing import Any

from .errors import VoiceProcessingError


@dataclass
class TTSConfig:
    sample_rate: int = 16000
    tone_hz: int = 220
    duration_seconds: float = 0.35


class TTSService:
    """Lightweight TTS abstraction with deterministic audio generation fallback."""

    def __init__(self, config: TTSConfig | None = None):
        self.config = config or TTSConfig()

    def synthesize(self, text: str) -> dict[str, Any]:
        if not text or not text.strip():
            raise VoiceProcessingError(
                code="empty_tts_text",
                message="Cannot synthesize empty text.",
                status_code=422,
            )

        start = time.perf_counter()
        audio_bytes = self._generate_placeholder_wav()
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "audio_bytes": audio_bytes,
            "metrics": {
                "tts_ms": round(elapsed_ms, 2),
                "audio_bytes": len(audio_bytes),
            },
        }

    def _generate_placeholder_wav(self) -> bytes:
        sample_rate = self.config.sample_rate
        total_frames = int(sample_rate * self.config.duration_seconds)
        amplitude = 5000

        frames = bytearray()
        for i in range(total_frames):
            value = int(
                amplitude
                * math.sin(2 * math.pi * self.config.tone_hz * i / sample_rate)
            )
            frames.extend(struct.pack("<h", value))

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(bytes(frames))
        return buffer.getvalue()
