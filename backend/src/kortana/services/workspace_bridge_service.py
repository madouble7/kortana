"""
Workspace bridge service.

Polls local repository state and ingests operator comments from a local inbox
file so Kor'tana can react to editor-side activity without explicit API calls.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.kortana.config import get_settings
from src.kortana.logger import get_logger
from src.kortana.services.operator_directive_service import OperatorDirectiveService

logger = get_logger(__name__)


@dataclass
class WorkspaceSnapshot:
    repo_root: str
    branch: str = "unknown"
    dirty: bool = False
    changed_files: list[str] = field(default_factory=list)
    changed_count: int = 0
    inbox_path: str = ""
    inbox_exists: bool = False
    ingested_count: int = 0
    last_scan: str = ""
    last_inbox_digest: str | None = None


class WorkspaceBridgeService:
    """Bridge local workspace signals into the always-on autonomy loop."""

    def __init__(self) -> None:
        settings = get_settings()
        configured_root = Path(os.getenv("KORTANA_WORKSPACE_ROOT", settings.REPO_ROOT))
        fallback_root = Path(__file__).resolve().parents[4]
        self.repo_root = (
            configured_root.resolve()
            if self._looks_like_repo_root(configured_root)
            else fallback_root.resolve()
        )
        inbox_default = self.repo_root / ".kortana" / "operator_inbox.md"
        self.inbox_path = Path(
            os.getenv("KORTANA_OPERATOR_INBOX", str(inbox_default))
        ).resolve()
        self._last_inbox_digest: str | None = None
        self._last_snapshot: WorkspaceSnapshot | None = None
        self._ensure_inbox_exists()

    async def poll(self) -> dict[str, Any]:
        """Poll local git state and ingest any new operator inbox entries."""
        branch = self._git_output(["git", "branch", "--show-current"]) or "unknown"
        status_lines = self._git_status_lines()
        ingested = await self._ingest_inbox()

        snapshot = WorkspaceSnapshot(
            repo_root=str(self.repo_root),
            branch=branch,
            dirty=bool(status_lines),
            changed_files=self._extract_changed_files(status_lines),
            changed_count=len(status_lines),
            inbox_path=str(self.inbox_path),
            inbox_exists=self.inbox_path.exists(),
            ingested_count=ingested,
            last_scan=datetime.utcnow().isoformat(),
            last_inbox_digest=self._last_inbox_digest,
        )
        self._last_snapshot = snapshot
        return self.get_status()

    def get_status(self) -> dict[str, Any]:
        if self._last_snapshot is None:
            return {
                "repo_root": str(self.repo_root),
                "branch": "unknown",
                "dirty": False,
                "changed_files": [],
                "changed_count": 0,
                "inbox_path": str(self.inbox_path),
                "inbox_exists": self.inbox_path.exists(),
                "ingested_count": 0,
                "last_scan": None,
                "last_inbox_digest": self._last_inbox_digest,
            }
        return {
            "repo_root": self._last_snapshot.repo_root,
            "branch": self._last_snapshot.branch,
            "dirty": self._last_snapshot.dirty,
            "changed_files": self._last_snapshot.changed_files,
            "changed_count": self._last_snapshot.changed_count,
            "inbox_path": self._last_snapshot.inbox_path,
            "inbox_exists": self._last_snapshot.inbox_exists,
            "ingested_count": self._last_snapshot.ingested_count,
            "last_scan": self._last_snapshot.last_scan,
            "last_inbox_digest": self._last_snapshot.last_inbox_digest,
        }

    def prompt_context(self) -> str:
        if self._last_snapshot is None:
            return ""
        if not self._last_snapshot.changed_files:
            return ""
        files = ", ".join(self._last_snapshot.changed_files[:8])
        return f"Recent local workspace changes were detected in: {files}."

    async def _ingest_inbox(self) -> int:
        if not self.inbox_path.exists():
            return 0

        try:
            content = self.inbox_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning(f"Failed to read operator inbox: {exc}")
            return 0

        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if digest == self._last_inbox_digest:
            return 0

        ingested = 0
        service = OperatorDirectiveService()
        for raw_line in content.splitlines():
            entry = raw_line.strip()
            if not entry or entry.startswith("#"):
                continue
            entry = self._normalize_entry(entry)
            directive_type = self._directive_type_from_entry(entry)
            directive = await service.create_directive(
                content=entry,
                directive_type=directive_type,
                priority=85,
                source="workspace_inbox",
            )
            if directive is not None:
                ingested += 1

        self._last_inbox_digest = digest
        return ingested

    def _git_status_lines(self) -> list[str]:
        output = self._git_output(["git", "status", "--porcelain"])
        if not output:
            return []
        return [line for line in output.splitlines() if line.strip()]

    def _git_output(self, command: list[str]) -> str:
        try:
            result = subprocess.run(
                self._git_command(command),
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except Exception as exc:
            logger.debug(f"Workspace bridge command failed ({command}): {exc}")
            return ""

    def _git_command(self, command: list[str]) -> list[str]:
        if not command or command[0] != "git":
            return command
        return [
            "git",
            "-c",
            f"safe.directory={self.repo_root}",
            *command[1:],
        ]

    @staticmethod
    def _extract_changed_files(status_lines: list[str]) -> list[str]:
        changed: list[str] = []
        for line in status_lines:
            if len(line) < 4:
                continue
            path = line[3:].strip()
            if "->" in path:
                path = path.split("->", 1)[1].strip()
            if path and path not in changed:
                changed.append(path)
        return changed[:20]

    @staticmethod
    def _normalize_entry(entry: str) -> str:
        normalized = entry.lstrip("-*>\t ").strip()
        if ":" in normalized:
            prefix, rest = normalized.split(":", 1)
            if prefix.lower() in {"focus", "avoid", "pause", "resume", "limit"}:
                return f"{prefix.lower()}: {rest.strip()}"
        return normalized

    @staticmethod
    def _directive_type_from_entry(entry: str) -> str | None:
        lowered = entry.lower()
        if lowered.startswith("focus:"):
            return "focus"
        if lowered.startswith("avoid:"):
            return "avoid"
        if lowered.startswith("pause"):
            return "pause"
        if lowered.startswith("resume"):
            return "resume"
        if lowered.startswith("limit:") or lowered.startswith("max tasks"):
            return "limit"
        return None

    @staticmethod
    def _looks_like_repo_root(candidate: Path) -> bool:
        if not candidate.exists():
            return False

        markers = [
            ".git",
            "backend",
            "frontend",
            "app",
            "src",
            "package.json",
            "pyproject.toml",
            "README.md",
        ]
        return any((candidate / marker).exists() for marker in markers)

    def _ensure_inbox_exists(self) -> None:
        try:
            self.inbox_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.inbox_path.exists():
                self.inbox_path.write_text(
                    (
                        "# Kor'tana Operator Inbox\n"
                        "# Add one steering note per line. Examples:\n"
                        "# focus: backend reliability and tests\n"
                        "# avoid: billing\n"
                        "# pause\n"
                        "# max tasks 1\n"
                    ),
                    encoding="utf-8",
                )
        except Exception as exc:
            logger.warning(f"Failed to initialize operator inbox: {exc}")


_bridge: WorkspaceBridgeService | None = None


def get_workspace_bridge() -> WorkspaceBridgeService:
    global _bridge
    if _bridge is None:
        _bridge = WorkspaceBridgeService()
    return _bridge
