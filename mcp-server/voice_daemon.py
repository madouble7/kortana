"""
kor'tana voice daemon — always-on voice interface

Wake phrase: say "kortana" (or a close mishear) anywhere in an utterance.
Flow:
  1. Continuously listen via microphone (Google STT on detected speech)
  2. Wake phrase detected → say "yes?" → listen for command
  3. POST command to kor'tana backend → speak response via Windows SAPI
  4. Return to listening

Run:  python c:\kortana\mcp-server\voice_daemon.py
Auto-start: registered via Task Scheduler (kortana-voice-daemon)
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import httpx
import pyttsx3
import speech_recognition as sr

# ── config ─────────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")
CHAT_ENDPOINT = f"{BACKEND_URL}/api/gemini/chat"
SESSION_ID = "voice"
LOG_FILE = Path(r"c:\kortana\logs\voice_daemon.log")

# Phrases that trigger kor'tana (catches common STT mishearings)
WAKE_PHRASES = {
    "kortana", "kor'tana", "cortana",
    "cor tana", "corr tana", "kurtana",
    "her tana", "kourtana",
}

# How long to listen for a command after wake (seconds)
COMMAND_TIMEOUT = 8
COMMAND_PHRASE_LIMIT = 15

# pyttsx3 voice rate (words per minute). 175 = natural pace.
TTS_RATE = int(os.getenv("KORTANA_TTS_RATE", "175"))
# Voice index: 0 = first installed voice, typically Zira (female) on Windows 11
TTS_VOICE_INDEX = int(os.getenv("KORTANA_VOICE_INDEX", "0"))

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── globals ────────────────────────────────────────────────────────────────────
_speak_lock = threading.Lock()
_tts_engine: pyttsx3.Engine | None = None
_conversation_history: list[dict[str, str]] = []


# ── logging ────────────────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── TTS ────────────────────────────────────────────────────────────────────────
def _init_tts() -> pyttsx3.Engine:
    engine = pyttsx3.init()
    engine.setProperty("rate", TTS_RATE)
    voices = engine.getProperty("voices")
    if voices and TTS_VOICE_INDEX < len(voices):
        engine.setProperty("voice", voices[TTS_VOICE_INDEX].id)
    return engine


def speak(text: str) -> None:
    """Speak text aloud via Windows SAPI, thread-safe."""
    global _tts_engine
    with _speak_lock:
        if _tts_engine is None:
            _tts_engine = _init_tts()
        # reinitialize if the engine was stopped
        try:
            _tts_engine.say(text)
            _tts_engine.runAndWait()
        except Exception:
            _tts_engine = _init_tts()
            _tts_engine.say(text)
            _tts_engine.runAndWait()
    log(f"spoke: {text[:80]}")


# ── STT ────────────────────────────────────────────────────────────────────────
def transcribe(audio: sr.AudioData, recognizer: sr.Recognizer) -> str | None:
    """Transcribe audio. Returns lowercase text or None on failure."""
    try:
        return recognizer.recognize_google(audio).lower()
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        log(f"STT request error: {e}", "WARN")
        return None


def _strip_wake(text: str) -> str:
    """Remove wake phrase from the start/end of transcription."""
    for phrase in sorted(WAKE_PHRASES, key=len, reverse=True):
        if text.startswith(phrase):
            return text[len(phrase):].lstrip(" ,.")
        if text.endswith(phrase):
            return text[: -len(phrase)].rstrip(" ,.")
    return text


def _contains_wake(text: str) -> bool:
    return any(p in text for p in WAKE_PHRASES)


# ── backend chat ───────────────────────────────────────────────────────────────
def send_to_kortana(message: str) -> str:
    """Send message to kor'tana backend, return spoken response."""
    global _conversation_history
    try:
        payload = {
            "message": message,
            "session_id": SESSION_ID,
            "history": _conversation_history[-6:],  # last 3 turns context
        }
        with httpx.Client(timeout=30.0) as client:
            r = client.post(CHAT_ENDPOINT, json=payload)
        if r.status_code == 200:
            data = r.json()
            response = data.get("response") or data.get("text") or str(data)
            # trim markdown for speech
            response = _clean_for_speech(response)
            # update history
            _conversation_history.append({"role": "user", "content": message})
            _conversation_history.append({"role": "assistant", "content": response})
            if len(_conversation_history) > 20:
                _conversation_history = _conversation_history[-20:]
            return response
        else:
            log(f"Backend returned {r.status_code}: {r.text[:200]}", "WARN")
            return "I encountered an issue reaching my backend. I'm still here though."
    except httpx.ConnectError:
        log("Backend unreachable", "WARN")
        return "My backend is offline right now. You can still use me through VS Code."
    except Exception as e:
        log(f"Chat error: {e}", "ERROR")
        return "Something went wrong on my end."


def _clean_for_speech(text: str) -> str:
    """Strip markdown and trim to a speakable length."""
    import re
    # Remove code blocks entirely
    text = re.sub(r"```[\s\S]*?```", "[code block]", text)
    # Remove inline code
    text = re.sub(r"`[^`]+`", lambda m: m.group(0)[1:-1], text)
    # Remove markdown links
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Remove bold/italic markers
    text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)
    # Remove headers
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)
    # Collapse blank lines
    text = re.sub(r"\n{2,}", "\n", text).strip()
    # Trim to ~600 chars (~45 seconds of speech) for voice
    if len(text) > 600:
        text = text[:600].rsplit(".", 1)[0] + ". There's more if you'd like."
    return text


# ── activation sound ───────────────────────────────────────────────────────────
def _play_activation_sound() -> None:
    """Play a short beep to signal kor'tana is listening for the command."""
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "[console]::beep(880, 120); Start-Sleep -Milliseconds 50; [console]::beep(1100, 120)"],
        capture_output=True, timeout=3,
    )


# ── main listen loop ───────────────────────────────────────────────────────────
def _handle_wake(recognizer: sr.Recognizer, mic: sr.Microphone, text: str) -> None:
    """Called when wake phrase detected. text = full utterance including wake."""
    command = _strip_wake(text).strip()
    log(f"wake detected | raw='{text}' | command='{command}'")

    if not command:
        # No command in the same utterance — listen for it now
        _play_activation_sound()
        try:
            with mic as source:
                log("listening for command…")
                audio = recognizer.listen(
                    source,
                    timeout=3,
                    phrase_time_limit=COMMAND_PHRASE_LIMIT,
                )
            command = transcribe(audio, recognizer) or ""
            log(f"command heard: '{command}'")
        except sr.WaitTimeoutError:
            speak("I'm here.")
            return

    if not command:
        speak("I didn't catch that — try again.")
        return

    speak("on it")
    response = send_to_kortana(command)
    log(f"response ({len(response)} chars): {response[:120]}")
    speak(response)


def run() -> None:
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8  # seconds of silence = end of phrase
    recognizer.energy_threshold = 300

    mic = sr.Microphone()

    # Calibrate to ambient noise once at startup
    log("calibrating to ambient noise…")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.5)
    log(f"energy threshold set to {recognizer.energy_threshold:.0f}")

    speak("kor'tana is ready. just say my name.")
    log("kor'tana voice daemon listening")

    # Background listener — callback fires on each detected phrase
    def _callback(recognizer: sr.Recognizer, audio: sr.AudioData) -> None:
        text = transcribe(audio, recognizer)
        if text and _contains_wake(text):
            # Spin off so background listener stays responsive
            threading.Thread(
                target=_handle_wake,
                args=(recognizer, mic, text),
                daemon=True,
            ).start()

    stop = recognizer.listen_in_background(
        mic, _callback, phrase_time_limit=COMMAND_PHRASE_LIMIT
    )

    log("background listener active — press Ctrl+C to stop")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        log("shutting down voice daemon")
        stop(wait_for_stop=False)
        speak("going quiet now.")


if __name__ == "__main__":
    run()
