"""voice websocket — full-duplex streaming audio for kor'tana voice interface.

Architecture:
  Client streams raw 16kHz mono float32 audio frames UP via WebSocket.
  Server runs Silero VAD → Whisper STT → Groq LLM → edge-tts.
  Server streams TTS audio chunks DOWN as they're generated.
  Barge-in: when server detects speech during TTS playback, it stops TTS
  and begins processing the new utterance immediately.

Protocol (JSON messages):
  Client → Server:
    {"type": "audio", "data": "<base64 float32 16kHz mono>"}
    {"type": "config", "sample_rate": 16000}
    {"type": "interrupt"}   — explicit barge-in from client

  Server → Client:
    {"type": "transcript", "text": "...", "final": true}
    {"type": "audio", "data": "<base64 mp3 chunk>", "sentence": "..."}
    {"type": "status", "speaking": true/false}
    {"type": "thinking"}   — LLM is generating
"""

from __future__ import annotations

import base64
import io
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.kortana.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

_GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL = "llama-3.3-70b-versatile"
_SYSTEM_PROMPT = (
    "You are kor'tana, a calm, warm AI companion. "
    "Respond in 1-2 short sentences optimized for speech. "
    "No markdown, no code blocks, no bullet lists, no asterisks. "
    "Be warm, direct, and concise. Sound natural."
)


@router.websocket("/stream")
async def voice_stream(websocket: WebSocket) -> None:
    """Full-duplex voice WebSocket — streams audio both directions."""
    await websocket.accept()
    logger.info("Voice WebSocket client connected")

    conversation: list[dict[str, str]] = []

    try:
        while True:
            msg = await websocket.receive_json()
            msg_type = msg.get("type", "")

            if msg_type == "chat":
                # Text-based chat (fallback when client does its own STT)
                text = msg.get("text", "").strip()
                if not text:
                    continue

                await websocket.send_json({"type": "thinking"})

                # Stream LLM response and TTS audio back
                await _stream_response(websocket, text, conversation)

            elif msg_type == "interrupt":
                await websocket.send_json({"type": "status", "speaking": False})

            elif msg_type == "audio":
                # Binary audio frame — client sends base64-encoded audio
                audio_b64 = msg.get("data", "")
                if audio_b64:
                    # Decode and process (future: server-side VAD + STT)
                    pass

    except WebSocketDisconnect:
        logger.info("Voice WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass


async def _stream_response(
    websocket: WebSocket,
    text: str,
    conversation: list[dict[str, str]],
) -> None:
    """Stream Groq LLM response and generate TTS audio per sentence."""
    import httpx

    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        await websocket.send_json(
            {
                "type": "audio_text",
                "text": "I can't reach any AI provider right now.",
            }
        )
        return

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    for h in conversation[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": text})

    full_response = ""
    sentence_buffer = ""

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            async with client.stream(
                "POST",
                _GROQ_API_URL,
                headers={"Authorization": f"Bearer {groq_key}"},
                json={
                    "model": _GROQ_MODEL,
                    "messages": messages,
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "stream": True,
                },
            ) as response:
                if response.status_code != 200:
                    await websocket.send_json(
                        {
                            "type": "audio_text",
                            "text": "I'm having trouble connecting.",
                        }
                    )
                    return

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break

                    try:
                        import json

                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        token = delta.get("content", "")
                    except Exception:
                        continue

                    if not token:
                        continue

                    full_response += token
                    sentence_buffer += token

                    # Send transcript incrementally
                    await websocket.send_json(
                        {
                            "type": "transcript",
                            "text": full_response,
                            "final": False,
                        }
                    )

                    # Check for sentence boundary
                    if _is_sentence_end(sentence_buffer):
                        sentence = sentence_buffer.strip()
                        if sentence:
                            # Generate TTS audio for this sentence
                            audio_b64 = await _generate_tts_audio(sentence)
                            if audio_b64:
                                await websocket.send_json(
                                    {
                                        "type": "audio",
                                        "data": audio_b64,
                                        "sentence": sentence,
                                    }
                                )
                        sentence_buffer = ""

    except Exception as e:
        logger.error(f"Groq stream error: {e}")

    # Speak remaining buffer
    if sentence_buffer.strip():
        audio_b64 = await _generate_tts_audio(sentence_buffer.strip())
        if audio_b64:
            await websocket.send_json(
                {
                    "type": "audio",
                    "data": audio_b64,
                    "sentence": sentence_buffer.strip(),
                }
            )

    # Final transcript
    await websocket.send_json(
        {
            "type": "transcript",
            "text": full_response,
            "final": True,
        }
    )

    # Update conversation history
    conversation.append({"role": "user", "content": text})
    conversation.append({"role": "assistant", "content": full_response})
    if len(conversation) > 20:
        del conversation[: len(conversation) - 20]

    await websocket.send_json({"type": "status", "speaking": False})


async def _generate_tts_audio(text: str) -> str | None:
    """Generate TTS audio for a sentence and return base64-encoded mp3."""
    try:
        import edge_tts  # type: ignore[import-untyped]
    except ImportError:
        return None

    try:
        rate, pitch = _detect_prosody(text)
        comm = edge_tts.Communicate(text, "en-GB-SoniaNeural", rate=rate, pitch=pitch)
        buf = io.BytesIO()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        data = buf.getvalue()
        if data:
            return base64.b64encode(data).decode("ascii")
    except Exception as e:
        logger.error(f"TTS error: {e}")
    return None


def _detect_prosody(text: str) -> tuple[str, str]:
    """Analyze text for emotional prosody — mirrors voice_daemon logic."""

    text_stripped = text.strip()
    lower = text.lower()
    words = set(lower.split())

    warmth = {
        "love",
        "glad",
        "happy",
        "wonderful",
        "beautiful",
        "proud",
        "grateful",
        "blessed",
        "joy",
        "peace",
        "grace",
        "faith",
    }
    concern = {
        "sorry",
        "unfortunately",
        "careful",
        "warning",
        "worried",
        "difficult",
        "struggle",
        "hard",
        "pain",
        "hurt",
    }

    if text_stripped.endswith("?"):
        return "+5%", "+3Hz"
    if text_stripped.endswith("!"):
        return "+15%", "+2Hz"
    if words & warmth:
        return "+8%", "+1Hz"
    if words & concern:
        return "-5%", "-2Hz"
    if len(text.split()) < 5:
        return "+12%", "+0Hz"
    return "+10%", "+0Hz"


def _is_sentence_end(text: str) -> bool:
    """Check if buffer ends at a sentence boundary."""
    text = text.rstrip()
    if not text:
        return False
    if text[-1] in ".!?":
        if len(text) >= 3 and text[-2].isupper() and text[-3] == " ":
            return False
        return True
    return False
