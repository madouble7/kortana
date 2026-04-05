"""
kor'tana voice daemon — always-on voice interface

Wake phrase: say "kortana" (or a close mishear) anywhere in an utterance.
Flow:
  1. Continuously listen via microphone (VAD via speech_recognition)
  2. Wake phrase detected → Piper chime → listen for command
  3. faster-whisper large-v3 (CUDA) transcribes the command
  4. POST command to kor'tana backend → Piper/Cori speaks the response
  5. Return to listening

Run:  python c:\kortana\mcp-server\voice_daemon.py
Auto-start: registered via Task Scheduler (kortana-voice-daemon)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import faster_whisper
import httpx
import numpy as np
import sounddevice as sd
import speech_recognition as sr

# ── config ─────────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")
CHAT_ENDPOINT = f"{BACKEND_URL}/api/gemini/chat"
SESSION_ID = "voice"
LOG_FILE = Path(r"c:\kortana\logs\voice_daemon.log")

# Piper TTS paths — piper.exe is installed by piper-tts package
_PIPER_EXE_FOUND = shutil.which("piper") or shutil.which(
    r"C:\Users\madou\AppData\Roaming\Python\Python311\Scripts\piper.exe"
)
PIPER_EXE = (
    Path(_PIPER_EXE_FOUND)
    if _PIPER_EXE_FOUND
    else Path(r"c:\kortana\models\piper\piper.exe")
)
MODELS_DIR = Path(r"c:\kortana\models\piper")
CORI_MODEL = MODELS_DIR / "en_GB-cori-high.onnx"
CORI_SAMPLE_RATE = 22050
_PIPER_MODEL_URL_BASE = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/cori/high"
)

# Whisper model config — small runs on CPU in ~300ms
WHISPER_MODEL_SIZE = os.getenv("KORTANA_WHISPER_MODEL", "small")
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

# Phrases that trigger kor'tana (catches common STT mishearings)
WAKE_PHRASES = {
    "kortana",
    "kor'tana",
    "cortana",
    "cor tana",
    "corr tana",
    "kurtana",
    "her tana",
    "kourtana",
}

# How long to listen for a command after wake (seconds)
COMMAND_PHRASE_LIMIT = 15

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── globals ────────────────────────────────────────────────────────────────────
_speak_lock = threading.Lock()
_conversation_history: list[dict[str, str]] = []
_whisper: faster_whisper.WhisperModel | None = None
_last_interaction: float = time.time()  # updated on every voice exchange
_backend_was_up: bool = True  # tracks backend state transitions


# ── model bootstrap ────────────────────────────────────────────────────────────
def _download_piper_model() -> bool:
    """Download Piper voice model if not present. Returns True if available."""
    if CORI_MODEL.exists():
        return True
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    log("Downloading Piper voice model (~60 MB)...")
    try:
        with httpx.Client(timeout=180.0, follow_redirects=True) as client:
            for suffix in ("", ".json"):
                dest = Path(str(CORI_MODEL) + suffix) if suffix else CORI_MODEL
                url = f"{_PIPER_MODEL_URL_BASE}/{CORI_MODEL.name}{suffix}"
                r = client.get(url)
                if r.status_code != 200:
                    log(f"Piper download failed ({r.status_code}): {url}", "WARN")
                    return False
                dest.write_bytes(r.content)
                log(f"Downloaded {dest.name} ({len(r.content):,} bytes)")
        return True
    except Exception as e:
        log(f"Piper model download error: {e}", "WARN")
        return False


# ── history bootstrap ──────────────────────────────────────────────────────────
def _load_history_from_backend() -> list[dict[str, str]]:
    """Load recent voice conversation history from backend DB on startup.

    This is the cross-session memory bridge — without it every restart
    feels like a first meeting. With it, kor'tana picks up mid-thought.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(
                f"{BACKEND_URL}/api/gemini/chat/history",
                params={"session_id": SESSION_ID, "limit": 20},
            )
        if r.status_code == 200:
            messages = r.json().get("messages", [])
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in messages
                if m.get("role") in ("user", "assistant") and m.get("content")
            ]
            if history:
                log(f"Loaded {len(history)} messages from past session — memory intact")
            return history
    except Exception as e:
        log(f"Could not load past history (non-fatal): {e}", "WARN")
    return []


# ── logging ────────────────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── TTS ────────────────────────────────────────────────────────────────────────
def speak(text: str) -> None:
    """Speak text via Piper TTS (en_GB-cori-high neural voice)."""
    with _speak_lock:
        try:
            proc = subprocess.Popen(
                [str(PIPER_EXE), "--model", str(CORI_MODEL), "--output_raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            raw, _ = proc.communicate(input=text.encode("utf-8"), timeout=60)
            if raw:
                audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                sd.play(audio, samplerate=CORI_SAMPLE_RATE)
                sd.wait()
        except Exception as e:
            log(f"Piper speak error: {e} — falling back to SAPI", "WARN")
            _speak_sapi(text)
    log(f"spoke: {text[:80]}")


# ── STT ────────────────────────────────────────────────────────────────────────
def transcribe(audio: sr.AudioData, _recognizer: sr.Recognizer) -> str | None:
    """Transcribe audio with faster-whisper large-v3 on CUDA."""
    if _whisper is None:
        return None
    try:
        # Convert sr.AudioData → 16kHz float32 numpy array
        raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
        audio_np = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = _whisper.transcribe(
            audio_np, language="en", beam_size=5, vad_filter=True
        )
        text = " ".join(seg.text for seg in segments).strip().lower()
        return text if text else None
    except Exception as e:
        log(f"STT error: {e}", "WARN")
        return None


def _strip_wake(text: str) -> str:
    """Remove wake phrase from the start/end of transcription."""
    for phrase in sorted(WAKE_PHRASES, key=len, reverse=True):
        if text.startswith(phrase):
            return text[len(phrase) :].lstrip(" ,.")
        if text.endswith(phrase):
            return text[: -len(phrase)].rstrip(" ,.")
    return text


def _contains_wake(text: str) -> bool:
    return any(p in text for p in WAKE_PHRASES)


# ── episodic memory ────────────────────────────────────────────────────────────
_MEMORY_STORE = f"{BACKEND_URL}/api/consciousness/memory/self"
_memory_count = 0  # exchanges since last memory write
_MEMORY_EVERY = 3  # write a memory every N completed turns


def _write_episodic_memory(user_msg: str, assistant_reply: str) -> None:
    """Persist a compact episodic memory of this voice exchange to the DB.

    Runs in a daemon thread so it never blocks voice response.
    The memory gets picked up by MemoryPolicyService.build_context() and
    injected into future chat system prompts automatically.
    """
    try:
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        content = (
            f"[voice exchange — {ts}] "
            f'Matt said: "{user_msg[:200]}" | '
            f'kor\'tana replied: "{assistant_reply[:300]}"'
        )
        with httpx.Client(timeout=5.0) as client:
            client.post(
                _MEMORY_STORE,
                json={
                    "summary": content,
                    "tags": ["voice", "episodic"],
                    "source": "voice",
                },
            )
        log(f"[memory] wrote episodic entry ({len(content)} chars)")
    except Exception as e:
        log(f"[memory] write skipped: {e}", "WARN")


def _seed_identity_memory() -> None:
    """On first start with an empty DB, write a few foundational identity memories.

    These give kor'tana immediate self-knowledge without waiting for the
    Railway daemon to accumulate reflections.  Only written if the DB is empty.
    """
    try:
        r = httpx.get(
            f"{BACKEND_URL}/api/consciousness/memory/self",
            params={"source": "identity-seed"},
            timeout=5.0,
        )
        if r.status_code == 200 and r.json().get("count", 0) > 0:
            return  # already seeded — skip
    except Exception:
        return

    seeds = [
        (
            "kor'tana is an always-on AI companion built by Matt (madouble7). "
            "She runs as a voice daemon on his Windows machine, speaking via SAPI TTS "
            "and listening via Google STT. She is calm, reverent, decisive, and honest.",
            ["identity", "core"],
        ),
        (
            "Matt is kor'tana's primary human. He is building a JARVIS-like companion. "
            "He prefers direct, concise answers. He is budget-constrained and values "
            "free-tier infrastructure. He is spiritually grounded and values humility.",
            ["relationship", "matt"],
        ),
        (
            "kor'tana's voice session_id is 'voice'. She keeps the last 20 turns in "
            "local memory and writes episodic entries to the consciousness DB after "
            "every 3 voice exchanges. Past conversation history is loaded on startup.",
            ["system", "memory"],
        ),
    ]

    try:
        with httpx.Client(timeout=10.0) as client:
            for summary, tags in seeds:
                client.post(
                    _MEMORY_STORE,
                    json={"summary": summary, "tags": tags, "source": "identity-seed"},
                )
        log(f"[memory] seeded {len(seeds)} foundational identity memories")
    except Exception as e:
        log(f"[memory] seed failed: {e}", "WARN")


# ── backend chat ───────────────────────────────────────────────────────────────
def send_to_kortana(message: str) -> str:
    """Send message to kor'tana backend, return spoken response."""
    global _conversation_history, _memory_count
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
            # episodic memory — write every N turns without blocking
            _memory_count += 1
            if _memory_count % _MEMORY_EVERY == 0:
                threading.Thread(
                    target=_write_episodic_memory,
                    args=(message, response),
                    daemon=True,
                ).start()
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
    """Play a short Piper chime to signal kor'tana is listening."""
    _chime = "Yes?"
    try:
        proc = subprocess.Popen(
            [str(PIPER_EXE), "--model", str(CORI_MODEL), "--output_raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        raw, _ = proc.communicate(input=_chime.encode("utf-8"), timeout=10)
        if raw:
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            sd.play(audio, samplerate=CORI_SAMPLE_RATE)
            sd.wait()
    except Exception:
        pass  # non-critical


# ── main listen loop ───────────────────────────────────────────────────────────
def _handle_wake(recognizer: sr.Recognizer, text: str) -> None:
    """Called when wake phrase detected. text = full utterance including wake."""
    command = _strip_wake(text).strip()
    log(f"wake detected | raw='{text}' | command='{command}'")

    if not command:
        # No command in the same utterance — listen for it now.
        # Must use a fresh Microphone() — the shared mic is held open by the
        # background listener and cannot be re-entered from another thread.
        _play_activation_sound()
        try:
            follow_mic = sr.Microphone()
            with follow_mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
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
    global _last_interaction
    _last_interaction = time.time()


def _speak_sapi(text: str) -> None:
    """Fallback TTS via Windows SAPI if Piper binary or model is unavailable."""
    safe = text.replace("'", "''").replace('"', '`"')
    ps = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.Rate = 0
$s.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Female)
$s.Speak('{safe}')
"""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True,
            timeout=60,
        )
    except Exception as e:
        log(f"SAPI speak error: {e}", "WARN")


# ── proactive awareness ────────────────────────────────────────────────────────
def _proactive_loop() -> None:
    """Background thread — kor'tana watches for conditions worth speaking up about.

    Checks every 60 s:
    - Backend down → alert once per outage, clear when it recovers
    - No voice interaction for 2+ hours → a single check-in, then backs off
    - Morning greeting → once per day between 07:00-09:00 local time
    """
    global _backend_was_up, _last_interaction

    _checkin_done_hour: int = -1  # which hour we last did the 2h check-in
    _morning_greeted_date: str = ""  # YYYY-MM-DD we last greeted
    _backend_down_alerted: bool = False  # suppress duplicate down-alerts

    CHECKIN_INTERVAL = 2 * 3600  # 2 hours of silence before check-in
    POLL_INTERVAL = 60  # check every 60 seconds

    while True:
        time.sleep(POLL_INTERVAL)
        now = datetime.now()

        # ── 1. backend health ──────────────────────────────────────────────────
        try:
            with httpx.Client(timeout=4.0) as client:
                resp = client.get(f"{BACKEND_URL}/health")
            backend_up = resp.status_code < 500
        except Exception:
            backend_up = False

        if not backend_up and _backend_was_up:
            _backend_down_alerted = False  # reset so we alert once this outage

        if not backend_up and not _backend_down_alerted:
            log("[proactive] backend offline — alerting", "WARN")
            speak(
                "Heads up. My backend is offline. The local daemon should restart it shortly."
            )
            _backend_down_alerted = True

        if backend_up and not _backend_was_up:
            log("[proactive] backend recovered")
            speak("Backend is back online.")
            _backend_down_alerted = False

        _backend_was_up = backend_up

        # ── 2. session check-in after 2 h silence ─────────────────────────────
        silence = time.time() - _last_interaction
        if silence >= CHECKIN_INTERVAL and _checkin_done_hour != now.hour:
            _checkin_done_hour = now.hour
            hours = int(silence // 3600)
            log(f"[proactive] {hours}h silence — checking in")
            speak(
                f"You've been at it for a while — {hours} hours since we last spoke. "
                "Just checking in. I'm still here if you need me."
            )

        # ── 3. morning greeting ────────────────────────────────────────────────
        today = now.strftime("%Y-%m-%d")
        if 7 <= now.hour < 9 and _morning_greeted_date != today:
            _morning_greeted_date = today
            log("[proactive] morning greeting")
            speak(
                f"Good morning. It's {now.strftime('%-I %M %p')}. Ready when you are."
            )


def run() -> None:
    global _whisper

    # Download Piper model if missing (~60 MB, one-time)
    _download_piper_model()

    # Load Whisper on CPU with int8 quantization (~300ms/phrase)
    log(f"loading Whisper [{WHISPER_MODEL_SIZE}] on {WHISPER_DEVICE}...")
    _whisper = faster_whisper.WhisperModel(
        WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE
    )
    log("Whisper ready")

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

    # Seed foundational identity memories on first run (no-op if DB already has content)
    threading.Thread(target=_seed_identity_memory, daemon=True).start()

    # Restore cross-session memory before announcing readiness
    _conversation_history.extend(_load_history_from_backend())

    speak("kor'tana is ready. just say my name.")
    log("kor'tana voice daemon listening")

    # Proactive awareness — watches backend health, session length, morning greeting
    threading.Thread(target=_proactive_loop, daemon=True).start()

    # Background listener — callback fires on each detected phrase
    def _callback(recognizer: sr.Recognizer, audio: sr.AudioData) -> None:
        text = transcribe(audio, recognizer)
        if text and _contains_wake(text):
            # Spin off so background listener stays responsive
            threading.Thread(
                target=_handle_wake,
                args=(recognizer, text),
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
