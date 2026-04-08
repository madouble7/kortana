r"""
kor'tana voice tools — agentic tool execution for the voice daemon

Gives kor'tana the ability to act, not just observe.
Each tool is classified under the Human Only Protocol:
  AUTO     — safe, reversible, read-only. Executes silently.
  HO       — destructive or external-facing. Requires Matt's verbal OK.
  APPROVAL — irreversible infrastructure changes. Explicit approval only.

Tools are invoked when Groq detects an intent match in the user's speech.
The LLM returns a structured tool_call which this module dispatches.

Usage from voice_daemon:
    from voice_tools import detect_and_run_tool
    result = detect_and_run_tool(user_message, conversation_history)
    if result:
        speak(result)
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import httpx

# ── vision module (lazy import) ───────────────────────────────────────────────
try:
    from vision import (
        analyze_for_errors,
        analyze_screen,
        describe_code_on_screen,
        get_frame_age,
        is_capturing,
        read_screen_text,
        start_capture,
    )

    _VISION_AVAILABLE = True
except ImportError:
    _VISION_AVAILABLE = False

# ── constants ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(r"c:\kortana")
BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8001")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", os.getenv("GH_TOKEN", ""))
GITHUB_OWNER = os.getenv("KORTANA_GITHUB_OWNER", "madouble7")
GITHUB_REPO = os.getenv("KORTANA_GITHUB_REPO", "kortana")

# Sandbox: only allow commands in these directories
_SAFE_PATHS = {
    REPO_ROOT,
    REPO_ROOT / "backend",
    REPO_ROOT / "frontend",
    REPO_ROOT / "mcp-server",
}
# Commands that are NEVER allowed
_BLOCKED_COMMANDS = {
    "rm -rf",
    "format ",
    "del /s",
    "rmdir /s",
    "drop table",
    "drop database",
}
# Max output length to read back to user
_MAX_OUTPUT_CHARS = 500
_CMD_TIMEOUT = 30  # seconds


class HOP(Enum):
    """Human Only Protocol classification."""

    AUTO = "auto"  # safe, reversible — execute immediately
    HO = "ho"  # needs Matt's verbal confirmation
    APPROVAL = "approval"  # needs explicit approval (not implemented in voice yet)


@dataclass
class Tool:
    name: str
    description: str
    hop: HOP
    handler: Any  # callable(args: dict) -> str
    examples: list[str] = field(default_factory=list)


# ── tool registry ──────────────────────────────────────────────────────────────
_tools: dict[str, Tool] = {}


def _register(name: str, description: str, hop: HOP, examples: list[str] | None = None):
    """Decorator to register a tool."""

    def decorator(fn):
        _tools[name] = Tool(
            name=name,
            description=description,
            hop=hop,
            handler=fn,
            examples=examples or [],
        )
        return fn

    return decorator


# ── AUTO tools (read-only, safe) ──────────────────────────────────────────────


@_register(
    "read_ci_logs",
    "Fetch the latest CI/CD pipeline run logs from GitHub Actions",
    HOP.AUTO,
    examples=[
        "read the CI logs",
        "what failed in the pipeline",
        "show me the build error",
    ],
)
def _tool_read_ci_logs(args: dict) -> str:
    if not GITHUB_TOKEN:
        return "I don't have a GitHub token configured."
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            # Get latest run
            runs = (
                client.get(
                    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs",
                    headers=headers,
                    params={"per_page": 1},
                )
                .json()
                .get("workflow_runs", [])
            )
            if not runs:
                return "No CI runs found."
            run = runs[0]
            run_id = run["id"]
            conclusion = run.get("conclusion", run.get("status", "unknown"))
            branch = run.get("head_branch", "unknown")

            # Get failed jobs
            jobs = (
                client.get(
                    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs/{run_id}/jobs",
                    headers=headers,
                )
                .json()
                .get("jobs", [])
            )

            failed_steps = []
            for job in jobs:
                if job.get("conclusion") == "failure":
                    for step in job.get("steps", []):
                        if step.get("conclusion") == "failure":
                            failed_steps.append(f"{job['name']}: {step['name']}")

            if failed_steps:
                steps_text = ", ".join(failed_steps[:3])
                return (
                    f"The latest CI run on {branch} {conclusion}. "
                    f"Failed steps: {steps_text}."
                )
            return f"The latest CI run on {branch} {conclusion}. No specific step failures found."
    except Exception as e:
        return f"Couldn't fetch CI logs: {e}"


@_register(
    "git_status",
    "Show current git status — branch, uncommitted changes",
    HOP.AUTO,
    examples=[
        "git status",
        "what branch am I on",
        "any uncommitted changes",
        "what's changed",
    ],
)
def _tool_git_status(args: dict) -> str:
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(REPO_ROOT),
            timeout=5,
            text=True,
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=str(REPO_ROOT),
            timeout=5,
            text=True,
        ).strip()
        if not status:
            return f"On branch {branch}, working tree clean."
        lines = status.splitlines()
        return f"On branch {branch}. {len(lines)} changed files: {', '.join(l.strip() for l in lines[:5])}."
    except Exception as e:
        return f"Git status failed: {e}"


@_register(
    "git_log",
    "Show recent git commits",
    HOP.AUTO,
    examples=[
        "show recent commits",
        "git log",
        "what was the last commit",
        "commit history",
    ],
)
def _tool_git_log(args: dict) -> str:
    count = min(args.get("count", 5), 10)
    try:
        log_output = subprocess.check_output(
            ["git", "log", "--oneline", f"-{count}"],
            cwd=str(REPO_ROOT),
            timeout=5,
            text=True,
        ).strip()
        return f"Last {count} commits: {log_output}"
    except Exception as e:
        return f"Git log failed: {e}"


@_register(
    "git_diff",
    "Show the current uncommitted diff summary",
    HOP.AUTO,
    examples=["show the diff", "what did I change", "git diff"],
)
def _tool_git_diff(args: dict) -> str:
    try:
        diff = subprocess.check_output(
            ["git", "diff", "--stat"],
            cwd=str(REPO_ROOT),
            timeout=10,
            text=True,
        ).strip()
        if not diff:
            diff = subprocess.check_output(
                ["git", "diff", "--cached", "--stat"],
                cwd=str(REPO_ROOT),
                timeout=10,
                text=True,
            ).strip()
        if not diff:
            return "No uncommitted changes."
        return f"Changes: {diff}"
    except Exception as e:
        return f"Git diff failed: {e}"


@_register(
    "read_file",
    "Read the contents of a file in the repository",
    HOP.AUTO,
    examples=["read the main file", "show me the config", "what's in requirements.txt"],
)
def _tool_read_file(args: dict) -> str:
    filepath = args.get("file", "")
    if not filepath:
        return "Which file should I read?"
    target = (REPO_ROOT / filepath).resolve()
    # Security: must be inside repo
    if not str(target).startswith(str(REPO_ROOT)):
        return "I can only read files inside the kortana repository."
    if not target.exists():
        return f"File not found: {filepath}"
    if target.stat().st_size > 50_000:
        return f"{filepath} is too large to read aloud ({target.stat().st_size:,} bytes). Try a specific section."
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        # Summarize for voice — first and last 10 lines
        lines = content.splitlines()
        if len(lines) <= 20:
            summary = content[:_MAX_OUTPUT_CHARS]
        else:
            head = "\n".join(lines[:10])
            tail = "\n".join(lines[-5:])
            summary = f"{head}\n... ({len(lines)} total lines) ...\n{tail}"
        return f"{filepath}: {summary[:_MAX_OUTPUT_CHARS]}"
    except Exception as e:
        return f"Couldn't read {filepath}: {e}"


@_register(
    "run_tests",
    "Run the backend pytest suite",
    HOP.AUTO,
    examples=["run tests", "run the test suite", "are tests passing", "pytest"],
)
def _tool_run_tests(args: dict) -> str:
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "-q", "--tb=short", "--no-header", "-x"],
            cwd=str(REPO_ROOT / "backend"),
            timeout=120,
            capture_output=True,
            text=True,
        )
        output = (result.stdout + result.stderr).strip()
        # Extract summary line
        for line in reversed(output.splitlines()):
            if "passed" in line or "failed" in line or "error" in line:
                return f"Test result: {line.strip()}"
        return f"Tests finished with exit code {result.returncode}. {output[-_MAX_OUTPUT_CHARS:]}"
    except subprocess.TimeoutExpired:
        return "Tests timed out after 2 minutes."
    except Exception as e:
        return f"Couldn't run tests: {e}"


@_register(
    "run_lint",
    "Run ruff linter on the backend",
    HOP.AUTO,
    examples=["run the linter", "lint the code", "any lint errors", "ruff check"],
)
def _tool_run_lint(args: dict) -> str:
    try:
        result = subprocess.run(
            ["python", "-m", "ruff", "check", ".", "--no-fix"],
            cwd=str(REPO_ROOT / "backend"),
            timeout=30,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return "Linting passed. No issues found."
        output = result.stdout.strip()
        lines = output.splitlines()
        return f"Linting found {len(lines)} issues. First few: {'; '.join(lines[:3])}"
    except Exception as e:
        return f"Couldn't run linter: {e}"


@_register(
    "backend_health",
    "Check if the backend API is alive and responding",
    HOP.AUTO,
    examples=[
        "is the backend up",
        "check the backend",
        "backend health",
        "is the API running",
    ],
)
def _tool_backend_health(args: dict) -> str:
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{BACKEND_URL}/api/health")
        if resp.status_code == 200:
            data = resp.json()
            return f"Backend is alive. Status: {data.get('status', 'ok')}."
        return f"Backend responded with status {resp.status_code}."
    except Exception as e:
        return f"Backend is unreachable: {e}"


@_register(
    "system_status",
    "Full system status — backend, daemon, ChromaDB, git",
    HOP.AUTO,
    examples=[
        "system status",
        "how's everything running",
        "full status check",
        "status report",
    ],
)
def _tool_system_status(args: dict) -> str:
    parts = []
    # Backend
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{BACKEND_URL}/api/health")
        parts.append(
            f"Backend: {'online' if resp.status_code == 200 else f'status {resp.status_code}'}"
        )
    except Exception:
        parts.append("Backend: offline")

    # Git
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(REPO_ROOT),
            timeout=5,
            text=True,
        ).strip()
        parts.append(f"Branch: {branch}")
    except Exception:
        parts.append("Git: unavailable")

    # ChromaDB
    try:
        import chromadb

        client = chromadb.PersistentClient(
            path=str(REPO_ROOT / "data" / "voice_memory")
        )
        col = client.get_collection("voice_episodes")
        parts.append(f"Memory: {col.count()} episodes in ChromaDB")
    except Exception:
        parts.append("Memory: ChromaDB unavailable")

    return ". ".join(parts) + "."


# ── HO tools (need Matt's verbal confirmation) ───────────────────────────────


@_register(
    "git_commit",
    "Stage all changes and commit with a message",
    HOP.HO,
    examples=["commit these changes", "git commit", "save my work"],
)
def _tool_git_commit(args: dict) -> str:
    message = args.get("message", "")
    if not message:
        return "What should the commit message be?"
    try:
        subprocess.check_output(
            ["git", "add", "-A"],
            cwd=str(REPO_ROOT),
            timeout=10,
            text=True,
        )
        result = subprocess.check_output(
            ["git", "commit", "-m", message],
            cwd=str(REPO_ROOT),
            timeout=15,
            text=True,
        ).strip()
        # Extract short hash
        for line in result.splitlines():
            if line.startswith("["):
                return f"Committed: {line}"
        return "Committed successfully."
    except subprocess.CalledProcessError as e:
        output = (e.stdout or "") + (e.stderr or "")
        if "nothing to commit" in output:
            return "Nothing to commit, working tree is clean."
        return f"Commit failed: {output[:200]}"
    except Exception as e:
        return f"Commit failed: {e}"


@_register(
    "git_push",
    "Push current branch to origin",
    HOP.HO,
    examples=["push to origin", "git push", "push my changes"],
)
def _tool_git_push(args: dict) -> str:
    try:
        result = subprocess.check_output(
            ["git", "push"],
            cwd=str(REPO_ROOT),
            timeout=30,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
        return f"Pushed successfully. {result[:200]}"
    except subprocess.CalledProcessError as e:
        return f"Push failed: {(e.stdout or '')[:200]}"
    except Exception as e:
        return f"Push failed: {e}"


@_register(
    "restart_backend",
    "Restart the FastAPI backend server",
    HOP.HO,
    examples=["restart the backend", "reboot the server", "restart the API"],
)
def _tool_restart_backend(args: dict) -> str:
    try:
        # Kill existing uvicorn
        subprocess.run(
            ["taskkill", "/F", "/IM", "uvicorn.exe"],
            timeout=5,
            capture_output=True,
        )
        time.sleep(2)
        # Start new backend
        subprocess.Popen(
            [
                "python",
                "-m",
                "uvicorn",
                "src.kortana.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8001",
            ],
            cwd=str(REPO_ROOT / "backend"),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        time.sleep(3)
        # Verify
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{BACKEND_URL}/api/health")
            if resp.status_code == 200:
                return "Backend restarted and healthy."
        except Exception:
            pass
        return "Backend restart initiated. It may take a few seconds to come online."
    except Exception as e:
        return f"Couldn't restart backend: {e}"


@_register(
    "run_lint_fix",
    "Run ruff linter with auto-fix on the backend",
    HOP.HO,
    examples=["fix the lint errors", "auto-fix lint", "ruff fix"],
)
def _tool_run_lint_fix(args: dict) -> str:
    try:
        result = subprocess.run(
            ["python", "-m", "ruff", "check", ".", "--fix"],
            cwd=str(REPO_ROOT / "backend"),
            timeout=30,
            capture_output=True,
            text=True,
        )
        output = (result.stdout + result.stderr).strip()
        if "Fixed" in output:
            return f"Lint auto-fix applied. {output[:200]}"
        if result.returncode == 0:
            return "No lint issues to fix."
        return f"Lint fix result: {output[:200]}"
    except Exception as e:
        return f"Lint fix failed: {e}"


# ── VISION tools (read-only, safe) ───────────────────────────────────────────


@_register(
    "whats_on_screen",
    "Describe what's currently visible on screen",
    HOP.AUTO,
    examples=[
        "what's on my screen",
        "what do you see",
        "what am I looking at",
        "describe my screen",
    ],
)
def _tool_whats_on_screen(args: dict) -> str:
    if not _VISION_AVAILABLE:
        return "Vision module isn't loaded. I can't see your screen right now."
    if not is_capturing():
        start_capture()
        import time as _t

        _t.sleep(2)  # wait for first frame
    question = args.get("question", "")
    if question:
        return analyze_screen(question)
    return analyze_screen()


@_register(
    "screen_errors",
    "Check the screen for error messages, warnings, or failures",
    HOP.AUTO,
    examples=[
        "any errors on screen",
        "what error do you see",
        "read the error message",
        "is there an error",
        "what went wrong",
    ],
)
def _tool_screen_errors(args: dict) -> str:
    if not _VISION_AVAILABLE:
        return "Vision module isn't loaded. I can't see your screen right now."
    if not is_capturing():
        start_capture()
        import time as _t

        _t.sleep(2)
    return analyze_for_errors()


@_register(
    "read_screen",
    "Read the text visible on screen — code, terminal output, dialogs",
    HOP.AUTO,
    examples=[
        "read the screen",
        "read what's on screen",
        "what does it say",
        "read the terminal",
        "read the output",
    ],
)
def _tool_read_screen(args: dict) -> str:
    if not _VISION_AVAILABLE:
        return "Vision module isn't loaded. I can't see your screen right now."
    if not is_capturing():
        start_capture()
        import time as _t

        _t.sleep(2)
    return read_screen_text()


@_register(
    "describe_code",
    "Describe the code currently visible in the editor",
    HOP.AUTO,
    examples=[
        "what code is this",
        "describe this code",
        "what file am I in",
        "what am I editing",
        "explain this code",
    ],
)
def _tool_describe_code(args: dict) -> str:
    if not _VISION_AVAILABLE:
        return "Vision module isn't loaded. I can't see your screen right now."
    if not is_capturing():
        start_capture()
        import time as _t

        _t.sleep(2)
    return describe_code_on_screen()


# ── intent detection via Groq ─────────────────────────────────────────────────

_TOOL_DETECTION_PROMPT = """You are a tool router for kor'tana, an AI voice assistant.
Given the user's message, determine if they want to use one of these tools:

{tool_list}

If a tool matches, respond with EXACTLY this JSON (no markdown, no extra text):
{{"tool": "tool_name", "args": {{}}}}

If no tool matches (it's just conversation), respond with:
{{"tool": null}}

Only match when the user's intent CLEARLY maps to a tool. Casual conversation is NOT a tool call."""


def _build_tool_list() -> str:
    """Build tool descriptions for the detection prompt."""
    lines = []
    for name, tool in _tools.items():
        ex = ", ".join(f'"{e}"' for e in tool.examples[:2])
        lines.append(f"- {name} [{tool.hop.value}]: {tool.description}. Examples: {ex}")
    return "\n".join(lines)


def detect_tool_intent(message: str) -> dict[str, Any] | None:
    """Use Groq to detect if the user's message maps to a tool.

    Returns {"tool": "name", "args": {...}} or None for no match.
    """
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        return None

    prompt = _TOOL_DETECTION_PROMPT.format(tool_list=_build_tool_list())

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": message},
                    ],
                    "max_tokens": 80,
                    "temperature": 0.0,
                },
            )
        if resp.status_code != 200:
            return None

        content = resp.json()["choices"][0]["message"]["content"].strip()

        # Parse JSON response — handle possible markdown wrapping
        content = content.strip("`").strip()
        if content.startswith("json"):
            content = content[4:].strip()

        parsed = json.loads(content)
        if parsed.get("tool") is None:
            return None
        return parsed
    except Exception:
        return None


def execute_tool(tool_name: str, args: dict) -> tuple[str, HOP]:
    """Execute a tool by name. Returns (result_text, hop_level)."""
    tool = _tools.get(tool_name)
    if not tool:
        return (f"Unknown tool: {tool_name}", HOP.AUTO)

    # Security: check for blocked commands in args
    args_str = json.dumps(args).lower()
    for blocked in _BLOCKED_COMMANDS:
        if blocked in args_str:
            return (
                f"I can't execute that — '{blocked}' is blocked for safety.",
                tool.hop,
            )

    result = tool.handler(args)
    return (result, tool.hop)


def detect_and_run_tool(
    message: str,
    confirm_ho_callback: Any | None = None,
) -> str | None:
    """Full pipeline: detect intent → classify → execute (or request confirmation).

    Args:
        message: The user's transcribed speech.
        confirm_ho_callback: Optional callable(tool_name, description) -> bool
            that asks Matt for verbal confirmation on HO tools.
            If None, HO tools will ask but not execute.

    Returns:
        Tool output string, or None if no tool matched.
    """
    intent = detect_tool_intent(message)
    if not intent or not intent.get("tool"):
        return None

    tool_name = intent["tool"]
    args = intent.get("args", {})
    tool = _tools.get(tool_name)

    if not tool:
        return None

    if tool.hop == HOP.AUTO:
        # Execute immediately — safe, reversible
        result, _ = execute_tool(tool_name, args)
        # Multi-step reasoning: if the result looks like a failure,
        # autonomously chain follow-up tools to diagnose the root cause
        return run_tool_chain(message, tool_name, args, result)

    elif tool.hop == HOP.HO:
        # Needs Matt's verbal OK
        if confirm_ho_callback:
            confirmed = confirm_ho_callback(tool_name, tool.description)
            if confirmed:
                result, _ = execute_tool(tool_name, args)
                return result
            else:
                return f"Okay, I won't {tool.description.lower()}."
        else:
            return (
                f"I can {tool.description.lower()}, but that needs your okay. "
                f"Say 'yes' or 'go ahead' to confirm."
            )

    elif tool.hop == HOP.APPROVAL:
        return (
            "That requires explicit approval. "
            "I'll add it to the approval queue for you to review."
        )

    return None


def get_tool_names() -> list[str]:
    """Return all registered tool names."""
    return list(_tools.keys())


def get_tool_descriptions() -> str:
    """Human-readable summary of all tools."""
    lines = []
    for name, tool in _tools.items():
        lines.append(f"{name} ({tool.hop.value}): {tool.description}")
    return "\n".join(lines)


# ── multi-step agentic reasoning ──────────────────────────────────────────────
# When a tool returns a failure or error, the chain-of-thought engine
# autonomously decides which follow-up tools to call to diagnose
# the root cause, then synthesizes a single coherent spoken report.

_MAX_CHAIN_STEPS = 3  # hard cap on autonomous follow-up steps
_FAILURE_INDICATORS = [
    "failed",
    "error",
    "timed out",
    "unreachable",
    "not found",
    "issues",
    "exception",
    "traceback",
]

_CHAIN_REASONING_PROMPT = """You are kor'tana's reasoning engine. A tool was just executed and returned an error or failure.

Your job: decide what SINGLE follow-up tool to call next to diagnose WHY it failed.

ORIGINAL REQUEST: {original_message}
TOOL EXECUTED: {tool_name}
TOOL RESULT: {tool_result}

Available follow-up tools (AUTO only — you cannot chain HO tools):
{auto_tools}

Respond with EXACTLY this JSON (no markdown):
{{"tool": "tool_name", "args": {{}}, "reason": "brief reason for this follow-up"}}

If no follow-up would help, or you have enough info already, respond:
{{"tool": null, "reason": "sufficient info"}}

Rules:
- Only pick ONE tool per step
- Only pick AUTO tools (read-only, safe)
- Pick the tool most likely to reveal the ROOT CAUSE
- If tests failed, try read_file on the failing test or screen_errors
- If backend is down, try system_status
- If CI failed, try read_ci_logs
- If lint found issues, the result already has the info — stop
- NEVER repeat a tool already used in this chain"""


def _get_auto_tool_list(exclude: set[str] | None = None) -> str:
    """Build list of AUTO tools for the chain reasoning prompt."""
    exclude = exclude or set()
    lines = []
    for name, tool in _tools.items():
        if tool.hop == HOP.AUTO and name not in exclude:
            lines.append(f"- {name}: {tool.description}")
    return "\n".join(lines)


def _result_looks_like_failure(result: str) -> bool:
    """Check if a tool result contains failure indicators."""
    lower = result.lower()
    return any(indicator in lower for indicator in _FAILURE_INDICATORS)


def _chain_reason_next(
    original_message: str,
    tool_name: str,
    tool_result: str,
    used_tools: set[str],
) -> dict[str, Any] | None:
    """Ask Groq which follow-up tool to call next.

    Returns {"tool": "name", "args": {...}, "reason": "..."} or None.
    """
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        return None

    prompt = _CHAIN_REASONING_PROMPT.format(
        original_message=original_message,
        tool_name=tool_name,
        tool_result=tool_result[:400],  # truncate for prompt budget
        auto_tools=_get_auto_tool_list(exclude=used_tools),
    )

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": prompt},
                        {
                            "role": "user",
                            "content": "What follow-up tool should I run?",
                        },
                    ],
                    "max_tokens": 100,
                    "temperature": 0.0,
                },
            )
        if resp.status_code != 200:
            return None

        content = resp.json()["choices"][0]["message"]["content"].strip()
        content = content.strip("`").strip()
        if content.startswith("json"):
            content = content[4:].strip()

        parsed = json.loads(content)
        if parsed.get("tool") is None:
            return None
        return parsed
    except Exception:
        return None


_SYNTHESIS_PROMPT = """You are kor'tana, a calm AI companion. Synthesize these diagnostic results into a single, clear spoken summary.

ORIGINAL QUESTION: {original_message}

DIAGNOSTIC CHAIN:
{chain_summary}

Rules:
- 2-3 sentences max, optimized for speech
- No markdown, no code blocks, no bullet lists
- State what happened, why it happened, and what to do about it
- Be specific: file names, line numbers, error messages
- Be warm and direct"""


def _synthesize_chain(
    original_message: str,
    chain: list[tuple[str, str, str]],
) -> str:
    """Synthesize a chain of tool results into a single spoken report.

    Args:
        original_message: The user's original request.
        chain: List of (tool_name, reason, result) tuples.

    Returns:
        Synthesized spoken summary.
    """
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        # Fallback: just concatenate results
        return " ".join(result for _, _, result in chain)

    chain_text = ""
    for i, (tool_name, reason, result) in enumerate(chain, 1):
        chain_text += f"Step {i} — {tool_name} ({reason}):\n{result[:300]}\n\n"

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system",
                            "content": _SYNTHESIS_PROMPT.format(
                                original_message=original_message,
                                chain_summary=chain_text,
                            ),
                        },
                        {
                            "role": "user",
                            "content": "Give me the summary.",
                        },
                    ],
                    "max_tokens": 150,
                    "temperature": 0.3,
                },
            )
        if resp.status_code != 200:
            return chain[-1][2]  # fallback: last tool result

        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return chain[-1][2]


def run_tool_chain(
    message: str,
    initial_tool: str,
    initial_args: dict,
    initial_result: str,
) -> str:
    """Run a multi-step diagnostic chain starting from a failed tool result.

    1. Check if initial result looks like a failure
    2. If so, ask Groq what follow-up tool to call
    3. Execute follow-up, check again
    4. Repeat up to _MAX_CHAIN_STEPS times
    5. Synthesize all results into one spoken report

    Returns the synthesized report, or the original result if no chaining needed.
    """
    if not _result_looks_like_failure(initial_result):
        return initial_result

    chain: list[tuple[str, str, str]] = [
        (initial_tool, "initial request", initial_result)
    ]
    used_tools: set[str] = {initial_tool}

    for step in range(_MAX_CHAIN_STEPS):
        # Ask Groq what follow-up to run
        last_tool, _, last_result = chain[-1]
        next_action = _chain_reason_next(message, last_tool, last_result, used_tools)

        if not next_action or not next_action.get("tool"):
            break  # Groq says we have enough info

        next_tool = next_action["tool"]
        next_args = next_action.get("args", {})
        reason = next_action.get("reason", "follow-up")

        # Safety: only chain AUTO tools
        tool_obj = _tools.get(next_tool)
        if not tool_obj or tool_obj.hop != HOP.AUTO:
            break

        # Don't repeat tools
        if next_tool in used_tools:
            break

        # Execute follow-up
        result, _ = execute_tool(next_tool, next_args)
        chain.append((next_tool, reason, result))
        used_tools.add(next_tool)

        # If this follow-up didn't fail, we probably have our answer
        if not _result_looks_like_failure(result):
            break

    # Single-step chains don't need synthesis
    if len(chain) <= 1:
        return initial_result

    # Synthesize multi-step results into one spoken report
    return _synthesize_chain(message, chain)
