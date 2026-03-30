"""
Repository boundary service.

Resolves the canonical Kor'tana repo root, optionally resolves a nested
reference repo root, and provides read-only search/read helpers for the
reference repo. Write-capable services must only target the canonical root.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.kortana.config import get_settings
from src.kortana.logger import get_logger

logger = get_logger(__name__)

_SCAN_SKIP_DIRS = {
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


@dataclass
class ReferenceSearchResult:
    path: str
    line_number: int
    snippet: str


class RepositoryBoundaryService:
    """Resolve and enforce canonical vs. reference repository boundaries."""

    def __init__(
        self,
        *,
        canonical_root: str | Path | None = None,
        reference_root: str | Path | None | object = Ellipsis,
    ) -> None:
        settings = get_settings()
        fallback_root = Path(__file__).resolve().parents[4]
        raw_canonical = (
            canonical_root
            if canonical_root is not None
            else os.getenv("KORTANA_WORKSPACE_ROOT") or settings.REPO_ROOT
        )
        self.fallback_root = fallback_root.resolve()
        self.configured_canonical_root = self._resolve_path(
            raw_canonical, base=self.fallback_root
        )
        self.canonical_repo_root = (
            self.configured_canonical_root
            if self._looks_like_repo_root(self.configured_canonical_root)
            else self.fallback_root
        )
        self.canonical_root_source = (
            "configured"
            if self._looks_like_repo_root(self.configured_canonical_root)
            else "fallback"
        )

        raw_reference = (
            settings.REFERENCE_REPO_ROOT
            if reference_root is Ellipsis
            else reference_root
        )
        self.configured_reference_root = self._resolve_reference_root(raw_reference)
        self.reference_repo_root = (
            self.configured_reference_root
            if self.configured_reference_root is not None
            and self._looks_like_repo_root(self.configured_reference_root)
            and self.configured_reference_root != self.canonical_repo_root
            else None
        )

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

    @staticmethod
    def _git_output(command: list[str], cwd: Path) -> str:
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True,
            )
        except Exception:
            return ""
        return result.stdout.strip()

    @staticmethod
    def _resolve_path(raw_path: str | Path | None, *, base: Path) -> Path:
        if raw_path is None:
            return base

        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = base / candidate
        return candidate.resolve()

    def _resolve_reference_root(
        self, raw_path: str | Path | None | object
    ) -> Path | None:
        if raw_path in {None, ""}:
            return None
        return self._resolve_path(raw_path, base=self.canonical_repo_root)

    def resolve_canonical_path(self, path: str | Path) -> Path:
        """Resolve a path and ensure it remains inside the canonical repo only."""
        candidate = self._resolve_path(path, base=self.canonical_repo_root)
        try:
            candidate.relative_to(self.canonical_repo_root)
        except ValueError as exc:
            raise ValueError(
                f"Path {candidate} escapes canonical repo root {self.canonical_repo_root}"
            ) from exc

        if self.reference_repo_root is not None:
            try:
                candidate.relative_to(self.reference_repo_root)
            except ValueError:
                pass
            else:
                raise ValueError(
                    f"Path {candidate} falls inside reference repo {self.reference_repo_root}"
                )

        return candidate

    def resolve_reference_path(self, relative_path: str | Path) -> Path:
        """Resolve a read-only path inside the configured reference repo."""
        if self.reference_repo_root is None:
            raise ValueError("Reference repo is not configured or does not exist.")

        candidate = self._resolve_path(relative_path, base=self.reference_repo_root)
        try:
            candidate.relative_to(self.reference_repo_root)
        except ValueError as exc:
            raise ValueError(
                f"Path {candidate} escapes reference repo root {self.reference_repo_root}"
            ) from exc
        return candidate

    def reference_status(self) -> dict[str, Any]:
        """Return status for the optional read-only reference repo."""
        if self.reference_repo_root is None:
            return {
                "configured_reference_root": (
                    str(self.configured_reference_root)
                    if self.configured_reference_root is not None
                    else None
                ),
                "reference_repo_root": None,
                "available": False,
                "branch": None,
                "dirty": None,
            }

        return {
            "configured_reference_root": str(self.configured_reference_root),
            "reference_repo_root": str(self.reference_repo_root),
            "available": True,
            "branch": self._git_output(
                ["git", "branch", "--show-current"], self.reference_repo_root
            )
            or "unknown",
            "dirty": bool(
                self._git_output(
                    ["git", "status", "--porcelain"], self.reference_repo_root
                )
            ),
        }

    def read_reference_file(
        self, relative_path: str | Path, *, max_chars: int = 12000
    ) -> str:
        """Read a bounded amount of text from the reference repo."""
        candidate = self.resolve_reference_path(relative_path)
        if not candidate.exists() or not candidate.is_file():
            raise FileNotFoundError(candidate)

        return candidate.read_text(encoding="utf-8")[:max_chars]

    def search_reference_repo(
        self, query: str, *, limit: int = 20
    ) -> list[ReferenceSearchResult]:
        """Read-only text search across the reference repo."""
        if self.reference_repo_root is None or not query.strip():
            return []

        needle = query.lower()
        results: list[ReferenceSearchResult] = []

        for root, dirs, files in os.walk(self.reference_repo_root):
            dirs[:] = [item for item in dirs if item not in _SCAN_SKIP_DIRS]
            for filename in files:
                candidate = Path(root) / filename
                try:
                    rel_path = candidate.relative_to(
                        self.reference_repo_root
                    ).as_posix()
                except ValueError:
                    continue

                try:
                    content = candidate.read_text(encoding="utf-8")
                except Exception:
                    continue

                for line_number, line in enumerate(content.splitlines(), 1):
                    if needle in line.lower():
                        results.append(
                            ReferenceSearchResult(
                                path=rel_path,
                                line_number=line_number,
                                snippet=line.strip()[:240],
                            )
                        )
                        if len(results) >= limit:
                            return results

        return results
