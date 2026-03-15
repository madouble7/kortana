"""Text-to-speech utilities for Kor'tana voice chat."""

from __future__ import annotations

import io
import math
import os
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
    provider: str = "pyttsx3"
    fallback_provider: str = "tone"
    voice_name: str | None = None
    rate: int = 170
    volume: float = 0.95


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
        audio_bytes, provider_used = self._synthesize_with_provider(text)
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "audio_bytes": audio_bytes,
            "metrics": {
                "tts_ms": round(elapsed_ms, 2),
                "audio_bytes": len(audio_bytes),
                "tts_provider": provider_used,
            },
        }

    def _synthesize_with_provider(self, text: str) -> tuple[bytes, str]:
        provider = (self.config.provider or "tone").lower()

        if provider == "pyttsx3":
            try:
                return self._synthesize_pyttsx3(text), "pyttsx3"
            except Exception as exc:
                fallback = (self.config.fallback_provider or "tone").lower()
                if fallback == "tone":
                    return self._generate_placeholder_wav(), "tone_fallback"
                raise VoiceProcessingError(
                    code="tts_provider_failed",
                    message="Primary and fallback TTS providers failed.",
                    details={"provider": provider, "fallback": fallback, "error": str(exc)},
                    status_code=502,
                ) from exc

        return self._generate_placeholder_wav(), "tone"

    def _synthesize_pyttsx3(self, text: str) -> bytes:
        try:
            import pyttsx3

            # pyttsx3 writes to a file; use a short-lived path.
            output_path = "data/processed/kortana_tts_output.wav"
            os.makedirs("data/processed", exist_ok=True)
            engine = pyttsx3.init()
            engine.setProperty("rate", self.config.rate)
            engine.setProperty("volume", self.config.volume)

            if self.config.voice_name:
                for voice in engine.getProperty("voices"):
                    if self.config.voice_name.lower() in voice.name.lower():
                        engine.setProperty("voice", voice.id)
                        break

            engine.save_to_file(text, output_path)
            engine.runAndWait()

            with open(output_path, "rb") as f:
                return f.read()
        except Exception as exc:
            raise VoiceProcessingError(
                code="pyttsx3_error",
                message="pyttsx3 synthesis failed.",
                details={"error": str(exc)},
                status_code=502,
            ) from exc

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
