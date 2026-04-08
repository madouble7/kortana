"""voice router — text-to-speech via edge-tts (free, no api key required).

provides a streaming audio endpoint so the frontend can play kor'tana's
spoken responses with zero cost and high quality neural voices.
voice parameters evolve over time based on conversational mood.
"""

import io
from typing import Any

import edge_tts
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.kortana.logger import get_logger
from src.kortana.services.proactive_presence import consume_pending_presence
from src.kortana.services.voice_evolution import evolve_voice, get_voice_profile

router = APIRouter()
logger = get_logger(__name__)

# --------------------------------------------------------------------------- #
# voice configuration
# --------------------------------------------------------------------------- #

# Microsoft Edge neural voices — all free, no API key.
# en-US-AriaNeural is an adult woman, warm and expressive — kor'tana's voice.
# (AnaNeural sounds too young/childlike)
DEFAULT_VOICE = "en-US-AriaNeural"

# Speed/pitch tweaks for naturalness.  edge-tts uses SSML-style rate strings.
DEFAULT_RATE = "-5%"  # slightly slower than default for presence
DEFAULT_PITCH = "-2Hz"  # slightly lower for warmth

ALLOWED_VOICES: set[str] = {
    "en-US-AnaNeural",
    "en-US-AriaNeural",
    "en-US-JennyNeural",
    "en-GB-SoniaNeural",
    "en-GB-LibbyNeural",
}


# --------------------------------------------------------------------------- #
# POST /api/voice/speak — stream TTS audio for a text payload
# --------------------------------------------------------------------------- #


@router.post("/speak")
async def speak(payload: dict[str, Any]) -> StreamingResponse:
    """Convert text to speech and stream mp3 audio back to the client.

    Payload:
        text (str): The text to speak.
        voice (str, optional): Edge TTS voice name.  Defaults to en-US-AnaNeural.
        rate (str, optional): Speech rate adjustment (e.g. "-10%", "+5%").
        pitch (str, optional): Pitch adjustment (e.g. "+2Hz", "-1Hz").
    """
    text = payload.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' field")

    voice = payload.get("voice", DEFAULT_VOICE)
    if voice not in ALLOWED_VOICES:
        voice = DEFAULT_VOICE

    rate = payload.get("rate", DEFAULT_RATE)
    pitch = payload.get("pitch", DEFAULT_PITCH)

    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)

    # Collect audio into a buffer — edge-tts yields small chunks, and
    # streaming them one-by-one causes choppy playback on the frontend.
    buffer = io.BytesIO()
    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
    except Exception as exc:
        logger.error("edge-tts synthesis failed: %s", exc)
        raise HTTPException(status_code=502, detail="Voice synthesis failed") from exc

    if buffer.tell() == 0:
        raise HTTPException(status_code=502, detail="No audio produced")

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=kortana_speech.mp3",
            "Cache-Control": "no-cache",
        },
    )


# --------------------------------------------------------------------------- #
# GET /api/voice/voices — list available voices
# --------------------------------------------------------------------------- #


@router.get("/voices")
async def list_voices() -> dict[str, Any]:
    """Return the set of allowed TTS voices and the current default."""
    return {
        "default": DEFAULT_VOICE,
        "voices": sorted(ALLOWED_VOICES),
    }


# --------------------------------------------------------------------------- #
# GET /api/voice/profile — current evolved voice state
# --------------------------------------------------------------------------- #


@router.get("/profile")
async def voice_profile() -> dict[str, Any]:
    """Return the current voice evolution profile including mood and TTS params."""
    profile = get_voice_profile()
    return {
        "mood": profile.get("mood", "neutral"),
        "rate": profile.get("rate", DEFAULT_RATE),
        "pitch": profile.get("pitch", DEFAULT_PITCH),
        "interactions": profile.get("interactions_count", 0),
        "mood_history": profile.get("mood_history", [])[-5:],
    }


# --------------------------------------------------------------------------- #
# POST /api/voice/evolve — analyze user message and evolve voice params
# --------------------------------------------------------------------------- #


@router.post("/evolve")
async def evolve(payload: dict[str, Any]) -> dict[str, Any]:
    """Analyze a user message and return evolved voice parameters.

    Payload:
        text (str): The user's message to analyze.
        hour (int, optional): Current hour (0-23) for time-of-day awareness.
    """
    user_text = payload.get("text", "")
    hour = payload.get("hour")
    return evolve_voice(user_text, hour=hour)


# --------------------------------------------------------------------------- #
# GET /api/voice/presence — poll for proactive reach-out messages
# --------------------------------------------------------------------------- #


@router.get("/presence")
async def presence() -> dict[str, Any]:
    """Check if kor'tana has a proactive message for matt.

    Returns the pending message if one exists, or null.
    Frontend polls this on an interval (e.g. every 30s).
    """
    msg = consume_pending_presence()
    return {"presence": msg}


# --------------------------------------------------------------------------- #
# POST /api/voice/action — execute a voice command
# --------------------------------------------------------------------------- #


@router.post("/action")
async def voice_action(payload: dict[str, Any]) -> dict[str, Any]:
    """Process a voice command from matt.

    Detects intent from natural language and executes the corresponding action.

    Args:
        text (str): The voice command text to process.
    """
    from src.kortana.services.intent_executor import process_voice_command

    user_text = payload.get("text", "")
    result = await process_voice_command(user_text)
    return {"action_result": result}


# --------------------------------------------------------------------------- #
# GET /api/voice/dreams — consume prepared thoughts from dream state
# --------------------------------------------------------------------------- #


@router.get("/dreams")
async def voice_dreams() -> dict[str, Any]:
    """Get thoughts kor'tana prepared while matt was away.

    Returns and clears any dream-state observations.
    """
    from src.kortana.services.dream_state import consume_prepared_thoughts

    thoughts = consume_prepared_thoughts()
    return {"dreams": thoughts}


# --------------------------------------------------------------------------- #
# GET /api/voice/identity — identity evolution summary
# --------------------------------------------------------------------------- #


@router.get("/identity")
async def voice_identity() -> dict[str, Any]:
    """Get kor'tana's current identity evolution state.

    Returns personality dimensions, growth areas, and evolution narrative.
    """
    from src.kortana.services.identity_evolution import (
        generate_identity_narrative,
        get_evolution_summary,
    )

    summary = get_evolution_summary()
    narrative = generate_identity_narrative()
    return {
        "evolution": summary,
        "narrative": narrative,
    }
