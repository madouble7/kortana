"""voice-to-action — kor'tana executes commands from natural language.

parses intent from voice or text commands and executes them:
  - git operations: commit, push, status, diff, log
  - test runs: pytest, npm test
  - build operations: npm build, lint, type-check
  - file operations: create, read, search
  - system queries: health, daemon status, metrics

"hey kor'tana, commit what i have" -> she does it.
"""

from __future__ import annotations

import re
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
BACKEND_ROOT = REPO_ROOT / "backend"
COMMAND_TIMEOUT = 60  # seconds

# ---------------------------------------------------------------------------
# intent recognition — lightweight pattern matching
# ---------------------------------------------------------------------------

_INTENT_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "git_commit": [
        re.compile(
            r"\b(commit|save|checkpoint)\b.*\b(what i have|changes|work|code)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\b(commit|check ?point)\b", re.IGNORECASE),
    ],
    "git_push": [
        re.compile(r"\b(push|ship|deploy)\b.*\b(it|code|changes)\b", re.IGNORECASE),
        re.compile(r"\bpush\b", re.IGNORECASE),
    ],
    "git_status": [
        re.compile(
            r"\b(what('s| is) changed|git status|what did i change)\b", re.IGNORECASE
        ),
        re.compile(
            r"\b(show|list) (my )?(changes|modifications|diffs?)\b", re.IGNORECASE
        ),
    ],
    "git_diff": [
        re.compile(r"\bshow (me )?(the )?diff\b", re.IGNORECASE),
        re.compile(r"\bwhat('s| did i) chang(e|ed)\b", re.IGNORECASE),
    ],
    "git_log": [
        re.compile(r"\b(recent|last|show) (commits?|history|log)\b", re.IGNORECASE),
        re.compile(r"\bgit log\b", re.IGNORECASE),
    ],
    "run_tests": [
        re.compile(r"\brun (the )?tests?\b", re.IGNORECASE),
        re.compile(r"\bpytest\b", re.IGNORECASE),
        re.compile(r"\btest (it|everything|all)\b", re.IGNORECASE),
    ],
    "run_lint": [
        re.compile(r"\b(lint|check) (the )?(code|it|everything)\b", re.IGNORECASE),
        re.compile(r"\bruff\b", re.IGNORECASE),
    ],
    "run_build": [
        re.compile(r"\bbuild (the )?(frontend|ui|app|it)\b", re.IGNORECASE),
        re.compile(r"\bnpm (run )?build\b", re.IGNORECASE),
    ],
    "check_health": [
        re.compile(
            r"\b(how are you|health|status|you okay|are you (up|running))\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bhealth ?check\b", re.IGNORECASE),
    ],
    "daemon_status": [
        re.compile(r"\b(daemon|autonomy|loop) (status|state|health)\b", re.IGNORECASE),
        re.compile(r"\bhow('s| is) the (daemon|loop|autonomy)\b", re.IGNORECASE),
    ],
    "what_broke": [
        re.compile(r"\bwhat (broke|failed|went wrong)\b", re.IGNORECASE),
        re.compile(r"\b(any )?(errors?|failures?|problems?)\b", re.IGNORECASE),
    ],
}


def detect_intent(text: str) -> tuple[str | None, float]:
    """detect the action intent from user text.

    returns (intent_name, confidence) or (None, 0) if no action detected.
    """
    text_lower = text.lower().strip()

    # skip if it's clearly a question or conversation
    if len(text_lower.split()) > 25:
        return None, 0.0  # too long to be a command

    best_intent: str | None = None
    best_score = 0.0

    for intent, patterns in _INTENT_PATTERNS.items():
        for pat in patterns:
            if pat.search(text_lower):
                # more specific patterns get higher scores
                specificity = len(pat.pattern) / 100
                score = min(0.5 + specificity, 1.0)
                if score > best_score:
                    best_score = score
                    best_intent = intent

    return best_intent, best_score


# ---------------------------------------------------------------------------
# action execution
# ---------------------------------------------------------------------------


def _run_cmd(
    cmd: list[str], cwd: Path | None = None, timeout: int = COMMAND_TIMEOUT
) -> dict[str, Any]:
    """run a shell command safely and return structured result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(cwd or REPO_ROOT),
            timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip()[-2000:],  # cap output
            "stderr": result.stderr.strip()[-500:],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "command timed out",
            "returncode": -1,
        }
    except Exception as exc:
        return {"success": False, "stdout": "", "stderr": str(exc), "returncode": -1}


def _generate_commit_message() -> str:
    """generate a meaningful commit message from the current diff."""
    diff = _run_cmd(["git", "diff", "--stat", "--no-color"])
    if not diff["success"]:
        return "checkpoint: work in progress"

    stat = diff["stdout"]
    lines = stat.strip().split("\n")

    if not lines:
        return "checkpoint: work in progress"

    # parse the summary line (e.g. "5 files changed, 100 insertions(+), 20 deletions(-)")
    summary = lines[-1].strip() if lines else ""

    # detect what kind of changes
    changed_files = [ln.strip().split("|")[0].strip() for ln in lines[:-1] if "|" in ln]

    if any("test" in f.lower() for f in changed_files):
        prefix = "test"
    elif any("service" in f.lower() or "router" in f.lower() for f in changed_files):
        prefix = "feat"
    elif any("fix" in f.lower() or "bug" in f.lower() for f in changed_files):
        prefix = "fix"
    else:
        prefix = "feat"

    # build message from file names
    short_names = [Path(f).stem for f in changed_files[:3]]
    if short_names:
        scope = ", ".join(short_names)
        return f"{prefix}: update {scope}"

    return f"{prefix}: {summary}"


async def execute_intent(intent: str, original_text: str = "") -> dict[str, Any]:
    """execute a detected intent and return the result.

    returns a structured result with:
      - action: what was done
      - result: command output or status
      - spoken: a voice-friendly summary
    """
    if intent == "git_commit":
        # stage all and commit
        _run_cmd(["git", "add", "-A"])
        msg = _generate_commit_message()
        result = _run_cmd(["git", "commit", "-m", msg])
        if result["success"]:
            return {
                "action": "git_commit",
                "result": result["stdout"],
                "spoken": f"done. committed with message: {msg}",
            }
        else:
            if "nothing to commit" in result["stdout"]:
                return {
                    "action": "git_commit",
                    "result": "nothing to commit",
                    "spoken": "nothing to commit... working tree is clean.",
                }
            return {
                "action": "git_commit",
                "result": result["stderr"],
                "spoken": "commit failed... " + result["stderr"][:100],
            }

    elif intent == "git_push":
        result = _run_cmd(["git", "push"])
        if result["success"]:
            return {
                "action": "git_push",
                "result": result["stdout"],
                "spoken": "pushed to remote. you're live.",
            }
        return {
            "action": "git_push",
            "result": result["stderr"],
            "spoken": "push failed... " + result["stderr"][:100],
        }

    elif intent == "git_status":
        result = _run_cmd(["git", "status", "--short"])
        if result["success"]:
            lines = result["stdout"].strip().split("\n")
            count = len([ln for ln in lines if ln.strip()])
            return {
                "action": "git_status",
                "result": result["stdout"],
                "spoken": f"{count} files changed."
                if count > 0
                else "working tree is clean.",
            }
        return {
            "action": "git_status",
            "result": result["stderr"],
            "spoken": "couldn't check git status.",
        }

    elif intent == "git_diff":
        result = _run_cmd(["git", "diff", "--stat", "--no-color"])
        return {
            "action": "git_diff",
            "result": result["stdout"][:1000],
            "spoken": result["stdout"].split("\n")[-1].strip()
            if result["stdout"]
            else "no changes.",
        }

    elif intent == "git_log":
        result = _run_cmd(["git", "log", "--oneline", "-5"])
        if result["success"]:
            return {
                "action": "git_log",
                "result": result["stdout"],
                "spoken": "last 5 commits: " + result["stdout"].replace("\n", ". "),
            }
        return {
            "action": "git_log",
            "result": "",
            "spoken": "couldn't read git log.",
        }

    elif intent == "run_tests":
        result = _run_cmd(
            ["python", "-m", "pytest", "tests/", "-q", "--tb=line"],
            cwd=BACKEND_ROOT,
            timeout=120,
        )
        output = result["stdout"]
        # extract the summary line
        summary = output.strip().split("\n")[-1] if output else "no output"
        return {
            "action": "run_tests",
            "result": output[-500:],
            "spoken": f"tests done. {summary}",
        }

    elif intent == "run_lint":
        result = _run_cmd(
            ["python", "-m", "ruff", "check", "."],
            cwd=BACKEND_ROOT,
        )
        if result["success"]:
            return {
                "action": "run_lint",
                "result": "all clean",
                "spoken": "lint passed. all clean.",
            }
        return {
            "action": "run_lint",
            "result": result["stdout"][:500],
            "spoken": "lint found some issues: " + result["stdout"][:100],
        }

    elif intent == "run_build":
        result = _run_cmd(["npm", "run", "build"], cwd=REPO_ROOT / "frontend")
        if result["success"]:
            return {
                "action": "run_build",
                "result": "build succeeded",
                "spoken": "frontend build succeeded.",
            }
        return {
            "action": "run_build",
            "result": result["stderr"][:500],
            "spoken": "build failed... " + result["stderr"][:100],
        }

    elif intent == "check_health":
        return {
            "action": "check_health",
            "result": "healthy",
            "spoken": "i'm here. systems nominal. what do you need?",
        }

    elif intent == "daemon_status":
        try:
            from src.kortana.services.autonomy_daemon import get_autonomy_daemon

            status = get_autonomy_daemon().get_status()
            cycles = status.get("cycles_completed", 0)
            state = status.get("system_state", "unknown")
            return {
                "action": "daemon_status",
                "result": status,
                "spoken": f"daemon is {state}. {cycles} cycles completed.",
            }
        except Exception:
            return {
                "action": "daemon_status",
                "result": "unavailable",
                "spoken": "daemon status unavailable right now.",
            }

    elif intent == "what_broke":
        # check recent test results and CI
        result = _run_cmd(
            ["python", "-m", "pytest", "tests/", "-q", "--tb=line", "-x"],
            cwd=BACKEND_ROOT,
            timeout=120,
        )
        if result["success"]:
            return {
                "action": "what_broke",
                "result": "nothing — all tests pass",
                "spoken": "nothing's broken. all tests pass.",
            }
        return {
            "action": "what_broke",
            "result": result["stdout"][-500:],
            "spoken": "found this: " + result["stdout"].strip().split("\n")[-1][:100],
        }

    return {
        "action": "unknown",
        "result": None,
        "spoken": "i didn't catch a specific action from that. can you be more specific?",
    }


# ---------------------------------------------------------------------------
# high-level entry point — detect + execute
# ---------------------------------------------------------------------------


async def process_voice_command(text: str) -> dict[str, Any] | None:
    """detect and execute a voice command from user text.

    returns the action result if a command was detected, None if it's just conversation.
    """
    intent, confidence = detect_intent(text)

    if intent is None or confidence < 0.4:
        return None  # not a command, just conversation

    logger.info("voice command detected: intent=%s confidence=%.2f", intent, confidence)

    result = await execute_intent(intent, original_text=text)
    result["intent"] = intent
    result["confidence"] = confidence
    result["timestamp"] = datetime.now(timezone.utc).isoformat()

    return result
