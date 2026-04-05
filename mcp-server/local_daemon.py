"""
kor'tana local daemon — runs autonomously on MADOUBLE even when Railway is down.

Cycle:
  1. Poll backend health endpoint
  2. If backend is UNHEALTHY → restart it, send Windows toast
  3. Pull latest from GitHub
  4. Execute any pending LOCAL tasks (file edits, builds, restarts)
  5. Report status via Windows toast when something meaningful happens

Run:  python c:\kortana\mcp-server\local_daemon.py
Auto-start: add a Task Scheduler entry pointing at this script.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
import psutil

# ── config ─────────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")
HEALTH_URL = f"{BACKEND_URL}/health"
REPO_ROOT = Path(r"c:\kortana")
BACKEND_DIR = REPO_ROOT / "backend"
LOG_FILE = REPO_ROOT / "logs" / "local_daemon.log"
CYCLE_INTERVAL = int(os.getenv("LOCAL_DAEMON_INTERVAL", "30"))  # seconds

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


# ── logging ────────────────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── windows toast ──────────────────────────────────────────────────────────────
def toast(title: str, message: str) -> None:
    """Send a Windows 11 toast notification via PowerShell."""
    ps = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
  <visual>
    <binding template="ToastGeneric">
      <text>{title}</text>
      <text>{message}</text>
    </binding>
  </visual>
</toast>
"@
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("kor'tana").Show($toast)
"""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True, timeout=5,
        )
    except Exception as e:
        log(f"Toast failed (non-fatal): {e}", "WARN")


# ── health check ───────────────────────────────────────────────────────────────
async def check_backend_health() -> tuple[bool, dict]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(HEALTH_URL)
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            return r.status_code == 200, data
    except Exception as e:
        log(f"Health check failed: {e}", "WARN")
        return False, {}


# ── backend restart ────────────────────────────────────────────────────────────
def find_uvicorn_pid() -> int | None:
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(p.cmdline())
            if "uvicorn" in cmdline and "kortana" in cmdline:
                return p.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None


def restart_backend() -> None:
    log("Attempting backend restart…", "WARN")
    pid = find_uvicorn_pid()
    if pid:
        try:
            psutil.Process(pid).terminate()
            time.sleep(2)
            log(f"Terminated stale uvicorn PID {pid}")
        except psutil.NoSuchProcess:
            pass

    env_file = BACKEND_DIR / ".env"
    cmd = (
        f"cd '{BACKEND_DIR}'; "
        f"$env:PYTHONPATH='src'; "
        + (f"Get-Content '{env_file}' | ForEach-Object {{ if ($_ -match '^([^#][^=]+)=(.+)$') {{ [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim()) }} }}; " if env_file.exists() else "")
        + "python -m uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000 --log-level warning"
    )
    subprocess.Popen(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
        cwd=str(BACKEND_DIR),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    log("Backend restart initiated")
    toast("kor'tana self-repair", "Backend was down — restarting now")


# ── git pull ───────────────────────────────────────────────────────────────────
def git_pull() -> bool:
    """Pull latest from GitHub. Returns True if new commits landed."""
    result = subprocess.run(
        ["git", "pull", "--ff-only"],
        cwd=str(BACKEND_DIR),
        capture_output=True, text=True, timeout=30,
    )
    pulled = "Already up to date" not in result.stdout
    if pulled:
        log(f"git pull: {result.stdout.strip()}")
        toast("kor'tana update", "New commits pulled from GitHub")
    return pulled


# ── local task executor ────────────────────────────────────────────────────────
LOCAL_TASK_FILE = REPO_ROOT / "mcp-server" / "local_tasks.json"


def load_local_tasks() -> list[dict]:
    if not LOCAL_TASK_FILE.exists():
        return []
    try:
        return json.loads(LOCAL_TASK_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_local_tasks(tasks: list[dict]) -> None:
    LOCAL_TASK_FILE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


def execute_local_task(task: dict) -> bool:
    """Execute a single local task. Returns True on success."""
    kind = task.get("kind", "shell")
    log(f"Executing local task [{kind}]: {task.get('description', task.get('command', ''))[:80]}")

    try:
        if kind == "shell":
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", task["command"]],
                cwd=task.get("cwd", str(REPO_ROOT)),
                capture_output=True, text=True, timeout=task.get("timeout", 120),
            )
            success = result.returncode == 0
            if not success:
                log(f"Task failed (exit {result.returncode}): {result.stderr[:200]}", "ERROR")
            return success

        if kind == "write_file":
            p = Path(task["path"])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(task["content"], encoding="utf-8")
            return True

        if kind == "git_commit":
            cwd = task.get("cwd", str(BACKEND_DIR))
            subprocess.run(["git", "add", task.get("files", "-A")], cwd=cwd)
            subprocess.run(["git", "commit", "-m", task["message"]], cwd=cwd)
            if task.get("push", True):
                subprocess.run(["git", "push"], cwd=cwd)
            return True

    except Exception as e:
        log(f"Task exception: {e}", "ERROR")
        return False

    log(f"Unknown task kind: {kind}", "WARN")
    return False


def run_local_tasks() -> None:
    tasks = load_local_tasks()
    if not tasks:
        return

    pending = [t for t in tasks if t.get("status") != "done"]
    if not pending:
        return

    log(f"Running {len(pending)} local task(s)")
    for task in tasks:
        if task.get("status") == "done":
            continue
        success = execute_local_task(task)
        task["status"] = "done" if success else "failed"
        task["executed_at"] = datetime.utcnow().isoformat()

    save_local_tasks(tasks)
    done_count = sum(1 for t in tasks if t.get("status") == "done")
    if done_count:
        toast("kor'tana local tasks", f"Completed {done_count} task(s) on MADOUBLE")


# ── main cycle ─────────────────────────────────────────────────────────────────
async def cycle(consecutive_failures: list[int]) -> None:
    healthy, health_data = await check_backend_health()

    if not healthy:
        consecutive_failures[0] += 1
        log(f"Backend unhealthy (failure #{consecutive_failures[0]})", "WARN")
        if consecutive_failures[0] >= 2:
            restart_backend()
            consecutive_failures[0] = 0
            await asyncio.sleep(10)  # give it time to start
    else:
        if consecutive_failures[0] > 0:
            log("Backend recovered")
            toast("kor'tana", "Backend is healthy again")
        consecutive_failures[0] = 0

    try:
        git_pull()
    except Exception as e:
        log(f"git pull error: {e}", "WARN")

    run_local_tasks()


async def main() -> None:
    log("kor'tana local daemon starting on MADOUBLE")
    toast("kor'tana", "Local daemon is awake on MADOUBLE")
    consecutive_failures = [0]

    while True:
        try:
            await cycle(consecutive_failures)
        except Exception as e:
            log(f"Cycle error: {e}", "ERROR")
        await asyncio.sleep(CYCLE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
