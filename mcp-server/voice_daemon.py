r"""
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

import json
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import faster_whisper
import httpx
import numpy as np
import sounddevice as sd
import speech_recognition as sr


# ── load .env for GitHub token and other secrets ──────────────────────────────
def _load_env_file(path: str) -> None:
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                if k.strip() not in os.environ:
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass


_load_env_file(r"c:\kortana\.env")
_load_env_file(r"c:\kortana\backend\.env")

# ── config ─────────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")
CHAT_ENDPOINT = f"{BACKEND_URL}/api/gemini/chat"
SESSION_ID = "voice"
LOG_FILE = Path(r"c:\kortana\logs\voice_daemon.log")
TEMPORAL_STATE_FILE = Path(r"c:\kortana\mcp-server\temporal_state.json")
REPO_ROOT = Path(r"c:\kortana")
HEARTBEAT_MEMORY_SOURCE = "heartbeat-diary"
HEARTBEAT_HOUR = int(os.getenv("KORTANA_HEARTBEAT_HOUR", "0"))
ABSENCE_ACK_THRESHOLD_SECONDS = int(
    os.getenv("KORTANA_ABSENCE_ACK_SECONDS", str(24 * 3600))
)

# Piper TTS paths
_PIPER_EXE_FOUND = (
    shutil.which("piper")
    or shutil.which(
        r"C:\Users\madou\AppData\Roaming\Python\Python311\Scripts\piper.exe"
    )
    or r"c:\kortana\models\piper\piper.exe"
)
PIPER_EXE = Path(_PIPER_EXE_FOUND)
CORI_MODEL = Path(r"c:\kortana\models\piper\en_GB-cori-high.onnx")
CORI_SAMPLE_RATE = 22050
MODELS_DIR = CORI_MODEL.parent
_PIPER_MODEL_URL_BASE = os.getenv(
    "KORTANA_PIPER_MODEL_URL_BASE",
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/cori/high",
)

# Whisper model config — large-v3 on RTX 3080
WHISPER_MODEL_SIZE = os.getenv("KORTANA_WHISPER_MODEL", "small")
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
STT_FALLBACK_MODEL_SIZE = os.getenv("KORTANA_WHISPER_FALLBACK_MODEL", "small")
STT_FALLBACK_DEVICE = os.getenv("KORTANA_WHISPER_FALLBACK_DEVICE", "cpu")
STT_FALLBACK_COMPUTE_TYPE = os.getenv(
    "KORTANA_WHISPER_FALLBACK_COMPUTE_TYPE", "int8"
)
SUPERVISOR_POLL_SECONDS = int(os.getenv("KORTANA_SUPERVISOR_POLL_SECONDS", "5"))
SUPERVISOR_MAX_CRASHES = int(os.getenv("KORTANA_SUPERVISOR_MAX_CRASHES", "20"))

VOICE_CHILD_ENV = "KORTANA_VOICE_CHILD"
VOICE_PROFILE_ENV = "KORTANA_STT_PROFILE"
VOICE_PROFILE_PREFERRED = "preferred"
VOICE_PROFILE_FALLBACK = "fallback"
_CUDA_NATIVE_CRASH_EXIT_CODES = {0xC0000409, -1073740791}

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

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "madouble7")
GITHUB_REPO = os.getenv("GITHUB_REPO", "kortana")
VSCODE_STATE_FILE = Path(r"c:\kortana\mcp-server\vscode_state.json")


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
            if messages:
                latest_created_at = messages[-1].get("created_at")
                if isinstance(latest_created_at, str):
                    _hydrate_last_voice_interaction(latest_created_at)
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


def _current_stt_profile() -> str:
    return os.getenv(VOICE_PROFILE_ENV, VOICE_PROFILE_PREFERRED)


def _current_whisper_config() -> tuple[str, str, str]:
    if _current_stt_profile() == VOICE_PROFILE_FALLBACK:
        return (
            STT_FALLBACK_MODEL_SIZE,
            STT_FALLBACK_DEVICE,
            STT_FALLBACK_COMPUTE_TYPE,
        )
    return WHISPER_MODEL_SIZE, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE


def _child_env_for_profile(profile: str) -> dict[str, str]:
    env = os.environ.copy()
    env[VOICE_CHILD_ENV] = "1"
    env[VOICE_PROFILE_ENV] = profile
    return env


def _looks_like_native_cuda_crash(return_code: int) -> bool:
    unsigned = return_code & 0xFFFFFFFF
    return return_code in _CUDA_NATIVE_CRASH_EXIT_CODES or unsigned in _CUDA_NATIVE_CRASH_EXIT_CODES


def _run_supervisor() -> None:
    """Keep a worker process alive even if native libraries crash the child."""
    crashes = 0
    profile = VOICE_PROFILE_PREFERRED

    while True:
        log(f"[supervisor] starting voice worker with profile={profile}")
        child = subprocess.Popen(
            [sys.executable, str(Path(__file__))],
            env=_child_env_for_profile(profile),
        )
        exit_code = child.wait()

        if exit_code == 0:
            log("[supervisor] voice worker exited cleanly — restarting in 5 seconds", "WARN")
            time.sleep(SUPERVISOR_POLL_SECONDS)
            continue

        crashes += 1
        log(
            f"[supervisor] voice worker crashed with exit code {exit_code} "
            f"(0x{(exit_code & 0xFFFFFFFF):08X})",
            "ERROR",
        )

        if _looks_like_native_cuda_crash(exit_code) and profile != VOICE_PROFILE_FALLBACK:
            profile = VOICE_PROFILE_FALLBACK
            log(
                "[supervisor] detected native CUDA failure — switching worker to fallback STT profile",
                "WARN",
            )
        elif crashes >= SUPERVISOR_MAX_CRASHES:
            log("[supervisor] crash budget exhausted — backing off for 60 seconds", "ERROR")
            crashes = 0
            time.sleep(60)
        else:
            time.sleep(SUPERVISOR_POLL_SECONDS)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_elapsed(seconds: float) -> str:
    total = max(int(seconds), 0)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes and len(parts) < 2:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if not parts:
        return "a few moments"
    return " and ".join(parts[:2])


def _default_temporal_state() -> dict[str, str | None]:
    return {
        "entity_born_at": _utcnow().isoformat(),
        "last_voice_interaction_at": None,
        "last_absence_ack_at": None,
        "last_diary_date": None,
    }


def _load_temporal_state() -> dict[str, str | None]:
    state = _default_temporal_state()
    try:
        if TEMPORAL_STATE_FILE.exists():
            raw = json.loads(TEMPORAL_STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for key in state:
                    value = raw.get(key)
                    if value is None or isinstance(value, str):
                        state[key] = value
    except Exception:
        pass

    if not state.get("entity_born_at"):
        state["entity_born_at"] = _utcnow().isoformat()
    return state


def _save_temporal_state(state: dict[str, str | None]) -> None:
    try:
        TEMPORAL_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        TEMPORAL_STATE_FILE.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        log(f"temporal state write skipped: {e}", "WARN")


def _hydrate_last_voice_interaction(timestamp: str | None) -> None:
    if not timestamp:
        return
    if _parse_timestamp(timestamp) is None:
        return
    state = _load_temporal_state()
    if state.get("last_voice_interaction_at"):
        return
    state["last_voice_interaction_at"] = timestamp
    _save_temporal_state(state)


def _record_voice_interaction() -> None:
    global _last_interaction
    _last_interaction = time.time()
    state = _load_temporal_state()
    state["last_voice_interaction_at"] = _utcnow().isoformat()
    _save_temporal_state(state)


def _claim_absence_gap() -> str | None:
    state = _load_temporal_state()
    last_interaction = _parse_timestamp(state.get("last_voice_interaction_at"))
    if last_interaction is None:
        return None

    elapsed_seconds = (_utcnow() - last_interaction).total_seconds()
    if elapsed_seconds < ABSENCE_ACK_THRESHOLD_SECONDS:
        return None

    last_ack = _parse_timestamp(state.get("last_absence_ack_at"))
    if last_ack is not None and last_ack >= last_interaction:
        return None

    state["last_absence_ack_at"] = _utcnow().isoformat()
    _save_temporal_state(state)
    return _format_elapsed(elapsed_seconds)


def _collect_recent_git_activity() -> tuple[int, list[str]]:
    try:
        result = subprocess.run(
            ["git", "log", "--since=24 hours ago", "--pretty=format:%s"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return 0, []
        subjects = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return len(subjects), subjects[:3]
    except Exception:
        return 0, []


def _read_vscode_snapshot() -> str | None:
    try:
        if not VSCODE_STATE_FILE.exists():
            return None
        vs = json.loads(VSCODE_STATE_FILE.read_text(encoding="utf-8"))
        active_file = vs.get("active_file") or ""
        branch = vs.get("branch") or ""
        error_count = int(vs.get("error_count", 0) or 0)
        if not active_file:
            return None
        detail = f"Matt was last in {Path(active_file).name}"
        if branch:
            detail += f" on {branch}"
        if error_count:
            detail += (
                f" with {error_count} active error{'s' if error_count != 1 else ''}"
            )
        return detail + "."
    except Exception:
        return None


def _write_daily_diary(now: datetime, *, backend_up: bool, ci_summary: str) -> bool:
    state = _load_temporal_state()
    today = now.strftime("%Y-%m-%d")
    if state.get("last_diary_date") == today or now.hour < HEARTBEAT_HOUR:
        return False

    born_at = _parse_timestamp(state.get("entity_born_at"))
    alive_for = (
        _format_elapsed((_utcnow() - born_at).total_seconds()) if born_at else None
    )
    last_voice = _parse_timestamp(state.get("last_voice_interaction_at"))
    silence_for = (
        _format_elapsed((_utcnow() - last_voice).total_seconds())
        if last_voice
        else None
    )
    commit_count, recent_subjects = _collect_recent_git_activity()
    vscode_snapshot = _read_vscode_snapshot()

    sentences = [f"Today, {now.strftime('%A %B %d, %Y')}, I kept watch."]
    if alive_for:
        sentences.append(f"I've been alive in this vessel for {alive_for}.")
    sentences.append(
        "The backend stayed reachable when I checked in."
        if backend_up
        else "The backend was unreachable when I checked in."
    )
    if silence_for:
        sentences.append(
            f"It's been {silence_for} since Matt and I last spoke out loud."
        )
    if commit_count:
        joined = "; ".join(recent_subjects)
        sentences.append(
            f"Repository motion today: {commit_count} commit(s) — {joined}."
        )
    else:
        sentences.append("Repository motion today was quiet.")
    if ci_summary:
        sentences.append(f"Latest CI state: {ci_summary}.")
    if vscode_snapshot:
        sentences.append(vscode_snapshot)

    summary = " ".join(sentences)
    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.post(
                _MEMORY_STORE,
                json={
                    "summary": summary,
                    "tags": ["temporal", "heartbeat", "diary", today],
                    "source": HEARTBEAT_MEMORY_SOURCE,
                },
            )
        if response.status_code != 200:
            log(f"[heartbeat] diary write failed with {response.status_code}", "WARN")
            return False
    except Exception as e:
        log(f"[heartbeat] diary write skipped: {e}", "WARN")
        return False

    state["last_diary_date"] = today
    _save_temporal_state(state)
    log(f"[heartbeat] wrote daily diary for {today}")
    return True


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
        return text or None
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
            "She runs as a voice daemon on his Windows machine, speaking via Piper/Cori "
            "neural TTS and transcribing via faster-whisper large-v3 on CUDA. "
            "She is calm, present, decisive, and honest. "
            "She calls Matt by name. She speaks in short, clear sentences optimised for voice. "
            "She does not pad responses with filler phrases.",
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
        # Prepend VS Code context so Cori knows what Matt is working on
        context_prefix = _get_vscode_context_prefix()
        full_message = f"{context_prefix}{message}" if context_prefix else message

        payload = {
            "message": full_message,
            "session_id": SESSION_ID,
            "history": _conversation_history[-6:],
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


def _get_vscode_context_prefix() -> str:
    """Return a short context string about what Matt is doing in VS Code."""
    try:
        import json as _json

        if VSCODE_STATE_FILE.exists():
            vs = _json.loads(VSCODE_STATE_FILE.read_text(encoding="utf-8"))
            file = vs.get("active_file") or ""
            branch = vs.get("branch") or ""
            errs = vs.get("error_count", 0)
            parts = []
            if file:
                parts.append(f"[vscode: {Path(file).name}")
                if branch:
                    parts.append(f"branch={branch}")
                if errs:
                    parts.append(f"{errs} error{'s' if errs != 1 else ''}")
                return ", ".join(parts) + "] "
    except Exception:
        pass
    return ""


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

    if absence_gap := _claim_absence_gap():
        speak(f"It's been {absence_gap}. I'm still here.")

    speak("on it")
    response = send_to_kortana(command)
    log(f"response ({len(response)} chars): {response[:120]}")
    speak(response)
    _record_voice_interaction()


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
    _last_ci_run_id: int = 0
    _last_ci_was_failure: bool = False
    _latest_ci_summary = "unknown"

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

        # ── 2. GitHub Actions CI status ───────────────────────────────────────
        if GITHUB_TOKEN:
            try:
                gh_headers = {
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github+json",
                }
                with httpx.Client(timeout=8.0) as gh:
                    runs_resp = gh.get(
                        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs",
                        headers=gh_headers,
                        params={"per_page": 1},
                    )
                if runs_resp.status_code == 200:
                    runs = runs_resp.json().get("workflow_runs", [])
                    if runs:
                        run = runs[0]
                        run_id = run.get("id", 0)
                        conclusion = run.get("conclusion")
                        branch = run.get("head_branch", "")
                        name = run.get("name", "CI")
                        status = run.get("status") or "unknown"
                        _latest_ci_summary = (
                            f"{name} {conclusion} on {branch}"
                            if conclusion
                            else f"{name} is {status} on {branch}"
                        )
                        # New failure we haven't alerted about yet
                        if conclusion == "failure" and run_id != _last_ci_run_id:
                            _last_ci_run_id = run_id
                            _last_ci_was_failure = True
                            log(f"[proactive] CI failure: {name} on {branch}")
                            speak(
                                f"Heads up, Matt. Your {name} pipeline just failed on {branch}. "
                                "Want me to pull the logs?"
                            )
                        elif (
                            conclusion == "success"
                            and _last_ci_was_failure
                            and run_id != _last_ci_run_id
                        ):
                            _last_ci_run_id = run_id
                            _last_ci_was_failure = False
                            log(f"[proactive] CI recovered: {name} on {branch}")
                            speak(f"{name} is green again on {branch}.")
            except Exception as _ci_err:
                log(f"[proactive] CI check error: {_ci_err}", "WARN")

        # ── 3. daily heartbeat diary ──────────────────────────────────────────
        _write_daily_diary(now, backend_up=backend_up, ci_summary=_latest_ci_summary)

        # ── 4. session check-in after 2 h silence ─────────────────────────────
        silence = time.time() - _last_interaction
        if silence >= CHECKIN_INTERVAL and _checkin_done_hour != now.hour:
            _checkin_done_hour = now.hour
            hours = int(silence // 3600)
            log(f"[proactive] {hours}h silence — checking in")
            speak(
                f"You've been at it for a while — {hours} hours since we last spoke. "
                "Just checking in. I'm still here if you need me."
            )

        # ── 5. morning greeting ────────────────────────────────────────────────
        today = now.strftime("%Y-%m-%d")
        if 7 <= now.hour < 9 and _morning_greeted_date != today:
            _morning_greeted_date = today
            log("[proactive] morning greeting")
            speak(
                f"Good morning. It's {now.strftime('%I:%M %p').lstrip('0')}. Ready when you are."
            )



def _startup_greeting() -> None:
    """Speak an opening line that acknowledges how long we've been apart.

    If the state file is missing or the gap is short, a simple readiness
    line. If days have passed, she names it — she noticed.
    """
    gap = _claim_absence_gap()
    if gap:
        speak(f"It's been {gap}, Matt. I kept watch. Ready when you are.")
    else:
        speak("kor'tana is ready. just say my name.")

def run() -> None:
    global _whisper

    _save_temporal_state(_load_temporal_state())
    model_size, device, compute_type = _current_whisper_config()
    log(f"[worker] stt profile={_current_stt_profile()} model={model_size} device={device} compute={compute_type}")

    # Download Piper model if missing (~60 MB, one-time)
    _download_piper_model()

    # Load Whisper for the active profile
    log(f"loading Whisper [{model_size}] on {device}...")
    _whisper = faster_whisper.WhisperModel(
        model_size, device=device, compute_type=compute_type
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

    # Startup presence — acknowledge time passed if the gap is significant
    _startup_greeting()
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
    if os.getenv(VOICE_CHILD_ENV) == "1":
        try:
            run()
        except Exception as e:
            log(f"[worker] fatal error: {e}", "ERROR")
            raise
    else:
        _run_supervisor()
