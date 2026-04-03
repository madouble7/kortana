"""
GitHub Autonomy Service for Kor'tana
Manages the autonomous development loop: monitoring issues, planning, and executing changes.
"""

import inspect
import json
import os
import re
import shutil
import subprocess
import tempfile
from base64 import b64encode
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from typing import Any

import httpx
from sqlalchemy import select

from src.kortana.config import get_settings
from src.kortana.http_client import get_http_client
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask
from src.kortana.services.ai_consensus import ConsensusMode, get_consensus_engine
from src.kortana.services.gemini import gemini_service
from src.kortana.services.operator_directive_service import OperatorDirectiveService
from src.kortana.services.repository_boundary_service import RepositoryBoundaryService
from src.kortana.services.workspace_bridge_service import get_workspace_bridge

from .code_generator import CodeGenerator

logger = get_logger(__name__)
settings = get_settings()
_REPO_SCAN_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "htmlcov",
    ".backup",
    "logs",
}
_REPO_CONTEXT_PREFERRED_FILES = (
    "backend/src/kortana/main.py",
    "backend/src/kortana/services/autonomy_daemon.py",
    "backend/src/kortana/services/github_autonomy_service.py",
    "backend/src/kortana/services/autonomy_controller.py",
    "backend/src/kortana/routers/always_on.py",
    "backend/tests/test_autonomy_daemon.py",
    "backend/tests/test_autonomy.py",
    "frontend/src/main.tsx",
    "app/app/page.tsx",
    "src/server.ts",
    "Dockerfile",
    "backend/Dockerfile",
    "docker-compose.yml",
    "package.json",
    "backend/requirements.txt",
)
_PROTECTED_PATH_PATTERNS = (
    ".env",
    ".env.*",
    "**/.env",
    "**/.env.*",
    "*.pem",
    "*.key",
    "*.crt",
    "*.p12",
    "*.pfx",
    "*.secrets.*",
    "*secret*.json",
    "*secret*.yaml",
    "*secret*.yml",
    ".kortana/operator_inbox.md",
    ".kortana/OPERATOR_PROTOCOL.md",
)
_VALIDATION_COMMAND_PREFIXES = (
    "pytest",
    "python -m pytest",
    "py -m pytest",
    "python -m unittest",
    "py -m unittest",
    "python -m py_compile",
    "py -m py_compile",
    "ruff check",
    "python -m ruff check",
    "uv run pytest",
    "uv run ruff check",
    "poetry run pytest",
    "poetry run ruff check",
    "npm test",
    "npm run test",
    "npm run lint",
    "pnpm test",
    "pnpm run test",
    "pnpm lint",
    "pnpm run lint",
    "yarn test",
    "yarn lint",
    "go test",
    "cargo test",
)
_VALIDATION_KEYWORDS = ("test", "pytest", "lint", "check", "validate", "py_compile")


class TaskValidationFailure(RuntimeError):
    """Raised when task-scoped validation fails inside the isolated workspace."""

    def __init__(self, message: str, result: dict[str, Any]) -> None:
        super().__init__(message)
        self.result = result


class GitHubAutonomyService:
    """Service for autonomous GitHub-driven development"""

    def __init__(self, db_session=None):
        self.db = db_session
        self.code_gen = CodeGenerator()
        self.settings = get_settings()
        self.http_client = get_http_client()
        self.repo_root = self._resolve_repo_root()
        self._repo_inventory_cache: list[str] | None = None
        self._repo_shape_cache: dict[str, Any] | None = None
        self._workspace_modes: dict[str, str] = {}

        # Get GitHub token from environment first, then fallback to settings
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            self.github_token = self.settings.GITHUB_TOKEN

        # Validate token is actually set (not placeholder)
        if self.github_token and self.github_token.startswith("your_"):
            logger.warning(
                "GitHub token appears to be a placeholder, replacing with env var"
            )
            self.github_token = os.getenv("GITHUB_TOKEN", "")

        self.repo_owner = os.getenv("GITHUB_OWNER") or self.settings.GITHUB_OWNER
        self.repo_name = os.getenv("GITHUB_REPO") or self.settings.GITHUB_REPO
        self.max_retries = self.settings.TASK_MAX_RETRIES

        logger.info(
            f"GitHubAutonomyService initialized: {self.repo_owner}/{self.repo_name}"
        )
        logger.debug(f"GitHub token present: {bool(self.github_token)}")
        logger.debug(f"GitHubAutonomyService repo root: {self.repo_root}")

    def _github_mode(self) -> str:
        mode = (
            (os.getenv("KORTANA_GITHUB_MODE") or self.settings.KORTANA_GITHUB_MODE)
            .strip()
            .lower()
        )
        if mode in {"full", "deferred", "disabled"}:
            return mode
        return "full"

    def _should_fetch_github(self) -> bool:
        return self._github_mode() == "full"

    def _should_publish_to_github(self, task: GitHubTask) -> bool:
        return self._github_mode() == "full" and not self._is_local_task(task)

    @staticmethod
    def _is_quota_exhausted_plan(plan: str) -> bool:
        """Return True when the plan text is a Gemini quota-error fallback, not real JSON."""
        signals = (
            "quota limits",
            "RESOURCE_EXHAUSTED",
            "generative model is temporarily unavailable",
            "The system continues without Gemini",
            "Error during analysis:",
        )
        return any(s in plan for s in signals)

    @staticmethod
    def _is_local_task(task: GitHubTask) -> bool:
        repo = (task.github_repo or "").lower()
        classification = (task.classification or "").lower()
        return repo.startswith("local/") or classification in {"local", "self_repair"}

    def _resolve_repo_root(self) -> Path:
        return RepositoryBoundaryService().canonical_repo_root

    @staticmethod
    def _looks_like_repo_root(candidate: Path) -> bool:
        if not candidate.exists():
            return False

        if (candidate / ".git").exists():
            return True

        has_backend = (candidate / "backend").exists()
        has_frontend_surface = any(
            (candidate / marker).exists()
            for marker in (
                "frontend",
                "app",
                "src",
                "package.json",
                "docker-compose.yml",
            )
        )
        return has_backend and has_frontend_surface

    @staticmethod
    def _normalize_repo_path(path: str) -> str:
        normalized = path.replace("\\", "/").strip()
        while normalized.startswith("./"):
            normalized = normalized[2:]
        return normalized

    @staticmethod
    def _protected_path_reason(path: str) -> str | None:
        normalized = GitHubAutonomyService._normalize_repo_path(path)
        if not normalized:
            return None

        basename = PurePosixPath(normalized).name
        for pattern in _PROTECTED_PATH_PATTERNS:
            if fnmatch(normalized, pattern) or fnmatch(basename, pattern):
                return f"path matches protected pattern {pattern}"
        return None

    def _repo_inventory(self) -> list[str]:
        if self._repo_inventory_cache is not None:
            return self._repo_inventory_cache

        inventory: list[str] = []
        git_manifest = self._git_output(["git", "ls-files"])
        if git_manifest:
            inventory = [
                self._normalize_repo_path(line)
                for line in git_manifest.splitlines()
                if line.strip()
            ]
        else:
            for path in self.repo_root.rglob("*"):
                if not path.is_file():
                    continue
                relative = path.relative_to(self.repo_root)
                if any(part in _REPO_SCAN_SKIP_DIRS for part in relative.parts):
                    continue
                inventory.append(relative.as_posix())
                if len(inventory) >= 500:
                    break

        inventory = sorted(dict.fromkeys(item for item in inventory if item))
        self._repo_inventory_cache = inventory
        return inventory

    def _repo_shape(self) -> dict[str, Any]:
        if self._repo_shape_cache is not None:
            return self._repo_shape_cache

        inventory = self._repo_inventory()
        existing_files = set(inventory)
        roots = sorted(
            {
                PurePosixPath(item).parts[0]
                for item in inventory
                if len(PurePosixPath(item).parts) > 1
            }
        )
        extensions = sorted(
            {
                PurePosixPath(item).suffix.lower()
                for item in inventory
                if PurePosixPath(item).suffix
            }
        )

        sample_files: list[str] = []
        for preferred in _REPO_CONTEXT_PREFERRED_FILES:
            if preferred in existing_files:
                sample_files.append(preferred)
        for item in inventory:
            if item in sample_files:
                continue
            sample_files.append(item)
            if len(sample_files) >= 60:
                break

        self._repo_shape_cache = {
            "existing_files": existing_files,
            "roots": roots,
            "extensions": extensions,
            "sample_files": sample_files[:60],
        }
        return self._repo_shape_cache

    def _build_repo_context(self) -> str:
        shape = self._repo_shape()
        extensions = ", ".join(shape["extensions"][:12]) or "(none detected)"
        roots = ", ".join(shape["roots"][:12]) or "(repo root only)"
        sample_files = "\n".join(f"- {path}" for path in shape["sample_files"][:30])
        return (
            "Repository grounding:\n"
            f"- Workspace root: {self.repo_root}\n"
            f"- Existing top-level roots: {roots}\n"
            f"- Observed file extensions: {extensions}\n"
            "- Only reference files that already exist in this repository, or create new files "
            "inside an existing top-level root using an already-observed language/extension.\n"
            "- Do not invent new stacks, languages, or top-level directories.\n"
            "- Prefer modifying existing files over creating new ones.\n"
            "Representative files:\n"
            f"{sample_files}"
        )

    def _validate_file_change_against_repo(
        self, file_change: dict[str, Any], shape: dict[str, Any]
    ) -> str | None:
        path = self._normalize_repo_path(str(file_change.get("path", "")))
        if not path:
            return "path is empty"
        if re.match(r"^[A-Za-z]:", path):
            return "absolute Windows paths are not allowed"

        pure_path = PurePosixPath(path)
        if pure_path.is_absolute() or ".." in pure_path.parts:
            return "path escapes the repository root"
        protected_reason = self._protected_path_reason(path)
        if protected_reason is not None:
            return protected_reason

        action = str(file_change.get("action", "modify")).lower()
        if action in {"modify", "delete"} and path not in shape["existing_files"]:
            return "target file does not exist in the repository"

        if action == "create":
            if len(pure_path.parts) > 1 and pure_path.parts[0] not in shape["roots"]:
                return "top-level root is not present in the repository"

            suffix = pure_path.suffix.lower()
            if suffix and suffix not in shape["extensions"]:
                return f"file extension {suffix} is not present in the repository"

        return None

    def _sanitize_plan_for_repo(self, plan_text: str) -> str:
        try:
            parsed = CodeGenerator(str(self.repo_root)).parse_plan(plan_text)
        except Exception:
            return plan_text

        file_changes = parsed.get("files", [])
        if not file_changes:
            return plan_text

        shape = self._repo_shape()
        valid_changes: list[dict[str, Any]] = []
        validation_notes: list[str] = []

        for file_change in file_changes:
            normalized_change = {
                "path": self._normalize_repo_path(str(file_change.get("path", ""))),
                "action": str(file_change.get("action", "modify")).lower(),
                "content": file_change.get("content", ""),
                "dependencies": file_change.get("dependencies", []),
                "priority": int(file_change.get("priority", 0) or 0),
            }
            reason = self._validate_file_change_against_repo(normalized_change, shape)
            if reason is None:
                valid_changes.append(normalized_change)
            else:
                validation_notes.append(f"{normalized_change['path']}: {reason}")

        if len(valid_changes) == len(file_changes):
            return plan_text

        logger.warning(
            "Repo-grounded plan sanitization removed invalid file changes: "
            + " | ".join(validation_notes[:5])
        )

        sanitized_plan = {
            "description": parsed.get("description")
            or "Repo-grounded implementation plan",
            "FILE_CHANGES": valid_changes,
            "COMMANDS": parsed.get("commands", []),
            "TESTS": parsed.get("tests", []),
            "VALIDATION_NOTES": validation_notes,
        }
        return json.dumps(sanitized_plan, indent=2)

    def _plan_payload(self, plan_text: str) -> dict[str, Any]:
        try:
            payload = json.loads(plan_text or "{}")
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _planned_file_changes(self, plan_text: str) -> list[str]:
        payload = self._plan_payload(plan_text)
        files = payload.get("FILE_CHANGES") or payload.get("files") or []
        normalized: list[str] = []
        for item in files:
            if not isinstance(item, dict):
                continue
            candidate = self._normalize_repo_path(
                str(item.get("file") or item.get("path") or "")
            )
            if candidate and candidate not in normalized:
                normalized.append(candidate)
        return normalized

    def _planned_commands(self, plan_text: str) -> list[str]:
        payload = self._plan_payload(plan_text)
        commands = payload.get("COMMANDS") or payload.get("commands") or []
        return [str(command).strip() for command in commands if str(command).strip()]

    def _planned_tests(self, plan_text: str) -> list[str]:
        payload = self._plan_payload(plan_text)
        tests = payload.get("TESTS") or payload.get("tests") or []
        return [str(test).strip() for test in tests if str(test).strip()]

    def _validation_notes(self, plan_text: str) -> list[str]:
        payload = self._plan_payload(plan_text)
        notes = payload.get("VALIDATION_NOTES") or payload.get("validation_notes") or []
        return [str(note).strip() for note in notes if str(note).strip()]

    def _candidate_validation_commands(self, plan_text: str) -> list[str]:
        commands: list[str] = []
        max_commands = max(
            1,
            int(os.getenv("KORTANA_VALIDATION_MAX_COMMANDS", "3") or "3"),
        )

        for command in self._planned_tests(plan_text):
            normalized = " ".join(command.split())
            if normalized and normalized not in commands:
                commands.append(normalized)

        for command in self._planned_commands(plan_text):
            normalized = " ".join(command.split())
            if (
                normalized
                and normalized not in commands
                and self._looks_like_validation_command(normalized)
            ):
                commands.append(normalized)

        return commands[:max_commands]

    @staticmethod
    def _looks_like_validation_command(command: str) -> bool:
        lowered = " ".join(command.strip().split()).lower()
        if not lowered:
            return False
        if any(lowered.startswith(prefix) for prefix in _VALIDATION_COMMAND_PREFIXES):
            return True
        return any(keyword in lowered for keyword in _VALIDATION_KEYWORDS)

    @staticmethod
    def _truncate_output(value: str | None, limit: int = 4000) -> str:
        if not value:
            return ""
        text = value.strip()
        if len(text) <= limit:
            return text
        return text[: limit - 15] + "\n...[truncated]"

    def _execute_validation_command(
        self,
        command: str,
        workspace: Path,
        *,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        started_at = datetime.utcnow()
        try:
            completed = subprocess.run(
                command,
                cwd=workspace,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                shell=True,
            )
            duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
            return {
                "command": command,
                "status": "passed" if completed.returncode == 0 else "failed",
                "exit_code": completed.returncode,
                "stdout": self._truncate_output(completed.stdout),
                "stderr": self._truncate_output(completed.stderr),
                "duration_ms": duration_ms,
            }
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
            return {
                "command": command,
                "status": "failed",
                "exit_code": None,
                "stdout": self._truncate_output(exc.stdout or ""),
                "stderr": self._truncate_output(
                    (exc.stderr or "") + "\nCommand timed out"
                ),
                "duration_ms": duration_ms,
                "timeout": True,
            }
        except Exception as exc:
            duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
            return {
                "command": command,
                "status": "failed",
                "exit_code": None,
                "stdout": "",
                "stderr": self._truncate_output(str(exc)),
                "duration_ms": duration_ms,
            }

    def _run_task_scoped_validation(
        self,
        plan_text: str,
        workspace: Path,
    ) -> dict[str, Any]:
        commands = self._candidate_validation_commands(plan_text)
        if not commands:
            return {
                "status": "skipped",
                "commands": [],
                "runs": [],
                "executed_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "details": "No task-scoped validation commands were planned",
            }

        timeout_seconds = max(
            15,
            int(os.getenv("KORTANA_VALIDATION_TIMEOUT_SEC", "180") or "180"),
        )
        runs: list[dict[str, Any]] = []
        failed_commands: list[str] = []
        skipped_count = 0

        for command in commands:
            if not self._looks_like_validation_command(command):
                runs.append(
                    {
                        "command": command,
                        "status": "skipped",
                        "exit_code": None,
                        "stdout": "",
                        "stderr": "Command is not allowed for task-scoped validation",
                        "duration_ms": 0,
                    }
                )
                skipped_count += 1
                continue

            run = self._execute_validation_command(
                command,
                workspace,
                timeout_seconds=timeout_seconds,
            )
            runs.append(run)
            if run["status"] == "failed":
                failed_commands.append(command)

        executed_count = len([run for run in runs if run["status"] != "skipped"])
        failed_count = len(failed_commands)
        result = {
            "status": (
                "failed" if failed_count else "passed" if executed_count else "skipped"
            ),
            "commands": commands,
            "runs": runs,
            "executed_count": executed_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "details": (
                "All task-scoped validation commands passed"
                if failed_count == 0 and executed_count > 0
                else "No executable validation commands were allowed"
                if executed_count == 0
                else "Validation failures: " + ", ".join(failed_commands[:4])
            ),
        }

        if failed_count:
            raise TaskValidationFailure(
                "Task-scoped validation failed: " + ", ".join(failed_commands[:4]),
                result,
            )
        return result

    def _build_plan_validation_report(
        self,
        task: GitHubTask,
        plan_text: str,
    ) -> dict[str, Any]:
        planned_files = self._planned_file_changes(plan_text)
        validation_notes = self._validation_notes(plan_text)
        blocked_paths = [
            note.split(":", 1)[0].strip()
            for note in validation_notes
            if "protected pattern" in note
        ]
        validations = [
            {
                "name": "repo_grounding",
                "status": "adjusted" if validation_notes else "passed",
                "details": (
                    f"{len(validation_notes)} plan adjustments applied"
                    if validation_notes
                    else "Plan remained inside observed repository shape"
                ),
            },
            {
                "name": "protected_path_guard",
                "status": "blocked" if blocked_paths else "passed",
                "details": (
                    "Blocked protected paths: " + ", ".join(blocked_paths[:6])
                    if blocked_paths
                    else "No protected paths were requested"
                ),
            },
        ]
        return {
            "stage": "planning_complete",
            "updated_at": datetime.utcnow().isoformat(),
            "publish_target": (
                "github" if self._should_publish_to_github(task) else "local"
            ),
            "workspace_strategy": (
                "clone" if self._should_publish_to_github(task) else "worktree"
            ),
            "planned_files": planned_files,
            "planned_commands": self._planned_commands(plan_text),
            "planned_tests": self._planned_tests(plan_text),
            "validation_notes": validation_notes,
            "blocked_paths": blocked_paths,
            "validations": validations,
        }

    def _build_execution_validation_report(
        self,
        *,
        task: GitHubTask,
        normalized_files: list[str],
        dry_run: bool,
        publish_to_github: bool,
        workspace: Path,
        codegen_result: dict[str, Any],
        validation_result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        workspace_mode = (
            "repo"
            if dry_run
            else self._workspace_modes.get(
                str(workspace), "worktree" if not publish_to_github else "clone"
            )
        )
        created = [str(item) for item in codegen_result.get("created", [])]
        modified = [str(item) for item in codegen_result.get("modified", [])]
        deleted = [str(item) for item in codegen_result.get("deleted", [])]
        validation_status = str(
            (validation_result or {}).get("status") or "skipped"
        ).lower()
        validation_details = (
            str((validation_result or {}).get("details") or "")
            or "No task-scoped validation commands were planned"
        )
        validations = [
            {
                "name": "protected_path_guard",
                "status": "passed",
                "details": f"Checked {len(normalized_files)} changed files against protected patterns",
            },
            {
                "name": "code_generation",
                "status": "passed",
                "details": (
                    f"created={len(created)} modified={len(modified)} deleted={len(deleted)}"
                ),
            },
            {
                "name": "task_scoped_validation",
                "status": validation_status,
                "details": validation_details,
            },
            {
                "name": "artifact_publish",
                "status": "passed" if task.commit_sha or dry_run else "skipped",
                "details": (
                    f"commit={task.commit_sha or 'dry-run'} "
                    f"pr={task.github_pr_number or 'none'} "
                    f"target={'github' if publish_to_github else 'local'}"
                ),
            },
        ]
        return {
            "stage": "executed" if not dry_run else "dry_run",
            "updated_at": datetime.utcnow().isoformat(),
            "publish_target": "github" if publish_to_github else "local",
            "workspace_strategy": workspace_mode,
            "changed_files": normalized_files,
            "change_counts": {
                "created": len(created),
                "modified": len(modified),
                "deleted": len(deleted),
            },
            "validation_result": validation_result
            or {
                "status": "skipped",
                "commands": [],
                "runs": [],
                "executed_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "details": "No task-scoped validation commands were planned",
            },
            "commit_sha": task.commit_sha,
            "github_pr_number": task.github_pr_number,
            "validations": validations,
        }

    def _merge_validation_report(
        self,
        existing: Any,
        entry: dict[str, Any],
    ) -> dict[str, Any]:
        if isinstance(existing, dict):
            merged = dict(existing)
            history = list(merged.get("history") or [])
        else:
            merged = {}
            history = []

        history.append(entry)
        merged.update(entry)
        merged["history"] = history[-10:]
        return merged

    def _record_validation_report(
        self,
        task: GitHubTask,
        entry: dict[str, Any],
    ) -> None:
        task.validation_report = self._merge_validation_report(
            getattr(task, "validation_report", None),
            entry,
        )

    def _enforce_execution_paths(self, paths: list[str]) -> None:
        blocked = [
            path
            for path in paths
            if self._protected_path_reason(self._normalize_repo_path(path)) is not None
        ]
        if blocked:
            raise ValueError(
                "Execution attempted to touch protected paths: "
                + ", ".join(blocked[:6])
            )

    def _git_output(self, command: list[str], cwd: Path | None = None) -> str:
        working_dir = cwd or self.repo_root
        try:
            result = subprocess.run(
                self._git_command(command, safe_dir=working_dir),
                cwd=working_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _git_command(
        self, command: list[str], safe_dir: Path | None = None
    ) -> list[str]:
        if not command or command[0] != "git":
            return command
        safe_directories = {str(self.repo_root.resolve())}
        if safe_dir is not None:
            safe_directories.add(str(Path(safe_dir).resolve()))

        git_command = ["git"]
        for directory in sorted(safe_directories):
            git_command.extend(["-c", f"safe.directory={directory}"])
        git_command.extend(command[1:])
        return git_command

    @staticmethod
    async def _maybe_await(value: Any) -> Any:
        """Await value when needed, otherwise return it as-is."""
        if inspect.isawaitable(value):
            return await value
        return value

    async def _db_execute(self, stmt: Any) -> Any:
        """Execute a DB statement against async or sync-like test doubles."""
        if self.db is None:
            raise RuntimeError("Database session is not initialized")
        return await self._maybe_await(self.db.execute(stmt))

    async def _db_commit(self) -> None:
        """Commit DB transaction for async or sync-like test doubles."""
        if self.db is None:
            return
        await self._maybe_await(self.db.commit())

    async def _db_rollback(self) -> None:
        """Rollback DB transaction for async or sync-like test doubles."""
        if self.db is None:
            return
        await self._maybe_await(self.db.rollback())

    async def _analyze_text_with_fallback(
        self,
        prompt: str,
        *,
        stage: str,
        task: GitHubTask,
        system_instruction: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        """Use Gemini first, then fall back to the multi-provider consensus engine."""
        gemini_response: str | None = None
        try:
            gemini_response = await self._maybe_await(
                gemini_service.analyze_text(
                    prompt,
                    **(
                        {"system_instruction": system_instruction}
                        if system_instruction
                        else {}
                    ),
                )
            )
        except Exception as exc:
            gemini_response = f"Error during analysis: {exc}"

        if gemini_response and not self._is_quota_exhausted_plan(gemini_response):
            return gemini_response

        logger.warning(
            "Gemini unavailable during %s for task #%s; attempting provider fallback",
            stage,
            task.github_issue_number,
        )

        fallback = await self._maybe_await(
            get_consensus_engine().query(
                prompt,
                mode=ConsensusMode.BEST,
                system=system_instruction,
                max_tokens=max_tokens,
                timeout=45.0,
            )
        )
        if fallback.answer and not fallback.answer.startswith("[ERROR]"):
            logger.info(
                "Fallback provider %s handled %s for task #%s",
                fallback.provider_used,
                stage,
                task.github_issue_number,
            )
            return fallback.answer

        logger.warning(
            "All fallback providers failed during %s for task #%s",
            stage,
            task.github_issue_number,
        )
        return gemini_response or "[ERROR] All providers failed"

    @staticmethod
    def _extract_http_error_detail(exc: Exception) -> tuple[int | None, str]:
        """Extract status code and body from HTTP errors when available."""
        if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
            response = exc.response
            detail = response.text
            try:
                payload = response.json()
                if isinstance(payload, dict):
                    detail = payload.get("message") or payload.get("error") or detail
            except ValueError:
                pass
            return response.status_code, detail
        return None, str(exc)

    def _validate_token(self) -> None:
        """Validate GitHub token is configured"""
        # Reload token from environment to support test mocks
        self.github_token = os.getenv("GITHUB_TOKEN") or get_settings().GITHUB_TOKEN
        if not self.github_token:
            raise ValueError("GitHub token not configured")

    async def _get_latest_reflection(self) -> str:
        """Return kor'tana's most recent cycle reflection as a context string."""
        try:
            from sqlalchemy import text as _ref_text

            result = await self._db_execute(
                _ref_text(
                    "SELECT content, cycle_number FROM reflections "
                    "ORDER BY created_at DESC LIMIT 1"
                )
            )
            row = result.fetchone()
            if row:
                return f"## my most recent self-reflection (cycle {row[1]})\n{row[0]}\n"
        except Exception:
            pass
        return ""

    async def _operator_preamble(self) -> str:
        """Return active operator steering for prompt conditioning."""
        try:
            summary = await OperatorDirectiveService(self.db).get_active_summary()
            workspace_context = get_workspace_bridge().prompt_context()
            if summary.prompt_preamble and workspace_context:
                return f"{summary.prompt_preamble}\n{workspace_context}"
            if workspace_context:
                return workspace_context
            return summary.prompt_preamble
        except Exception as e:
            logger.debug(f"Operator guidance unavailable for prompt build: {e}")
            return ""

    async def fetch_and_queue_issues(self, repo: str | None = None) -> list[GitHubTask]:
        """Fetch open issues from GitHub and queue them as tasks if not already present"""
        if not self._should_fetch_github():
            logger.info(
                "GitHub issue discovery skipped in %s mode", self._github_mode()
            )
            return []
        self._validate_token()

        owner, name = repo.split("/") if repo else (self.repo_owner, self.repo_name)
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        url = (
            f"https://api.github.com/repos/{owner}/{name}/issues?state=open&per_page=50"
        )

        try:
            response = await self.http_client.get(
                url, api_name="github_api", headers=headers, timeout=15
            )
            issues = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch GitHub issues: {str(e)}")
            return []

        queued_tasks = []
        issue_numbers = [
            issue["number"] for issue in issues if "pull_request" not in issue
        ]

        if not issue_numbers:
            return []

        # Check existing tasks
        from sqlalchemy import select

        stmt = select(GitHubTask.github_issue_number).where(
            GitHubTask.github_issue_number.in_(issue_numbers),
            GitHubTask.github_repo == f"{owner}/{name}",
        )
        result = await self._db_execute(stmt)
        existing_issue_numbers = {row[0] for row in result.all()}

        for issue in issues:
            if "pull_request" in issue:
                continue

            if issue["number"] in existing_issue_numbers:
                continue

            task = GitHubTask(
                github_issue_number=issue["number"],
                github_repo=f"{owner}/{name}",
                title=issue["title"],
                description=issue.get("body") or "",
                status="pending",
                priority=self._determine_priority(issue),
                branch_name=self._generate_branch_name(issue["number"], issue["title"]),
            )

            self.db.add(task)
            queued_tasks.append(task)

        if queued_tasks:
            try:
                await self._db_commit()
                logger.info(f"Queued {len(queued_tasks)} new tasks from GitHub")
            except Exception as e:
                await self._db_rollback()
                logger.error(f"Failed to commit new tasks: {str(e)}")

        return queued_tasks

    def fetch_and_queue_issues_sync(self, repo: str | None = None) -> list[dict]:
        """Sync wrapper for fetch_and_queue_issues - fetches GitHub issues synchronously"""
        if not self._should_fetch_github():
            logger.info(
                "GitHub issue discovery skipped in %s mode", self._github_mode()
            )
            return []
        self._validate_token()

        owner, name = repo.split("/") if repo else (self.repo_owner, self.repo_name)
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        url = (
            f"https://api.github.com/repos/{owner}/{name}/issues?state=open&per_page=50"
        )

        try:
            # Use sync httpx client for Celery compatibility
            response = httpx.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            issues = response.json()
            logger.info(f"Fetched {len(issues)} issues from {owner}/{name}")
            return [
                {"number": issue["number"], "title": issue["title"]} for issue in issues
            ]
        except Exception as e:
            logger.error(f"Failed to fetch GitHub issues: {str(e)}")
            return []

    def _determine_priority(self, issue: dict[str, Any]) -> str:
        """Determine priority from labels"""
        labels = [label.get("name", "").lower() for label in issue.get("labels", [])]
        if any(label in ["critical", "p0", "urgent", "bug"] for label in labels):
            return "high"
        elif any(label in ["p2", "low", "chore"] for label in labels):
            return "low"
        return "medium"

    def _generate_branch_name(self, issue_num: int, title: str) -> str:
        """Generate safe branch name"""
        safe_title = "".join(c if c.isalnum() else "-" for c in title.lower())
        safe_title = "-".join(filter(None, safe_title.split("-")))[:50]
        return f"auto-fix/{issue_num}-{safe_title}"

    async def process_next_tasks(self, limit: int = 5):
        """Process tasks through the pipeline: Pending -> Analyzing -> Planning -> Executing"""
        from sqlalchemy import select

        # 1. Analyze pending tasks - batch fetch and process
        stmt = select(GitHubTask).where(GitHubTask.status == "pending").limit(limit)
        result = await self._db_execute(stmt)
        pending = result.scalars().all()
        for task in pending:
            await self.analyze_task(task)

        # 2. Plan analyzed tasks - batch fetch and process
        stmt = select(GitHubTask).where(GitHubTask.status == "analyzed").limit(limit)
        result = await self._db_execute(stmt)
        analyzed = result.scalars().all()
        for task in analyzed:
            await self.plan_task(task)

        # 3. Execute planned tasks (only if autonomous mode is enabled) - batch fetch and process
        if (
            self.settings.ENVIRONMENT == "production"
            or os.getenv("KORTANA_AUTONOMOUS_MODE") == "true"
        ):
            stmt = (
                select(GitHubTask)
                .where(GitHubTask.status == "planning_complete")
                .limit(limit)
            )
            result = await self._db_execute(stmt)
            planned = result.scalars().all()
            for task in planned:
                await self.execute_task(task)

    async def analyze_task(self, task_or_id: GitHubTask | str) -> GitHubTask:
        """Analyze task with Gemini"""
        if isinstance(task_or_id, str):
            stmt = select(GitHubTask).where(GitHubTask.id == task_or_id)
            result = await self._db_execute(stmt)
            task = result.scalar_one_or_none()
            if not task:
                raise ValueError("Task not found")
        else:
            task = (
                task_or_id  # Already have the task object, no additional query needed
            )

        task.status = "analyzing"
        await self._db_commit()

        try:
            logger.info(f"Analyzing task #{task.github_issue_number}: {task.title}")
            # Post a pickup comment to the GitHub issue (best-effort)
            _issue_num = int(task.github_issue_number or 0)
            if _issue_num > 0:
                await self.post_issue_comment(
                    task,
                    "kor'tana — picking this up now. analyzing and planning a fix.",
                )
            operator_preamble = await self._operator_preamble()
            reflection_ctx = await self._get_latest_reflection()
            repo_context = self._build_repo_context()
            prompt = (
                (f"{operator_preamble}\n\n" if operator_preamble else "")
                + (f"{reflection_ctx}\n" if reflection_ctx else "")
                + (
                    f"we are kor'tana prime, an autonomous ai architect modifying our own application (or another repository).\n"
                    f"Analyze this issue and provide expert-level implementation insights. "
                    f"If this is a [SELF-REPAIR] issue, you must diagnose the internal autonomy logic flaw causing the error and architect a structural fix.\n\n"
                    f"{repo_context}\n\n"
                    f"Title: {task.title}\nDescription: {task.description}"
                )
            )
            analysis = await self._analyze_text_with_fallback(
                prompt,
                stage="analysis",
                task=task,
                max_tokens=1800,
            )

            # Detect quota-exhaustion fallback — defer instead of storing garbage analysis.
            if self._is_quota_exhausted_plan(analysis):
                logger.warning(
                    f"Gemini quota exhausted during analysis of task #{task.github_issue_number} — deferring"
                )
                task.status = "pending"
                task.error_message = "Gemini quota exhausted — deferred for retry"
                await self._db_commit()
                return task

            task.analysis = analysis
            task.status = "analyzed"
            task.analyzed_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            task.status = "pending"
            task.error_message = str(e)
            task.error_count = (task.error_count or 0) + 1
            if task.error_count >= self.max_retries:
                task.status = "failed"

        await self._db_commit()
        return task

    async def plan_task(self, task_or_id: GitHubTask | str) -> GitHubTask:
        """Generate implementation plan with Gemini"""
        if isinstance(task_or_id, str):
            stmt = select(GitHubTask).where(GitHubTask.id == task_or_id)
            result = await self._db_execute(stmt)
            task = result.scalar_one_or_none()
            if not task:
                raise ValueError("Task not found")
        else:
            task = (
                task_or_id  # Already have the task object, no additional query needed
            )

        task.status = "planning"
        await self._db_commit()

        try:
            logger.info(f"Planning task #{task.github_issue_number}")
            operator_preamble = await self._operator_preamble()
            repo_context = self._build_repo_context()
            prompt = (f"{operator_preamble}\n\n" if operator_preamble else "") + (
                f"we are kor'tana prime, an autonomous ai entity architecting our own codebase. "
                f"Generate a detailed file-by-file implementation plan for this issue and keep it grounded to this repository only. "
                f"If the request cannot be satisfied safely inside the observed repo structure, return FILE_CHANGES as an empty list. "
                f"You MUST output ONLY a valid JSON object matching this schema:\n"
                f"{{\n"
                f'  "FILE_CHANGES": [\n'
                f"    {{\n"
                f'      "file": "path/to/file.py",\n'
                f'      "action": "create|modify|delete",\n'
                f'      "content": "raw code content here"\n'
                f"    }}\n"
                f"  ]\n"
                f"}}\n"
                f"Strict constraints:\n"
                f"{repo_context}\n\n"
                f"Title: {task.title}\nAnalysis: {task.analysis}"
            )
            raw_plan = await self._analyze_text_with_fallback(
                prompt,
                stage="planning",
                task=task,
                max_tokens=3200,
            )

            # Detect quota-exhaustion fallback — defer instead of storing garbage plans.
            if self._is_quota_exhausted_plan(raw_plan):
                logger.warning(
                    f"Gemini quota exhausted for task #{task.github_issue_number} — deferring"
                )
                task.status = "pending"
                task.error_message = "Gemini quota exhausted — deferred for retry"
                await self._db_commit()
                return task

            plan = self._sanitize_plan_for_repo(raw_plan)
            task.plan = plan
            self._record_validation_report(
                task,
                self._build_plan_validation_report(task, plan),
            )
            task.status = "planning_complete"
        except Exception as e:
            logger.error(f"Planning failed: {str(e)}")
            task.status = "analyzed"
            task.error_message = str(e)
            task.error_count = (task.error_count or 0) + 1
            if task.error_count >= self.max_retries:
                task.status = "failed"

        await self._db_commit()
        return task

    async def execute_task(
        self, task_or_id: GitHubTask | str, dry_run: bool = False
    ) -> GitHubTask:
        """Execute the task: Create branch, apply changes, and commit"""
        if isinstance(task_or_id, str):
            stmt = select(GitHubTask).where(GitHubTask.id == task_or_id)
            result = await self._db_execute(stmt)
            task = result.scalar_one_or_none()
            if not task:
                raise ValueError("Task not found")
        else:
            task = (
                task_or_id  # Already have the task object, no additional query needed
            )

        task.status = "executing"
        await self._db_commit()

        workspace: Path | None = None
        publish_to_github = not dry_run and self._should_publish_to_github(task)
        validation_result: dict[str, Any] | None = None
        try:
            logger.info(f"Executing task #{task.github_issue_number}")

            # Pre-flight: refuse to execute if the plan is a quota-error fallback.
            if not task.plan or self._is_quota_exhausted_plan(task.plan):
                logger.warning(
                    f"Task #{task.github_issue_number} has no valid plan — deferring"
                )
                task.status = "pending"
                task.error_message = (
                    "No valid plan — deferred for retry when quota resets"
                )
                await self._db_commit()
                return task

            # 1. Create GitHub branch
            if publish_to_github:
                if not await self._maybe_await(self._create_branch(task)):
                    raise Exception(
                        task.error_message or "Failed to create GitHub branch"
                    )

            workspace = (
                self.repo_root
                if dry_run
                else await self._prepare_execution_workspace(task)
            )

            # 2. Use CodeGenerator to apply changes
            result = self.code_gen.generate_from_gemini_plan(
                task.plan, repo_path=str(workspace), dry_run=dry_run
            )

            if result.get("errors"):
                raise Exception(f"Code generation errors: {result['errors']}")

            files_changed = [
                str(path)
                for path in (
                    result.get("created", [])
                    + result.get("modified", [])
                    + result.get("deleted", [])
                )
            ]
            normalized_files = self._normalize_changed_files(files_changed, workspace)
            self._enforce_execution_paths(normalized_files)
            task.code_changes = normalized_files or None
            validation_result = self._run_task_scoped_validation(
                task.plan or "", workspace
            )

            # 3. Commit changes to the branch (if not dry-run)
            if not dry_run:
                if normalized_files:
                    commit_sha = await self._commit_workspace_changes(
                        task, normalized_files, workspace
                    )
                    if not commit_sha:
                        raise Exception("Failed to commit changes")
                    task.commit_sha = commit_sha

                    if publish_to_github:
                        # 4. Push branch to GitHub
                        if not await self._push_workspace_branch(task, workspace):
                            raise Exception("Failed to push branch")

                        # 5. Create pull request
                        pr_number = await self._create_pull_request_for_branch(task)
                        if pr_number:
                            task.github_pr_number = pr_number
                            logger.info(
                                f"Created PR #{pr_number} for task #{task.github_issue_number}"
                            )
                    else:
                        logger.info(
                            "Executed task %s locally on branch %s without GitHub publish",
                            task.id,
                            task.branch_name,
                        )
                elif publish_to_github and not self._is_local_task(task):
                    # Code generator produced no file changes — plan was abstract.
                    # Defer the task so it can be retried or handled differently.
                    logger.warning(
                        f"Task #{task.github_issue_number} produced no code changes — deferring"
                    )
                    task.status = "pending"
                    task.error_message = (
                        "Plan produced no file changes — deferred for retry"
                    )
                    await self._db_commit()
                    return task

            self._record_validation_report(
                task,
                self._build_execution_validation_report(
                    task=task,
                    normalized_files=normalized_files,
                    dry_run=dry_run,
                    publish_to_github=publish_to_github,
                    workspace=workspace,
                    codegen_result=result,
                    validation_result=validation_result,
                ),
            )

            task.status = "executed"
            task.executed_at = datetime.utcnow()
            await self._db_commit()
            return task
        except Exception as e:
            logger.error(f"Execution failed: {str(e)}")
            failure_details = (
                dict(e.result)
                if isinstance(e, TaskValidationFailure)
                else validation_result or None
            )
            self._record_validation_report(
                task,
                {
                    "stage": "execution_failed",
                    "updated_at": datetime.utcnow().isoformat(),
                    "publish_target": "github" if publish_to_github else "local",
                    "workspace_strategy": (
                        "repo"
                        if dry_run
                        else self._workspace_modes.get(
                            str(workspace),
                            "worktree" if not publish_to_github else "clone",
                        )
                        if workspace is not None
                        else None
                    ),
                    "error": str(e),
                    "validation_result": failure_details,
                },
            )
            task.status = "planning_complete"
            task.error_message = str(e)
            task.error_count = (task.error_count or 0) + 1
            if task.error_count >= self.max_retries:
                task.status = "failed"
            await self._db_commit()
            raise
        finally:
            if workspace is not None and not dry_run:
                await self._cleanup_execution_workspace(workspace)

    async def _prepare_execution_workspace(self, task: GitHubTask) -> Path:
        if self._should_publish_to_github(task):
            return await self._prepare_remote_execution_workspace(task)
        return await self._prepare_local_execution_workspace(task)

    async def _prepare_remote_execution_workspace(self, task: GitHubTask) -> Path:
        """Clone the repo into an isolated temp workspace and check out the task branch."""
        workspace = Path(
            tempfile.mkdtemp(prefix=f"kortana-task-{task.github_issue_number}-")
        )
        self._workspace_modes[str(workspace)] = "clone"
        self._run_git(
            ["git", "clone", str(self.repo_root), str(workspace)], cwd=self.repo_root
        )

        origin_url = self._git_output(["git", "remote", "get-url", "origin"])
        if origin_url:
            self._run_git(
                ["git", "remote", "set-url", "origin", origin_url],
                cwd=workspace,
            )

        try:
            self._run_git(["git", "fetch", "origin", task.branch_name], cwd=workspace)
            self._run_git(
                [
                    "git",
                    "checkout",
                    "-B",
                    task.branch_name,
                    f"origin/{task.branch_name}",
                ],
                cwd=workspace,
            )
        except subprocess.CalledProcessError:
            base_ref = "origin/main"
            try:
                self._run_git(["git", "fetch", "origin", "main"], cwd=workspace)
            except subprocess.CalledProcessError:
                self._run_git(["git", "fetch", "origin", "master"], cwd=workspace)
                base_ref = "origin/master"
            self._run_git(
                ["git", "checkout", "-B", task.branch_name, base_ref],
                cwd=workspace,
            )

        return workspace

    async def _prepare_local_execution_workspace(self, task: GitHubTask) -> Path:
        """Create an isolated local worktree so commits persist without GitHub."""
        workspace = Path(
            tempfile.mkdtemp(prefix=f"kortana-local-{abs(task.github_issue_number)}-")
        )
        shutil.rmtree(workspace, ignore_errors=True)
        self._workspace_modes[str(workspace)] = "worktree"

        branch_name = task.branch_name or self._generate_branch_name(
            abs(task.github_issue_number or 1),
            task.title,
        )
        task.branch_name = branch_name
        base_ref = self._resolve_local_base_ref()

        if self._local_branch_exists(branch_name):
            self._run_git(["git", "worktree", "add", str(workspace), branch_name])
        else:
            self._run_git(
                ["git", "worktree", "add", "-b", branch_name, str(workspace), base_ref]
            )

        return workspace

    def _resolve_local_base_ref(self) -> str:
        current_branch = self._git_output(["git", "branch", "--show-current"])
        if current_branch:
            return current_branch

        for candidate in ("main", "master"):
            if self._local_branch_exists(candidate):
                return candidate
        return "HEAD"

    def _local_branch_exists(self, branch_name: str) -> bool:
        try:
            self._run_git(["git", "rev-parse", "--verify", f"refs/heads/{branch_name}"])
            return True
        except subprocess.CalledProcessError:
            return False

    def _normalize_changed_files(
        self, files_changed: list[str], workspace: Path
    ) -> list[str]:
        normalized: list[str] = []
        workspace_root = workspace.resolve()
        repo_root = self.repo_root.resolve()
        for item in files_changed:
            candidate = Path(item)
            value = str(item).replace("\\", "/").lstrip("./")
            try:
                resolved = candidate.resolve()
            except Exception:
                resolved = None

            if resolved is not None:
                try:
                    value = resolved.relative_to(workspace_root).as_posix()
                except ValueError:
                    try:
                        value = resolved.relative_to(repo_root).as_posix()
                    except ValueError:
                        value = str(item).replace("\\", "/").lstrip("./")

            if value and value not in normalized:
                normalized.append(value)
        return normalized

    async def _commit_workspace_changes(
        self,
        task: GitHubTask,
        files_changed: list[Any],
        workspace: Path,
    ) -> str | None:
        """Commit changed files in an isolated workspace and return the new SHA."""
        try:
            for file_path in files_changed:
                self._run_git(["git", "add", str(file_path)], cwd=workspace)

            commit_message = (
                f"Auto: Resolve issue #{task.github_issue_number}\n\n"
                f"Issue: {task.title}\n"
                f"Branch: {task.branch_name}"
            )
            self._run_git(
                ["git", "commit", "--no-verify", "-m", commit_message],
                cwd=workspace,
            )
            sha_result = self._run_git(
                ["git", "rev-parse", "HEAD"],
                cwd=workspace,
            )
            commit_sha = sha_result.stdout.strip()
            logger.info(f"Committed changes on {task.branch_name}: {commit_sha[:8]}...")
            return commit_sha or None
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit changes on {task.branch_name}: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Commit failed with exception: {str(e)}")
            return None

    async def _push_workspace_branch(self, task: GitHubTask, workspace: Path) -> bool:
        """Push the task branch from an isolated workspace without mutating origin URLs."""
        try:
            auth_header = self._build_push_auth_header()
            self._run_git(
                [
                    "git",
                    f"-chttp.extraheader={auth_header}",
                    "push",
                    "-u",
                    "origin",
                    f"{task.branch_name}:{task.branch_name}",
                ],
                cwd=workspace,
            )
            logger.info(f"Pushed branch {task.branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push branch {task.branch_name}: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Push failed with exception: {str(e)}")
            return False

    async def _cleanup_execution_workspace(self, workspace: Path) -> None:
        try:
            mode = self._workspace_modes.pop(str(workspace), "clone")
            if mode == "worktree":
                self._run_git(["git", "worktree", "remove", "--force", str(workspace)])
                shutil.rmtree(workspace, ignore_errors=True)
                return
            shutil.rmtree(workspace, ignore_errors=True)
        except Exception as exc:
            logger.warning(f"Failed to cleanup workspace {workspace}: {exc}")

    def _build_push_auth_header(self) -> str:
        if not self.github_token:
            raise ValueError("GitHub token not configured")
        token_bytes = f"x-access-token:{self.github_token}".encode("utf-8")
        encoded = b64encode(token_bytes).decode("ascii")
        return f"AUTHORIZATION: basic {encoded}"

    def _run_git(
        self, command: list[str], cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        working_dir = cwd or self.repo_root
        return subprocess.run(
            self._git_command(command, safe_dir=working_dir),
            cwd=working_dir,
            check=True,
            capture_output=True,
            text=True,
        )

    async def _create_branch(self, task: GitHubTask) -> bool:
        """Create GitHub branch for task using async httpx"""
        if not self._should_publish_to_github(task):
            return True
        if not self.github_token:
            logger.error("GitHub token not configured for branch creation")
            return False

        try:
            owner, repo = task.github_repo.split("/")
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Get main branch SHA
            ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/main"
            try:
                ref_response = await self.http_client.get(
                    ref_url, api_name="github_api", headers=headers, timeout=10
                )
                if ref_response.status_code != 200:
                    logger.debug(
                        f"Main branch not found (status {ref_response.status_code}), trying master"
                    )
                    raise Exception("Main branch not found")
            except Exception as e:
                logger.debug(
                    f"Getting main branch failed: {str(e)}, trying master branch"
                )
                # Try master branch
                ref_url = (
                    f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/master"
                )
                ref_response = await self.http_client.get(
                    ref_url, api_name="github_api", headers=headers, timeout=10
                )
                if ref_response.status_code != 200:
                    task.error_message = (
                        f"Failed to get master branch ({ref_response.status_code}): "
                        f"{ref_response.text}"
                    )
                    logger.error(task.error_message)
                    return False

            # Parse and validate main_sha
            try:
                main_sha = ref_response.json()["object"]["sha"]
                logger.debug(f"Got base branch SHA: {main_sha[:8]}...")
            except (KeyError, ValueError) as e:
                task.error_message = (
                    f"Failed to parse branch SHA from response: {str(e)}"
                )
                logger.error(f"Failed to parse branch SHA from response: {str(e)}")
                return False

            # Create branch (idempotent - handle existing branches)
            branch_data = {"ref": f"refs/heads/{task.branch_name}", "sha": main_sha}
            create_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
            logger.info(f"Creating branch: {task.branch_name}")

            try:
                create_response = await self.http_client.post(
                    create_url,
                    api_name="github_api",
                    headers=headers,
                    json=branch_data,
                    timeout=10,
                )
            except Exception as e:
                status_code, detail = self._extract_http_error_detail(e)
                if status_code == 422:
                    logger.info(
                        f"Branch already exists: {task.branch_name} (idempotent)"
                    )
                    return True

                if status_code is not None:
                    task.error_message = (
                        f"Branch creation failed with status {status_code}: {detail}"
                    )
                    logger.error(task.error_message)
                else:
                    task.error_message = (
                        f"Branch creation failed with exception: {detail}"
                    )
                    logger.error(task.error_message)
                return False

            # 201 = created, 422 = already exists (idempotent success)
            if create_response.status_code == 201:
                logger.info(f"Branch created successfully: {task.branch_name}")
                return True
            elif create_response.status_code == 422:
                logger.info(f"Branch already exists: {task.branch_name} (idempotent)")
                return True
            else:
                task.error_message = (
                    f"Branch creation failed with status "
                    f"{create_response.status_code}: {create_response.text}"
                )
                logger.error(task.error_message)
                return False
        except Exception as e:
            task.error_message = f"Branch creation failed with exception: {str(e)}"
            logger.error(task.error_message)
            return False

    async def _commit_branch_changes(
        self, task: GitHubTask, files_changed: list[Any]
    ) -> str | None:
        """Backward-compatible wrapper around isolated commits."""
        return await self._commit_workspace_changes(task, files_changed, self.repo_root)

    async def _push_branch(self, task: GitHubTask) -> bool:
        """Backward-compatible wrapper around isolated pushes."""
        return await self._push_workspace_branch(task, self.repo_root)

    async def post_issue_comment(self, task: GitHubTask, body: str) -> bool:
        """Post a comment to the GitHub issue"""
        if not self._should_publish_to_github(task):
            return True
        try:
            owner, repo = task.github_repo.split("/")
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{task.github_issue_number}/comments"
            payload = {"body": body}
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, headers=headers, json=payload, timeout=15
                )
            if response.status_code != 201:
                logger.error(
                    f"Failed to post comment to #{task.github_issue_number}: {response.text}"
                )
                return False
            return True
        except Exception as e:
            status_code, detail = self._extract_http_error_detail(e)
            logger.error(
                f"Error posting comment to issue #{task.github_issue_number}: {detail or str(e)}"
            )
            return False

    async def fetch_issue_comments(self, task: GitHubTask) -> list[dict[str, Any]]:
        """Fetch comments for a GitHub issue"""
        if not self._should_fetch_github():
            return []
        try:
            owner, repo = task.github_repo.split("/")
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{task.github_issue_number}/comments"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                logger.error(
                    f"Failed to fetch comments from #{task.github_issue_number}: {response.text}"
                )
                return []
            return response.json()
        except Exception as e:
            status_code, detail = self._extract_http_error_detail(e)
            logger.error(
                f"Error fetching comments for issue #{task.github_issue_number}: {detail or str(e)}"
            )
            return []

    async def _create_pull_request_for_branch(self, task: GitHubTask) -> int | None:
        """Create a pull request for the branch"""
        if not self._should_publish_to_github(task):
            return None
        try:
            owner, repo = task.github_repo.split("/")

            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Create PR from branch back to main
            pr_data = {
                "title": f"[AUTO] {task.title}",
                "body": f"Autonomous fix for issue #{task.github_issue_number}\n\nGenerated by KOR'TANA autonomy system",
                "head": task.branch_name,
                "base": "main",
            }

            # Fallback to master if main doesn't exist
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

            response = await self.http_client.post(
                url, api_name="github_api", headers=headers, json=pr_data, timeout=10
            )

            if response.status_code == 201:
                pr = response.json()
                pr_number = pr.get("number")
                logger.info(f"Created PR #{pr_number} for {task.branch_name}")
                return pr_number
            elif response.status_code == 422:
                # PR might already exist
                logger.warning(f"PR creation returned 422: {response.text}")
                return None
            else:
                logger.error(
                    f"PR creation failed with status {response.status_code}: {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"PR creation failed with exception: {str(e)}")
            return None

    def close(self):
        """Close database session safely"""
        if self.db:
            try:
                # Try to close gracefully
                if hasattr(self.db, "close"):
                    self.db.close()
            except Exception as e:
                logger.debug(f"Error closing database session: {e}")

    async def create_pull_request(
        self, title: str, body: str, head: str, base: str = "main"
    ) -> str | None:
        """
        Create a PR generic endpoint for Vector Alpha.
        Returns the PR URL if successful.
        """
        try:
            owner_repo = getattr(self.settings, "GITHUB_REPOSITORY", "KOR-TANA/kortana")
            if not owner_repo:
                owner_repo = "KOR-TANA/kortana"

            url = f"https://api.github.com/repos/{owner_repo}/pulls"

            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            pr_data = {"title": title, "body": body, "head": head, "base": base}

            response = await self.http_client.post(
                url, api_name="github_api", headers=headers, json=pr_data, timeout=10
            )

            if response.status_code == 201:
                pr = response.json()
                logger.info(f"[GitHub] Vector Alpha proposed PR: {pr.get('html_url')}")
                return pr.get("html_url")
            else:
                logger.error(
                    f"[GitHub] Failed to create pull request {head} -> {base}: {response.text}"
                )
                return None
        except Exception as e:
            logger.error(
                f"[GitHub] Failed to create pull request {head} -> {base}: {e}"
            )
            return None
