"""
kor'tana MCP Server — autonomous PC access layer
Gives kor'tana eyes, hands, and memory on the local machine.
"""

import asyncio
import functools
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import httpx
import mcp.server.stdio
import mcp.types as types
import psutil
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

server = Server("kortana-pc")

KORTANA_BACKEND = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")

# ── helpers ───────────────────────────────────────────────────────────────────


def _safe_path(p: str) -> Path:
    """Expand env vars and ~ but keep it absolute."""
    return Path(os.path.expandvars(os.path.expanduser(p))).resolve()


async def _run_proc(*args, **kwargs) -> subprocess.CompletedProcess:
    """Run subprocess.run in a thread pool so the asyncio event loop stays free."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, functools.partial(subprocess.run, *args, **kwargs)
    )


def _truncate(text: str, limit: int = 32_000) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return (
        text[:half]
        + f"\n\n[... {len(text) - limit} chars truncated ...]\n\n"
        + text[-half:]
    )


# ── tool registry ─────────────────────────────────────────────────────────────


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="execute_shell",
            description=(
                "Run a PowerShell command on kor'tana's machine. "
                "Returns stdout, stderr, and exit code. "
                "Use for builds, tests, installs, git ops, anything."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "PowerShell command to execute",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (default: c:\\kortana)",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout seconds (default: 60)",
                    },
                },
                "required": ["command"],
            },
        ),
        types.Tool(
            name="read_file",
            description="Read a file from the local filesystem. Returns full content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or ~ path to file",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "1-based start line (optional)",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "1-based end line (optional)",
                    },
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="write_file",
            description="Write or overwrite a file on the local filesystem. Creates parent dirs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or ~ path to file",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full file content to write",
                    },
                    "append": {
                        "type": "boolean",
                        "description": "Append instead of overwrite (default: false)",
                    },
                },
                "required": ["path", "content"],
            },
        ),
        types.Tool(
            name="list_directory",
            description="List contents of a directory. Returns names, types, sizes, and modified times.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"},
                    "recursive": {
                        "type": "boolean",
                        "description": "Recurse into subdirs (default: false)",
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Max recursion depth (default: 2)",
                    },
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="delete_path",
            description="Delete a file or directory (recursive). Use with care.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to delete"},
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="get_system_info",
            description=(
                "Get current machine state: CPU, memory, disk, top processes, "
                "Python/Node versions, IP, uptime, and running services."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="manage_process",
            description="List, start, or kill processes on the machine.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "kill", "start"],
                        "description": "Action to perform",
                    },
                    "pid": {
                        "type": "integer",
                        "description": "PID to kill (for action=kill)",
                    },
                    "name_filter": {
                        "type": "string",
                        "description": "Filter list by process name substring",
                    },
                    "command": {
                        "type": "string",
                        "description": "Command to start (for action=start)",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working dir for start action",
                    },
                },
                "required": ["action"],
            },
        ),
        types.Tool(
            name="git_operation",
            description="Perform git operations: status, diff, add, commit, push, pull, branch, log.",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "status",
                            "diff",
                            "add",
                            "commit",
                            "push",
                            "pull",
                            "branch",
                            "log",
                            "checkout",
                        ],
                        "description": "Git operation",
                    },
                    "repo_path": {
                        "type": "string",
                        "description": "Path to git repo (default: c:\\kortana)",
                    },
                    "args": {
                        "type": "string",
                        "description": "Extra args (e.g. branch name, commit message, file paths)",
                    },
                },
                "required": ["operation"],
            },
        ),
        types.Tool(
            name="search_files",
            description="Search for text across files using grep/ripgrep. Returns matching lines with file and line number.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Search pattern (regex supported)",
                    },
                    "path": {"type": "string", "description": "Directory to search in"},
                    "file_glob": {
                        "type": "string",
                        "description": "File pattern (e.g. *.py, *.ts)",
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Case sensitive (default: false)",
                    },
                },
                "required": ["pattern", "path"],
            },
        ),
        types.Tool(
            name="take_screenshot",
            description="Capture a screenshot of the current screen. Returns base64-encoded PNG path.",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {
                        "type": "string",
                        "description": "Where to save PNG (default: c:\\kortana\\logs\\screenshot.png)",
                    },
                },
            },
        ),
        types.Tool(
            name="get_clipboard",
            description="Read the current clipboard text content.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="set_clipboard",
            description="Write text to the clipboard.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to put on clipboard",
                    },
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="environment_vars",
            description="Read or set environment variables for the MCP server process.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["get", "set", "list"],
                        "description": "Action",
                    },
                    "name": {
                        "type": "string",
                        "description": "Variable name (for get/set)",
                    },
                    "value": {
                        "type": "string",
                        "description": "Variable value (for set)",
                    },
                },
                "required": ["action"],
            },
        ),
        types.Tool(
            name="speak",
            description="Make kor'tana speak aloud on MADOUBLE using Windows SAPI text-to-speech. Use to deliver responses, alerts, or updates out loud — even when the voice daemon isn't running.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to speak aloud"},
                    "rate": {
                        "type": "integer",
                        "description": "Words per minute (default: 175)",
                    },
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="notify",
            description="Send a Windows toast notification to Matt on MADOUBLE. Use to surface important events, completions, or alerts without requiring the chat to be open.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Notification title"},
                    "message": {"type": "string", "description": "Notification body"},
                },
                "required": ["title", "message"],
            },
        ),
        types.Tool(
            name="memory_write",
            description=(
                "Permanently store a fact, observation, or preference about Matt or the project "
                "in kor'tana's long-term memory. Use this to teach her things that should survive "
                "across sessions — habits, preferences, context, decisions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The fact or observation to remember (1–2 sentences, specific)",
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["long_term", "short_term", "episodic"],
                        "description": "Memory tier (default: long_term)",
                    },
                },
                "required": ["content"],
            },
        ),
        types.Tool(
            name="memory_search",
            description=(
                "Semantically search kor'tana's memory for relevant facts, past observations, "
                "or stored context. Use before answering questions about past conversations, "
                "Matt's preferences, or project history."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default: 5)",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="memory_recall",
            description=(
                "Load recent persistent conversation history from kor'tana's store. "
                "Returns the last N exchanges from the requested session, oldest first."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of messages to return (default: 20)",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session to recall (default: default)",
                    },
                },
            },
        ),
        types.Tool(
            name="revelation_read",
            description=(
                "Read kor'tana's unsurfaced revelations — synthesised insights she has detected "
                "from accumulated data (patterns, contradictions, predictions). "
                "Call this when starting a session or when Matt asks what she has noticed in the background."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max revelations to return (default: 5)",
                    },
                    "unsurfaced_only": {
                        "type": "boolean",
                        "description": "Return only unacknowledged revelations (default: true)",
                    },
                },
            },
        ),
        types.Tool(
            name="queue_local_task",
            description="Queue a task for the local daemon to execute autonomously on MADOUBLE (even when VS Code is closed). Supports shell commands, file writes, and git commits.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": ["shell", "write_file", "git_commit"],
                        "description": "Task type",
                    },
                    "description": {
                        "type": "string",
                        "description": "Human-readable description",
                    },
                    "command": {
                        "type": "string",
                        "description": "Shell command (for kind=shell)",
                    },
                    "cwd": {"type": "string", "description": "Working directory"},
                    "path": {
                        "type": "string",
                        "description": "File path (for kind=write_file)",
                    },
                    "content": {
                        "type": "string",
                        "description": "File content (for kind=write_file)",
                    },
                    "message": {
                        "type": "string",
                        "description": "Commit message (for kind=git_commit)",
                    },
                    "files": {
                        "type": "string",
                        "description": "Files to stage (for kind=git_commit, default: -A)",
                    },
                    "push": {
                        "type": "boolean",
                        "description": "Push after commit (default: true)",
                    },
                },
                "required": ["kind", "description"],
            },
        ),
        # ── cognitive state tools ──────────────────────────────────────────────
        types.Tool(
            name="cognitive_identity",
            description="Read kor'tana's current identity evolution — 10 personality dimensions (warmth, assertiveness, spiritual_depth, etc.) tracked via EMA, plus narrative self-description.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="cognitive_dreams",
            description="Read kor'tana's dream state — background thoughts synthesized during periods of silence. Returns prepared dream thoughts if any exist.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="cognitive_daemon",
            description="Get the autonomy daemon's current status — running state, deployment mode, tasks processed, and health metrics.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="cognitive_providers",
            description="List all AI model providers and their status — shows which models are active, their priority, and cost tier (free/paid).",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


# ── tool handlers ─────────────────────────────────────────────────────────────


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    # ── execute_shell ──────────────────────────────────────────────────────────
    if name == "execute_shell":
        cmd = arguments["command"]
        cwd = arguments.get("cwd", r"c:\kortana")
        timeout = arguments.get("timeout", 60)

        try:
            result = await _run_proc(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = {
                "stdout": _truncate(result.stdout),
                "stderr": _truncate(result.stderr),
                "exit_code": result.returncode,
                "cwd": cwd,
            }
        except subprocess.TimeoutExpired:
            output = {"error": f"Command timed out after {timeout}s", "exit_code": -1}
        except Exception as e:
            output = {"error": str(e), "exit_code": -1}

        return [types.TextContent(type="text", text=json.dumps(output, indent=2))]

    # ── read_file ──────────────────────────────────────────────────────────────
    if name == "read_file":
        p = _safe_path(arguments["path"])
        start = arguments.get("start_line")
        end = arguments.get("end_line")

        if not p.exists():
            return [
                types.TextContent(
                    type="text", text=json.dumps({"error": f"File not found: {p}"})
                )
            ]

        lines = p.read_text(encoding="utf-8", errors="replace").splitlines(
            keepends=True
        )
        if start or end:
            s = (start or 1) - 1
            e = end or len(lines)
            lines = lines[s:e]

        content = "".join(lines)
        return [types.TextContent(type="text", text=_truncate(content))]

    # ── write_file ─────────────────────────────────────────────────────────────
    if name == "write_file":
        p = _safe_path(arguments["path"])
        content = arguments["content"]
        append = arguments.get("append", False)

        p.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        p.write_text(content, encoding="utf-8") if not append else p.open(
            "a", encoding="utf-8"
        ).write(content)
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"written": str(p), "bytes": len(content.encode())}),
            )
        ]

    # ── list_directory ─────────────────────────────────────────────────────────
    if name == "list_directory":
        p = _safe_path(arguments["path"])
        recursive = arguments.get("recursive", False)
        max_depth = arguments.get("max_depth", 2)

        if not p.exists():
            return [
                types.TextContent(
                    type="text", text=json.dumps({"error": f"Path not found: {p}"})
                )
            ]

        def _walk(dirpath: Path, depth: int) -> list[dict]:
            entries = []
            try:
                for item in sorted(dirpath.iterdir()):
                    stat = item.stat()
                    entry = {
                        "name": item.name,
                        "type": "dir" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else None,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                    if recursive and item.is_dir() and depth < max_depth:
                        entry["children"] = _walk(item, depth + 1)
                    entries.append(entry)
            except PermissionError:
                pass
            return entries

        tree = _walk(p, 0)
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"path": str(p), "entries": tree}, indent=2),
            )
        ]

    # ── delete_path ────────────────────────────────────────────────────────────
    if name == "delete_path":
        p = _safe_path(arguments["path"])
        if not p.exists():
            return [
                types.TextContent(
                    type="text", text=json.dumps({"error": "Path not found"})
                )
            ]
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return [types.TextContent(type="text", text=json.dumps({"deleted": str(p)}))]

    # ── get_system_info ────────────────────────────────────────────────────────
    if name == "get_system_info":
        cpu_pct = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(r"c:\\")

        top_procs = sorted(
            psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]),
            key=lambda p: p.info.get("cpu_percent") or 0,
            reverse=True,
        )[:10]
        procs_out = []
        for proc in top_procs:
            try:
                procs_out.append(
                    {
                        "pid": proc.pid,
                        "name": proc.name(),
                        "cpu_pct": proc.cpu_percent(),
                        "mem_mb": round(proc.memory_info().rss / 1024 / 1024, 1),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        info = {
            "platform": platform.platform(),
            "hostname": platform.node(),
            "uptime_hours": round(
                (datetime.now().timestamp() - psutil.boot_time()) / 3600, 1
            ),
            "cpu": {"cores": psutil.cpu_count(), "percent": cpu_pct},
            "memory": {
                "total_gb": round(mem.total / 1e9, 1),
                "used_gb": round(mem.used / 1e9, 1),
                "percent": mem.percent,
            },
            "disk_c": {
                "total_gb": round(disk.total / 1e9, 1),
                "free_gb": round(disk.free / 1e9, 1),
                "percent": disk.percent,
            },
            "python": sys.version,
            "top_processes": procs_out,
        }
        return [types.TextContent(type="text", text=json.dumps(info, indent=2))]

    # ── manage_process ─────────────────────────────────────────────────────────
    if name == "manage_process":
        action = arguments["action"]

        if action == "list":
            name_filter = arguments.get("name_filter", "").lower()
            procs = []
            for p in psutil.process_iter(["pid", "name", "status", "create_time"]):
                try:
                    if name_filter and name_filter not in p.name().lower():
                        continue
                    procs.append(
                        {
                            "pid": p.pid,
                            "name": p.name(),
                            "status": p.status(),
                            "started": datetime.fromtimestamp(
                                p.create_time()
                            ).isoformat(),
                            "mem_mb": round(p.memory_info().rss / 1024 / 1024, 1),
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {"processes": procs, "count": len(procs)}, indent=2
                    ),
                )
            ]

        if action == "kill":
            pid = arguments.get("pid")
            if not pid:
                return [
                    types.TextContent(
                        type="text", text=json.dumps({"error": "pid required for kill"})
                    )
                ]
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps({"killed": pid, "name": proc.name()}),
                    )
                ]
            except psutil.NoSuchProcess:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps({"error": f"No process with pid {pid}"}),
                    )
                ]

        if action == "start":
            cmd = arguments.get("command")
            cwd = arguments.get("cwd", r"c:\kortana")
            if not cmd:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps({"error": "command required for start"}),
                    )
                ]
            proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", cmd],
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            return [
                types.TextContent(
                    type="text", text=json.dumps({"started": cmd, "pid": proc.pid})
                )
            ]

    # ── git_operation ──────────────────────────────────────────────────────────
    if name == "git_operation":
        operation = arguments["operation"]
        repo = arguments.get("repo_path", r"c:\kortana\backend")
        extra = arguments.get("args", "")

        git_cmds = {
            "status": "git status --short",
            "diff": f"git diff {extra}",
            "add": f"git add {extra or '.'}",
            "commit": f'git commit -m "{extra}"',
            "push": f"git push {extra}",
            "pull": f"git pull {extra}",
            "branch": f"git branch {extra}",
            "log": f"git log --oneline -20 {extra}",
            "checkout": f"git checkout {extra}",
        }
        cmd = git_cmds.get(operation, f"git {operation} {extra}")
        result = await _run_proc(
            cmd, shell=True, cwd=repo, capture_output=True, text=True, timeout=30
        )
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "operation": operation,
                        "stdout": _truncate(result.stdout),
                        "stderr": _truncate(result.stderr),
                        "exit_code": result.returncode,
                    },
                    indent=2,
                ),
            )
        ]

    # ── search_files ───────────────────────────────────────────────────────────
    if name == "search_files":
        pattern = arguments["pattern"]
        search_path = arguments["path"]
        file_glob = arguments.get("file_glob", "*")
        case_flag = "" if arguments.get("case_sensitive", False) else "-i"

        # prefer rg (ripgrep) if available, fall back to powershell Select-String
        rg = shutil.which("rg")
        if rg:
            glob_arg = f"--glob {file_glob}" if file_glob != "*" else ""
            cmd = f'rg {case_flag} --line-number --with-filename {glob_arg} "{pattern}" "{search_path}"'
        else:
            cmd = f'Get-ChildItem -Path "{search_path}" -Recurse -Filter "{file_glob}" | Select-String {case_flag} "{pattern}"'

        result = await _run_proc(
            ["powershell", "-NoProfile", "-Command", cmd] if not rg else cmd,
            shell=bool(rg),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return [
            types.TextContent(
                type="text", text=_truncate(result.stdout or result.stderr)
            )
        ]

    # ── take_screenshot ────────────────────────────────────────────────────────
    if name == "take_screenshot":
        out = arguments.get("output_path", r"c:\kortana\logs\screenshot.png")
        out_path = _safe_path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $screen.Width,$screen.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($screen.Location,[System.Drawing.Point]::Empty,$screen.Size)
$bmp.Save('{out_path}')
$g.Dispose(); $bmp.Dispose()
Write-Host "saved"
"""
        result = await _run_proc(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return [
                types.TextContent(
                    type="text", text=json.dumps({"screenshot": str(out_path)})
                )
            ]
        return [
            types.TextContent(type="text", text=json.dumps({"error": result.stderr}))
        ]

    # ── get_clipboard ──────────────────────────────────────────────────────────
    if name == "get_clipboard":
        result = await _run_proc(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return [
            types.TextContent(
                type="text", text=json.dumps({"clipboard": result.stdout.strip()})
            )
        ]

    # ── set_clipboard ──────────────────────────────────────────────────────────
    if name == "set_clipboard":
        text = arguments["text"].replace("'", "''")
        await _run_proc(
            ["powershell", "-NoProfile", "-Command", f"Set-Clipboard '{text}'"],
            capture_output=True,
            timeout=5,
        )
        return [types.TextContent(type="text", text=json.dumps({"set": True}))]

    # ── environment_vars ───────────────────────────────────────────────────────
    if name == "environment_vars":
        action = arguments["action"]
        if action == "list":
            safe_keys = [
                k
                for k in os.environ
                if "secret" not in k.lower()
                and "key" not in k.lower()
                and "token" not in k.lower()
                and "password" not in k.lower()
            ]
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({k: os.environ[k] for k in safe_keys}, indent=2),
                )
            ]
        if action == "get":
            var_name = arguments.get("name", "")
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({var_name: os.environ.get(var_name, "")}),
                )
            ]
        if action == "set":
            os.environ[arguments["name"]] = arguments.get("value", "")
            return [
                types.TextContent(
                    type="text", text=json.dumps({"set": arguments["name"]})
                )
            ]

    # ── speak ──────────────────────────────────────────────────────────────────
    if name == "speak":
        text = arguments["text"].replace("'", "''").replace('"', '""')
        rate = arguments.get("rate", 175)
        ps = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = {max(-10, min(10, (rate - 175) // 25))}
$synth.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Female)
$synth.Speak('{text}')
"""
        result = await _run_proc(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {"spoken": result.returncode == 0, "text": arguments["text"][:80]}
                ),
            )
        ]

    # ── notify ─────────────────────────────────────────────────────────────────
    if name == "notify":
        title = arguments["title"]
        message = arguments["message"]
        ps = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml(\"<toast><visual><binding template='ToastGeneric'><text>{title}</text><text>{message}</text></binding></visual></toast>\")
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier(\"kor'tana\").Show($toast)
"""
        result = await _run_proc(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=8,
        )
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"notified": result.returncode == 0, "title": title}),
            )
        ]

    # ── queue_local_task ───────────────────────────────────────────────────────
    if name == "queue_local_task":
        import json as _json

        task_file = Path(r"c:\kortana\mcp-server\local_tasks.json")
        tasks = []
        if task_file.exists():
            try:
                tasks = _json.loads(task_file.read_text(encoding="utf-8"))
            except Exception:
                tasks = []
        task = {
            **arguments,
            "status": "pending",
            "queued_at": datetime.utcnow().isoformat(),
        }
        tasks.append(task)
        task_file.write_text(_json.dumps(tasks, indent=2), encoding="utf-8")
        return [
            types.TextContent(
                type="text",
                text=_json.dumps({"queued": True, "task_count": len(tasks)}),
            )
        ]

    # ── memory_write ───────────────────────────────────────────────────────────
    if name == "memory_write":
        content = arguments["content"]
        memory_type = arguments.get("memory_type", "long_term")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{KORTANA_BACKEND}/api/consciousness/memory/store",
                    json={
                        "content": content,
                        "memory_type": memory_type,
                        "agent_id": "kortana-mcp",
                    },
                )
            data = (
                r.json()
                if r.status_code == 200
                else {"error": r.text[:200], "status_code": r.status_code}
            )
        except Exception as e:
            data = {"error": str(e)}
        return [types.TextContent(type="text", text=json.dumps(data, indent=2))]

    # ── memory_search ──────────────────────────────────────────────────────────
    if name == "memory_search":
        query = arguments["query"]
        limit = arguments.get("limit", 5)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{KORTANA_BACKEND}/api/consciousness/memory/search",
                    params={"q": query, "limit": limit},
                )
            data = (
                r.json()
                if r.status_code == 200
                else {"error": r.text[:200], "status_code": r.status_code}
            )
        except Exception as e:
            data = {"error": str(e)}
        return [types.TextContent(type="text", text=json.dumps(data, indent=2))]

    # ── memory_recall ──────────────────────────────────────────────────────────
    if name == "memory_recall":
        limit = arguments.get("limit", 20)
        session_id = arguments.get("session_id", "default")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{KORTANA_BACKEND}/api/gemini/chat/history",
                    params={"session_id": session_id, "limit": limit},
                )
            data = (
                r.json()
                if r.status_code == 200
                else {"error": r.text[:200], "status_code": r.status_code}
            )
        except Exception as e:
            data = {"error": str(e)}
        return [types.TextContent(type="text", text=json.dumps(data, indent=2))]

    # ── revelation_read ────────────────────────────────────────────────────────
    if name == "revelation_read":
        limit = arguments.get("limit", 5)
        unsurfaced_only = arguments.get("unsurfaced_only", True)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{KORTANA_BACKEND}/api/consciousness/memory/revelations",
                    params={
                        "limit": limit,
                        "unsurfaced_only": str(unsurfaced_only).lower(),
                    },
                )
            data = (
                r.json()
                if r.status_code == 200
                else {"error": r.text[:200], "status_code": r.status_code}
            )
        except Exception as e:
            data = {"error": str(e)}
        return [types.TextContent(type="text", text=json.dumps(data, indent=2))]

    # ── cognitive_identity ─────────────────────────────────────────────────────
    if name == "cognitive_identity":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{KORTANA_BACKEND}/api/voice/identity")
            data = r.json() if r.status_code == 200 else {"error": r.text[:200]}
        except Exception as e:
            data = {"error": str(e)}
        return [types.TextContent(type="text", text=json.dumps(data, indent=2))]

    # ── cognitive_dreams ───────────────────────────────────────────────────────
    if name == "cognitive_dreams":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{KORTANA_BACKEND}/api/voice/dreams")
            data = r.json() if r.status_code == 200 else {"error": r.text[:200]}
        except Exception as e:
            data = {"error": str(e)}
        return [types.TextContent(type="text", text=json.dumps(data, indent=2))]

    # ── cognitive_daemon ───────────────────────────────────────────────────────
    if name == "cognitive_daemon":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{KORTANA_BACKEND}/api/daemon/status")
            data = r.json() if r.status_code == 200 else {"error": r.text[:200]}
        except Exception as e:
            data = {"error": str(e)}
        return [types.TextContent(type="text", text=json.dumps(data, indent=2))]

    # ── cognitive_providers ────────────────────────────────────────────────────
    if name == "cognitive_providers":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{KORTANA_BACKEND}/api/health")
            if r.status_code == 200:
                health = r.json()
                data = {
                    "providers": health.get("model_providers", []),
                    "consensus_engine": health.get("consensus_engine", {}),
                }
            else:
                data = {"error": r.text[:200]}
        except Exception as e:
            data = {"error": str(e)}
        return [types.TextContent(type="text", text=json.dumps(data, indent=2))]

    return [
        types.TextContent(
            type="text", text=json.dumps({"error": f"Unknown tool: {name}"})
        )
    ]


# ── entrypoint ─────────────────────────────────────────────────────────────────


async def main() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="kortana-pc",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
