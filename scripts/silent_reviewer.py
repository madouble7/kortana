#!/usr/bin/env python3
"""Silent Reviewer — kor'tana's autonomous daemon loop.

Single source of truth for all self-generated activity:
  - Observation gathering
  - Revelation synthesis
  - Wisdom distillation & prediction
  - Self-model evolution (Inner Council deliberation)

Runs continuously on a configurable interval (default 18 min).
Uses SHA-256 fingerprinting to skip cycles when nothing meaningful
has changed.  Calls the Autonomy Orchestrator internal endpoint
which handles the full observe→reflect→synthesize→persist pipeline.
"""

import hashlib
import logging
import os
import subprocess
import time

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")
CYCLE_INTERVAL_SECONDS = int(os.getenv("KORTANA_CYCLE_INTERVAL", "1080"))  # 18 min
REPO_ROOT = os.getenv(
    "KORTANA_REPO_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)

AUTONOMY_CYCLE_URL = f"{BACKEND_URL}/api/consciousness/_internal/autonomy-cycle"
MEMORY_URL = f"{BACKEND_URL}/api/consciousness/memory/self"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SilentReviewer] %(levelname)s  %(message)s",
)
log = logging.getLogger("silent_reviewer")

# ---------------------------------------------------------------------------
# Fingerprint — determines if a new cycle is warranted
# ---------------------------------------------------------------------------
_last_fingerprint: str | None = None


def _compute_fingerprint() -> str:
    """SHA-256 of HEAD commit + memory count + timestamp bucket (18 min)."""
    parts: list[str] = []

    # Git HEAD
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            timeout=5,
            text=True,
        ).strip()
        parts.append(head)
    except Exception:
        parts.append("no-git")

    # Memory count (cheap GET)
    try:
        resp = httpx.get(MEMORY_URL, params={"limit": 1}, timeout=5.0)
        resp.raise_for_status()
        count = resp.json().get("count", 0)
        parts.append(str(count))
    except Exception:
        parts.append("0")

    # Time bucket (rounds to interval)
    bucket = int(time.time()) // CYCLE_INTERVAL_SECONDS
    parts.append(str(bucket))

    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _has_meaningful_change() -> bool:
    """Return True if the fingerprint differs from last cycle."""
    global _last_fingerprint
    fp = _compute_fingerprint()
    if fp == _last_fingerprint:
        log.info("Fingerprint unchanged (%s) — skipping cycle.", fp)
        return False
    _last_fingerprint = fp
    return True


# ---------------------------------------------------------------------------
# Orchestrator trigger
# ---------------------------------------------------------------------------
def trigger_autonomy_cycle() -> dict | None:
    """POST to the Autonomy Orchestrator internal endpoint.

    This single call executes the full pipeline:
      observe → reflect → distill wisdom → predict → evolve self-model.
    """
    try:
        resp = httpx.post(AUTONOMY_CYCLE_URL, timeout=120.0)
        resp.raise_for_status()
        data = resp.json()
        log.info(
            "Autonomy cycle complete — self-model v%s, stage=%s, duration=%sms",
            data.get("self_model_version", "?"),
            data.get("developmental_stage", "?"),
            data.get("duration_ms", "?"),
        )
        return data
    except httpx.ConnectError:
        log.warning("Backend not reachable — skipping cycle.")
        return None
    except Exception as e:
        log.error("Autonomy cycle failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Main daemon loop
# ---------------------------------------------------------------------------
def run_cycle() -> None:
    """Execute one iteration of the Silent Reviewer."""
    if not _has_meaningful_change():
        return
    log.info("Meaningful change detected — initiating autonomy cycle.")
    trigger_autonomy_cycle()


def main() -> None:
    """Continuous daemon loop."""
    log.info(
        "Silent Reviewer awakening. Cycle interval: %ds. Repo: %s",
        CYCLE_INTERVAL_SECONDS,
        REPO_ROOT,
    )
    while True:
        try:
            run_cycle()
        except KeyboardInterrupt:
            log.info("Interrupted — shutting down gracefully.")
            break
        except Exception as e:
            log.error("Unexpected error in cycle: %s", e)
        time.sleep(CYCLE_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
