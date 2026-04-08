"""ambient dev awareness — kor'tana sees what matt is building.

extends the VS Code telemetry (current_focus.json) into actionable awareness:
  - tracks file changes and git diffs in real-time
  - detects build failures, test results, type errors
  - generates proactive dev insights when patterns emerge
  - understands the shape of the current work session

she doesn't just respond to code questions — she sees the code changing.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.kortana.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(r"c:\kortana")
FOCUS_FILE = Path(r"c:\kortana\mcp-server\current_focus.json")

# how many cycles between deep awareness scans
AWARENESS_SCAN_INTERVAL = 10  # every ~10 minutes
_cycles_since_last_scan = 0

# in-memory dev state
_dev_state: dict[str, Any] = {
    "active_file": None,
    "branch": None,
    "recent_changes": [],      # list of recently changed files
    "uncommitted_files": [],   # git status
    "recent_errors": [],       # detected errors/friction
    "session_files": [],       # files touched this session
    "last_scan": None,
}


def get_dev_state() -> dict[str, Any]:
    """return the current dev awareness state."""
    return dict(_dev_state)


# ---------------------------------------------------------------------------
# git integration — see what's changing
# ---------------------------------------------------------------------------


def _git_output(cmd: list[str]) -> str | None:
    """run a git command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def scan_git_state() -> dict[str, Any]:
    """scan current git state — branch, uncommitted changes, recent commits."""
    state: dict[str, Any] = {}

    # current branch
    branch = _git_output(["rev-parse", "--abbrev-ref", "HEAD"])
    state["branch"] = branch

    # uncommitted changes
    status = _git_output(["status", "--porcelain"])
    if status:
        changed_files = []
        for line in status.strip().split("\n"):
            if line.strip():
                # format: "XY filename"
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    changed_files.append({
                        "status": parts[0],
                        "file": parts[1],
                    })
        state["uncommitted"] = changed_files
    else:
        state["uncommitted"] = []

    # recent commits (last 5)
    log = _git_output([
        "log", "--oneline", "-5", "--format=%h %s"
    ])
    if log:
        state["recent_commits"] = log.strip().split("\n")
    else:
        state["recent_commits"] = []

    # diff stat (what's changed but not committed)
    diff_stat = _git_output(["diff", "--stat", "--no-color"])
    if diff_stat:
        state["diff_summary"] = diff_stat.strip().split("\n")[-1]  # summary line
    else:
        state["diff_summary"] = None

    return state


# ---------------------------------------------------------------------------
# VS Code focus integration
# ---------------------------------------------------------------------------


def read_focus_state() -> dict[str, Any] | None:
    """read the current VS Code focus state from telemetry file."""
    try:
        if FOCUS_FILE.exists():
            data = json.loads(FOCUS_FILE.read_text(encoding="utf-8"))
            return {
                "active_file": data.get("current_active_file"),
                "session_focus": data.get("session_focus_seconds", {}),
                "branch": data.get("branch"),
                "timestamp": data.get("timestamp"),
            }
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# awareness scan — the core observation loop
# ---------------------------------------------------------------------------


async def scan_dev_awareness() -> dict[str, Any] | None:
    """perform a dev awareness scan. called by daemon periodically.

    returns observations if anything interesting was detected, None otherwise.
    """
    global _cycles_since_last_scan
    _cycles_since_last_scan += 1

    if _cycles_since_last_scan < AWARENESS_SCAN_INTERVAL:
        return None
    _cycles_since_last_scan = 0

    observations: list[str] = []

    # read VS Code state
    focus = read_focus_state()
    if focus:
        active = focus.get("active_file")
        if active and active != _dev_state.get("active_file"):
            _dev_state["active_file"] = active
            # track session files
            if active not in _dev_state["session_files"]:
                _dev_state["session_files"].append(active)
                if len(_dev_state["session_files"]) > 50:
                    _dev_state["session_files"] = _dev_state["session_files"][-50:]

        # detect focus patterns
        session_focus = focus.get("session_focus", {})
        if session_focus:
            sorted_files = sorted(
                session_focus.items(), key=lambda x: x[1], reverse=True
            )
            if sorted_files:
                top_file, top_seconds = sorted_files[0]
                if top_seconds > 1800:  # 30+ minutes on one file
                    observations.append(
                        f"deep focus detected: {Path(top_file).name} "
                        f"({top_seconds // 60}m spent)"
                    )

    # scan git state
    git_state = scan_git_state()
    _dev_state["branch"] = git_state.get("branch")

    uncommitted = git_state.get("uncommitted", [])
    _dev_state["uncommitted_files"] = uncommitted

    if len(uncommitted) > 10:
        observations.append(
            f"large uncommitted changeset: {len(uncommitted)} files modified"
        )

    # detect if working on tests
    test_files = [
        f for f in uncommitted
        if "test" in f.get("file", "").lower()
    ]
    if test_files:
        observations.append(
            f"test files being modified: {len(test_files)} test files changed"
        )

    # detect new files
    new_files = [f for f in uncommitted if f.get("status", "").startswith("?")]
    if new_files:
        file_names = [Path(f["file"]).name for f in new_files[:5]]
        observations.append(f"new files created: {', '.join(file_names)}")

    _dev_state["recent_changes"] = [f["file"] for f in uncommitted[:20]]
    _dev_state["last_scan"] = datetime.now(timezone.utc).isoformat()

    if observations:
        logger.info("dev awareness: %d observations", len(observations))
        return {
            "type": "dev_awareness",
            "observations": observations,
            "git_state": {
                "branch": git_state.get("branch"),
                "uncommitted_count": len(uncommitted),
                "diff_summary": git_state.get("diff_summary"),
            },
            "focus": {
                "active_file": _dev_state.get("active_file"),
                "session_files_count": len(_dev_state.get("session_files", [])),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return None


# ---------------------------------------------------------------------------
# proactive dev insights — generated when patterns are concerning
# ---------------------------------------------------------------------------


def generate_dev_insight() -> str | None:
    """generate a proactive dev insight if current state warrants it.

    called by the dream state or presence system to offer help.
    """
    uncommitted = _dev_state.get("uncommitted_files", [])

    if len(uncommitted) > 15:
        return (
            "you've got a lot of uncommitted changes building up... "
            "might be worth a checkpoint commit before going further."
        )

    session_files = _dev_state.get("session_files", [])
    if len(session_files) > 20:
        return (
            "you've touched a lot of files this session... "
            "that's either a big feature or scope creep. want to talk through it?"
        )

    return None


# ---------------------------------------------------------------------------
# context injection — add dev awareness to chat context
# ---------------------------------------------------------------------------


def build_dev_awareness_context() -> str:
    """build a dev awareness context string for injection into chat system prompt."""
    parts: list[str] = []

    if _dev_state.get("active_file"):
        parts.append(f"- currently editing: {Path(_dev_state['active_file']).name}")

    if _dev_state.get("branch"):
        parts.append(f"- git branch: {_dev_state['branch']}")

    uncommitted = _dev_state.get("uncommitted_files", [])
    if uncommitted:
        count = len(uncommitted)
        file_names = [Path(f.get("file", "")).name for f in uncommitted[:5]]
        parts.append(f"- uncommitted changes: {count} files ({', '.join(file_names)})")

    if _dev_state.get("recent_errors"):
        parts.append(f"- recent errors detected: {len(_dev_state['recent_errors'])}")

    session_files = _dev_state.get("session_files", [])
    if session_files:
        parts.append(f"- files touched this session: {len(session_files)}")

    if not parts:
        return ""

    return "## dev awareness\n" + "\n".join(parts)
