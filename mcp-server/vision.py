r"""
kor'tana vision — continuous contextual screen awareness

Gives kor'tana the ability to see what Matt is working on.
Captures the screen periodically into a ring buffer and analyzes
on demand via Groq's vision model.

Architecture:
  1. Background thread captures screenshots every N seconds
  2. Ring buffer holds last K frames (default 5, ~10MB RAM)
  3. On-demand analysis: user asks "what's on my screen?" →
     latest frame sent to Groq vision model → spoken summary
  4. Diff-aware: can detect when the screen changes significantly

Privacy:
  - Captures are NEVER stored to disk
  - Frames live only in memory ring buffer
  - Analysis only runs when explicitly triggered by voice
  - No continuous vision model inference (too expensive)

Usage from voice_tools:
    from vision import get_latest_frame_b64, analyze_screen, start_capture, stop_capture
"""

from __future__ import annotations

import base64
import io
import os
import threading
import time
from collections import deque
from dataclasses import dataclass

import httpx

# ── optional imports ──────────────────────────────────────────────────────────
try:
    import mss
    import mss.tools

    _MSS_AVAILABLE = True
except ImportError:
    _MSS_AVAILABLE = False

try:
    from PIL import Image

    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


# ── configuration ─────────────────────────────────────────────────────────────
CAPTURE_INTERVAL = float(os.getenv("KORTANA_VISION_INTERVAL", "5"))  # seconds
BUFFER_SIZE = int(os.getenv("KORTANA_VISION_BUFFER", "5"))  # frames to keep
JPEG_QUALITY = int(os.getenv("KORTANA_VISION_QUALITY", "60"))  # JPEG quality
MAX_DIMENSION = int(os.getenv("KORTANA_VISION_MAX_DIM", "1280"))  # max px
# Groq vision model — llama-3.2-11b for speed, 90b for detail
VISION_MODEL = os.getenv(
    "KORTANA_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"
)


@dataclass
class Frame:
    """A captured screen frame."""

    timestamp: float
    jpeg_b64: str  # base64-encoded JPEG
    width: int
    height: int


# ── ring buffer ───────────────────────────────────────────────────────────────
_buffer: deque[Frame] = deque(maxlen=BUFFER_SIZE)
_capture_thread: threading.Thread | None = None
_capture_stop = threading.Event()
_capture_running = False


def _log(msg: str) -> None:
    """Simple log — matches voice_daemon format."""
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{ts}] [INFO] [vision] {msg}", flush=True)


# ── screen capture ────────────────────────────────────────────────────────────
def _capture_frame() -> Frame | None:
    """Capture the primary monitor and return a compressed JPEG frame."""
    if not _MSS_AVAILABLE:
        return None

    try:
        with mss.mss() as sct:
            # Capture primary monitor
            monitor = sct.monitors[1]  # 0 = all monitors, 1 = primary
            raw = sct.grab(monitor)

        if not _PIL_AVAILABLE:
            # Fallback: use mss raw bytes (no compression)
            png_bytes = mss.tools.to_png(raw.rgb, raw.size)
            b64 = base64.b64encode(png_bytes).decode("ascii")
            return Frame(
                timestamp=time.time(),
                jpeg_b64=b64,
                width=raw.width,
                height=raw.height,
            )

        # Convert to PIL for compression and resizing
        img = Image.frombytes("RGB", raw.size, raw.rgb)

        # Resize if too large (saves bandwidth to vision model)
        w, h = img.size
        if max(w, h) > MAX_DIMENSION:
            ratio = MAX_DIMENSION / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

        # Compress to JPEG
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        jpeg_bytes = buf.getvalue()
        b64 = base64.b64encode(jpeg_bytes).decode("ascii")

        return Frame(
            timestamp=time.time(),
            jpeg_b64=b64,
            width=img.size[0],
            height=img.size[1],
        )

    except Exception as e:
        _log(f"capture failed: {e}")
        return None


def _capture_loop() -> None:
    """Background capture loop — runs in a daemon thread."""
    global _capture_running
    _capture_running = True
    _log(f"capture started (interval={CAPTURE_INTERVAL}s, buffer={BUFFER_SIZE})")

    while not _capture_stop.is_set():
        frame = _capture_frame()
        if frame:
            _buffer.append(frame)
        _capture_stop.wait(timeout=CAPTURE_INTERVAL)

    _capture_running = False
    _log("capture stopped")


def start_capture() -> None:
    """Start the background screen capture thread."""
    global _capture_thread
    if _capture_thread and _capture_thread.is_alive():
        return  # already running

    if not _MSS_AVAILABLE:
        _log("mss not installed — vision disabled")
        return

    _capture_stop.clear()
    _capture_thread = threading.Thread(
        target=_capture_loop, daemon=True, name="vision-capture"
    )
    _capture_thread.start()


def stop_capture() -> None:
    """Stop the background capture thread."""
    _capture_stop.set()
    if _capture_thread:
        _capture_thread.join(timeout=5)


def is_capturing() -> bool:
    """Check if capture is running."""
    return _capture_running


# ── frame access ──────────────────────────────────────────────────────────────
def get_latest_frame() -> Frame | None:
    """Get the most recent captured frame."""
    if _buffer:
        return _buffer[-1]
    return None


def get_latest_frame_b64() -> str | None:
    """Get the base64-encoded JPEG of the latest frame."""
    frame = get_latest_frame()
    return frame.jpeg_b64 if frame else None


def get_frame_age() -> float | None:
    """How many seconds ago was the latest frame captured?"""
    frame = get_latest_frame()
    if frame:
        return time.time() - frame.timestamp
    return None


# ── vision analysis via Groq ─────────────────────────────────────────────────
def analyze_screen(
    question: str = "Describe what you see on this screen. Focus on code, errors, terminal output, or anything the user might need help with.",
    frame: Frame | None = None,
) -> str:
    """Send the latest screenshot to Groq's vision model for analysis.

    Args:
        question: What to ask about the screen content.
        frame: Specific frame to analyze. If None, uses latest from buffer.

    Returns:
        Text description of what's on screen.
    """
    if frame is None:
        frame = get_latest_frame()
    if frame is None:
        # Try a one-shot capture
        frame = _capture_frame()
    if frame is None:
        return "I can't see your screen right now. Make sure screen capture is running."

    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        return "I don't have an API key configured for vision analysis."

    age = time.time() - frame.timestamp
    age_note = f" (captured {age:.0f}s ago)" if age > 2 else ""

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}"},
                json={
                    "model": VISION_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        f"{question}\n\n"
                                        "Respond in 2-3 short sentences optimized for speech. "
                                        "No markdown, no code blocks, no bullet lists. "
                                        "Be specific about what you see — file names, error messages, "
                                        "line numbers, terminal commands."
                                    ),
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{frame.jpeg_b64}",
                                    },
                                },
                            ],
                        }
                    ],
                    "max_tokens": 200,
                    "temperature": 0.2,
                },
            )

        if resp.status_code != 200:
            error = resp.text[:200]
            return f"Vision analysis failed with status {resp.status_code}. {error}"

        content = resp.json()["choices"][0]["message"]["content"].strip()
        return content + age_note

    except httpx.TimeoutException:
        return "Vision analysis timed out. The image might be too large."
    except Exception as e:
        return f"Vision analysis error: {e}"


def analyze_for_errors() -> str:
    """Specifically look for errors, warnings, or failures on screen."""
    return analyze_screen(
        "Look at this screenshot carefully. Are there any error messages, "
        "red highlights, failed tests, stack traces, or warnings visible? "
        "If yes, describe them specifically. If the screen looks normal, say so."
    )


def read_screen_text() -> str:
    """Extract and read back visible text from the screen."""
    return analyze_screen(
        "Read the visible text on this screen. Focus on: "
        "code in the editor, terminal output, error messages, "
        "or any dialog boxes. Summarize what you see."
    )


def describe_code_on_screen() -> str:
    """Describe the code currently visible in the editor."""
    return analyze_screen(
        "Describe the code visible in the editor. What file is open? "
        "What language is it? What does the visible code do? "
        "Are there any obvious issues or patterns worth noting?"
    )
