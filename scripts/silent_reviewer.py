#!/usr/bin/env python3
"""
KOR'TANA Silent Reviewer — Autonomous Wisdom Pipeline

The single source of truth for all autonomous synthesis cycles.
Wisdom distillation and prediction are NEVER triggered via API —
they run exclusively through this daemon loop.

On each iteration:
  1. Detect meaningful change (new commits, new memories, new revelations)
  2. Gather telemetry / git / SelfMemory context
  3. Store a structured reflection
  4. Trigger revelation synthesis (obeys internal cooldown)
  5. If meaningful change detected → distill wisdom + predict evolution
  6. Sleep for SILENT_REVIEWER_INTERVAL_MINUTES (default: 18)

AUTONOMY.lock acts as a kill switch — if present, the loop halts immediately.

Usage:
    python scripts/silent_reviewer.py              # continuous loop (default)
    python scripts/silent_reviewer.py --once        # single pass then exit
"""

import hashlib
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
LOCK_FILE = REPO_ROOT / "AUTONOMY.lock"
STATE_FILE = REPO_ROOT / ".silent_reviewer_state"
BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")
LOOP_INTERVAL_MINUTES = int(os.getenv("SILENT_REVIEWER_INTERVAL_MINUTES", "18"))
LOOP_INTERVAL_SECONDS = LOOP_INTERVAL_MINUTES * 60
HTTP_TIMEOUT = 10.0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [silent-reviewer] %(levelname)s %(message)s",
)
logger = logging.getLogger("silent-reviewer")


# ---------------------------------------------------------------------------
# Kill switch
# ---------------------------------------------------------------------------
def is_killed() -> bool:
    """Return True if AUTONOMY.lock exists — operator pulled the plug."""
    if LOCK_FILE.exists():
        logger.warning("AUTONOMY.lock detected — halting.")
        return True
    return False


# ---------------------------------------------------------------------------
# Change detection (intelligent throttling)
# ---------------------------------------------------------------------------
def _compute_fingerprint() -> str:
    """Build a fingerprint of current state: HEAD sha + recent memory count + recent rev count.

    If this fingerprint differs from the last stored one, meaningful change has occurred.
    """
    parts: list[str] = []

    # Git HEAD
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=5,
        )
        parts.append(result.stdout.strip())
    except Exception:
        parts.append("no-git")

    # Count of recent memories (proxy for new telemetry)
    try:
        resp = httpx.get(
            f"{BACKEND_URL}/api/consciousness/memory/stats",
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        parts.append(str(resp.json().get("count", 0)))
    except Exception:
        parts.append("0")

    # Count of unsurfaced revelations
    try:
        resp = httpx.get(
            f"{BACKEND_URL}/api/consciousness/memory/revelations",
            params={"limit": 1, "unsurfaced_only": True},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        parts.append(str(resp.json().get("count", 0)))
    except Exception:
        parts.append("0")

    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def has_meaningful_change() -> bool:
    """Compare current fingerprint against last stored state.

    Returns True on first run (no state file) or when fingerprint differs.
    """
    current = _compute_fingerprint()

    previous = ""
    if STATE_FILE.exists():
        try:
            previous = STATE_FILE.read_text().strip()
        except Exception:
            pass

    if current != previous:
        try:
            STATE_FILE.write_text(current)
        except Exception:
            pass
        return True

    logger.info("No meaningful change since last cycle — skipping distillation.")
    return False


# ---------------------------------------------------------------------------
# Data gathering
# ---------------------------------------------------------------------------
def gather_memories(limit: int = 50) -> list:
    """Fetch recent SelfMemory entries from the consciousness API."""
    try:
        resp = httpx.get(
            f"{BACKEND_URL}/api/consciousness/memory/self",
            params={"limit": limit},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("memories", [])
    except Exception as exc:
        logger.error(f"Memory fetch failed: {exc}")
        return []


def gather_unsurfaced_revelations(limit: int = 10) -> list:
    """Fetch unsurfaced revelations for synthesis context."""
    try:
        resp = httpx.get(
            f"{BACKEND_URL}/api/consciousness/memory/revelations",
            params={"limit": limit, "unsurfaced_only": True},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("revelations", [])
    except Exception as exc:
        logger.error(f"Revelation fetch failed: {exc}")
        return []


def gather_recent_git(limit: int = 20) -> list[str]:
    """Get recent git log entries from the local repo."""
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={limit}", "--oneline"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception as exc:
        logger.error(f"Git log failed: {exc}")
        return []


# ---------------------------------------------------------------------------
# Synthesis
# ---------------------------------------------------------------------------
def synthesize_reflection(
    memories: list, revelations: list, git_log: list
) -> str | None:
    """Build a structured reflection from recent observations."""
    if not memories and not revelations and not git_log:
        return None

    parts = ["### Silent Reflection"]

    if memories:
        tags_seen: set[str] = set()
        for m in memories:
            for t in m.get("tags", []):
                tags_seen.add(t)
        parts.append(
            f"- Observed {len(memories)} memories spanning tags: {', '.join(sorted(tags_seen))}"
        )

    if revelations:
        parts.append(f"- {len(revelations)} unsurfaced revelations awaiting synthesis")
        for r in revelations[:3]:
            parts.append(
                f"  - [{r.get('revelation_type', '?')}] {r.get('title', 'untitled')}"
            )

    if git_log:
        parts.append(f"- {len(git_log)} recent commits observed")
        for line in git_log[:5]:
            parts.append(f"  - {line}")

    parts.append(
        "\nSynthesizing patterns silently. Wisdom will emerge through the autonomous loop."
    )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Store reflection
# ---------------------------------------------------------------------------
def store_reflection(content: str) -> None:
    """Write the reflection to SelfMemory via the consciousness API."""
    try:
        httpx.post(
            f"{BACKEND_URL}/api/consciousness/memory/self",
            json={
                "summary": content,
                "tags": ["reflection", "self-evolution", "background", "phase4"],
                "source": "silent-reviewer",
            },
            timeout=HTTP_TIMEOUT,
        )
        logger.info("Reflection stored.")
    except Exception as exc:
        logger.error(f"Reflection store failed: {exc}")


# ---------------------------------------------------------------------------
# Trigger revelation synthesis
# ---------------------------------------------------------------------------
def trigger_revelation_cycle(force: bool = False) -> dict | None:
    """POST to the revelation synthesis endpoint (cooldown enforced server-side)."""
    try:
        resp = httpx.post(
            f"{BACKEND_URL}/api/consciousness/memory/revelation",
            json={"force": force},
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        n = data.get("revelations_written", 0)
        if n:
            logger.info(f"Revelation cycle: {n} new revelations")
        return data
    except Exception as exc:
        logger.error(f"Revelation trigger failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Autonomous wisdom & prediction (direct engine calls via internal API)
# ---------------------------------------------------------------------------
def trigger_wisdom_distillation() -> dict | None:
    """Call the internal wisdom distillation endpoint.

    This is the ONLY path through which wisdom is generated.
    The consciousness router exposes read-only access.
    """
    try:
        resp = httpx.post(
            f"{BACKEND_URL}/api/consciousness/_internal/wisdom-cycle",
            timeout=90.0,
        )
        resp.raise_for_status()
        data = resp.json()
        w = data.get("wisdom_entries", 0)
        p = data.get("predictions_generated", 0)
        if w or p:
            logger.info(f"Autonomous cycle: {w} wisdom, {p} predictions")
        return data
    except Exception as exc:
        logger.error(f"Wisdom/prediction cycle failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def run_cycle() -> None:
    """Execute one full autonomous review cycle."""
    if is_killed():
        return

    logger.info("Cycle start — gathering observations...")

    # 1. Gather context
    memories = gather_memories()
    revelations = gather_unsurfaced_revelations()
    git_log = gather_recent_git()

    if is_killed():
        return

    # 2. Synthesize and store reflection
    reflection = synthesize_reflection(memories, revelations, git_log)
    if reflection:
        store_reflection(reflection)

    if is_killed():
        return

    # 3. Trigger revelation engine (obeys cooldown internally)
    trigger_revelation_cycle()

    if is_killed():
        return

    # 4. Phase 4: autonomous wisdom distillation + prediction
    #    Only run if meaningful change detected (new commits, memories, revelations)
    if has_meaningful_change():
        trigger_wisdom_distillation()
    else:
        logger.info("Skipping wisdom cycle — no meaningful change.")

    logger.info("Cycle complete.")


def main() -> None:
    """Entry point — continuous loop by default, --once for single pass."""
    single_pass = "--once" in sys.argv

    if single_pass:
        logger.info("Single pass mode")
        run_cycle()
        logger.info("Done.")
    else:
        logger.info(
            f"Autonomous loop starting (interval={LOOP_INTERVAL_MINUTES}m / {LOOP_INTERVAL_SECONDS}s)"
        )
        while not is_killed():
            run_cycle()
            if is_killed():
                break
            logger.info(f"Sleeping {LOOP_INTERVAL_MINUTES}m...")
            time.sleep(LOOP_INTERVAL_SECONDS)
        logger.info("Loop terminated.")


if __name__ == "__main__":
    main()
