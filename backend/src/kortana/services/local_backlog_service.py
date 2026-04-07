"""Local-first task synthesis for autonomous runtime."""

from __future__ import annotations

import hashlib
import inspect
import os
import re
from typing import Any

from sqlalchemy import select

from src.kortana.config import get_settings
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask
from src.kortana.services.operator_directive_service import DirectiveSummary

logger = get_logger(__name__)

LOCAL_WORKSPACE_REPO = "local/workspace"
LOCAL_SELF_HEAL_REPO = "local/self-heal"


class LocalBacklogService:
    """Synthesise durable local tasks when GitHub is not the control plane."""

    def __init__(self, db_session: Any) -> None:
        self.db = db_session
        self.settings = get_settings()

    async def discover_workspace_tasks(
        self,
        *,
        workspace_status: dict[str, Any] | None = None,
        guidance: DirectiveSummary | None = None,
    ) -> list[GitHubTask]:
        if not self._local_backlog_enabled():
            return []

        snapshot = workspace_status or {}
        guidance = guidance or DirectiveSummary()

        if not self._has_workspace_signal(snapshot, guidance):
            return []

        active_task = await self._find_active_local_task(LOCAL_WORKSPACE_REPO)
        if active_task is not None:
            return []

        anchor = self._workspace_anchor(snapshot, guidance)
        existing = await self._find_existing_local_task(anchor, LOCAL_WORKSPACE_REPO)
        if existing is not None:
            return []

        # Load identity for voice-line header
        voice_line = ""
        try:
            from src.kortana.services.prompt_assembly import PromptAssemblyService

            profile = await PromptAssemblyService.load_profile(self.db)
            voice_line = f"{profile.name} | {profile.mission}"
        except Exception:
            pass

        issue_number = await self._next_local_issue_number()
        title = self._workspace_title(snapshot, guidance)
        branch_name = self._branch_name(issue_number, title, prefix="auto/local")
        description = self._workspace_description(
            anchor, snapshot, guidance, voice_line=voice_line
        )
        priority = self._workspace_priority(snapshot, guidance)

        task = GitHubTask(
            github_issue_number=issue_number,
            github_repo=LOCAL_WORKSPACE_REPO,
            title=title,
            description=description,
            status="pending",
            classification="local",
            priority=priority,
            branch_name=branch_name,
        )
        self.db.add(task)
        await self._db_commit()
        logger.info("Synthesized local workspace task %s", title)
        return [task]

    async def manifest_self_repair(
        self,
        *,
        failed_task: GitHubTask,
        repair_anchor: str,
    ) -> GitHubTask | None:
        title = f"[AUTO] [SELF-REPAIR] Resolve systemic failure in {failed_task.title}"
        active = await self._find_by_title_or_anchor(
            title=title,
            anchor=repair_anchor,
            repo=LOCAL_SELF_HEAL_REPO,
            include_completed=True,
        )
        if active is not None:
            return None

        # Load identity for voice-line header
        voice_line = ""
        try:
            from src.kortana.services.prompt_assembly import PromptAssemblyService

            profile = await PromptAssemblyService.load_profile(self.db)
            voice_line = f"{profile.name} | {profile.mission}"
        except Exception:
            pass

        issue_number = await self._next_local_issue_number()
        branch_name = self._branch_name(issue_number, title, prefix="auto/self-repair")
        protocol_header = f"**{voice_line}**" if voice_line else "**KOR'TANA**"
        description = (
            f"{protocol_header} — LOCAL SELF-REPAIR PROTOCOL ACTIVATED.\n\n"
            "GitHub publication is deferred or unavailable, so this repair task is "
            "being manifested directly into the local backlog.\n\n"
            f"{repair_anchor}\n\n"
            f"Origin task: {failed_task.github_repo}#{failed_task.github_issue_number}\n"
            f"Origin status: {failed_task.status}\n\n"
            f"### Error Diagnostic\n```\n{failed_task.error_message or 'Unknown failure'}\n```\n"
        )
        task = GitHubTask(
            github_issue_number=issue_number,
            github_repo=LOCAL_SELF_HEAL_REPO,
            title=title,
            description=description,
            status="pending",
            classification="self_repair",
            priority="high",
            branch_name=branch_name,
        )
        self.db.add(task)
        await self._db_commit()
        logger.info("Manifested local self-repair task for %s", failed_task.id)
        return task

    async def _find_existing_local_task(
        self,
        anchor: str,
        repo: str,
    ) -> GitHubTask | None:
        # include_completed=True so that executed/blocked/failed tasks block re-seeding
        # of the same anchor, preventing infinite loops on the same workspace state.
        return await self._find_by_title_or_anchor(
            title=None,
            anchor=anchor,
            repo=repo,
            include_completed=True,
        )

    async def _find_active_local_task(self, repo: str) -> GitHubTask | None:
        stmt = (
            select(GitHubTask)
            .where(
                GitHubTask.github_repo == repo,
                GitHubTask.status.in_(
                    [
                        "pending",
                        "queued",
                        "analyzed",
                        "planning",
                        "planning_complete",
                        "waiting_for_approval",
                        "executing",
                    ]
                ),
            )
            .limit(1)
        )
        result = await self._db_execute(stmt)
        return result.scalar_one_or_none()

    async def _find_by_title_or_anchor(
        self,
        *,
        title: str | None,
        anchor: str,
        repo: str,
        include_completed: bool,
    ) -> GitHubTask | None:
        stmt = select(GitHubTask).where(
            GitHubTask.github_repo == repo,
            GitHubTask.description.contains(anchor),
        )
        if title is not None:
            stmt = stmt.where(GitHubTask.title == title)
        if not include_completed:
            stmt = stmt.where(
                GitHubTask.status.in_(
                    [
                        "pending",
                        "queued",
                        "analyzed",
                        "planning",
                        "planning_complete",
                        "waiting_for_approval",
                        "executing",
                    ]
                )
            )
        result = await self._db_execute(stmt.limit(1))
        return result.scalar_one_or_none()

    async def _next_local_issue_number(self) -> int:
        stmt = (
            select(GitHubTask.github_issue_number)
            .where(GitHubTask.github_repo.like("local/%"))
            .order_by(GitHubTask.github_issue_number.asc())
            .limit(1)
        )
        result = await self._db_execute(stmt)
        lowest = result.scalar_one_or_none()
        if lowest is None or lowest >= 0:
            return -1
        return int(lowest) - 1

    @staticmethod
    def _has_workspace_signal(
        snapshot: dict[str, Any],
        guidance: DirectiveSummary,
    ) -> bool:
        if snapshot.get("dirty") or snapshot.get("changed_files"):
            return True
        if guidance.focus_topics or guidance.notes:
            return True
        return False

    @staticmethod
    def _workspace_anchor(
        snapshot: dict[str, Any],
        guidance: DirectiveSummary,
    ) -> str:
        payload = "|".join(
            [
                str(snapshot.get("branch") or ""),
                str(snapshot.get("changed_count") or 0),
                ",".join(snapshot.get("changed_files") or []),
                ",".join(guidance.focus_topics),
                ",".join(guidance.notes),
            ]
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
        return f"[LOCAL-TASK-ANCHOR] workspace:{digest}"

    @staticmethod
    def _workspace_title(
        snapshot: dict[str, Any],
        guidance: DirectiveSummary,
    ) -> str:
        if guidance.focus_topics and snapshot.get("dirty"):
            focus = ", ".join(guidance.focus_topics[:2])
            return f"Advance local focus and reconcile workspace drift: {focus}"
        if guidance.focus_topics:
            return "Advance local autonomy focus: " + ", ".join(
                guidance.focus_topics[:2]
            )
        changed_files = snapshot.get("changed_files") or []
        if changed_files:
            return "Reconcile local workspace changes"
        return "Advance local autonomy backlog"

    @staticmethod
    def _workspace_description(
        anchor: str,
        snapshot: dict[str, Any],
        guidance: DirectiveSummary,
        voice_line: str = "",
    ) -> str:
        changed_files = snapshot.get("changed_files") or []
        changed_block = (
            "\n".join(f"- {path}" for path in changed_files[:12])
            if changed_files
            else "- (no explicit file list captured)"
        )
        focus = ", ".join(guidance.focus_topics[:4]) or "(none)"
        avoid = ", ".join(guidance.avoid_topics[:4]) or "(none)"
        notes = " | ".join(guidance.notes[:3]) or "(none)"
        header = (
            f"**{voice_line}** — Local-first autonomy task."
            if voice_line
            else "**Local-first autonomy task.**"
        )
        return (
            f"{header}\n\n"
            "GitHub has been demoted from the control plane. Treat this repository "
            "state and operator guidance as the source of truth.\n\n"
            f"{anchor}\n\n"
            f"Current branch: {snapshot.get('branch') or 'unknown'}\n"
            f"Dirty workspace: {bool(snapshot.get('dirty'))}\n"
            f"Changed file count: {int(snapshot.get('changed_count') or 0)}\n"
            f"Focus topics: {focus}\n"
            f"Avoid topics: {avoid}\n"
            f"Operator notes: {notes}\n\n"
            "Observed changed files:\n"
            f"{changed_block}\n"
        )

    @staticmethod
    def _workspace_priority(
        snapshot: dict[str, Any],
        guidance: DirectiveSummary,
    ) -> str:
        changed_count = int(snapshot.get("changed_count") or 0)
        if guidance.focus_topics or changed_count >= 20:
            return "high"
        if changed_count >= 5:
            return "medium"
        return "low"

    @staticmethod
    def _branch_name(issue_number: int, title: str, prefix: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        slug = slug[:48] or "autonomy-task"
        return f"{prefix}/{abs(issue_number)}-{slug}"

    async def queue_autonomous_investigation(
        self,
        *,
        title: str,
        description: str,
        classification: str = "self_directed",
        priority: str = "medium",
    ) -> GitHubTask | None:
        """Queue a self-directed investigation task into the local backlog.

        Deduplicates by title — returns None if an identical title already exists
        (any status, including completed, to avoid re-running finished work).
        """
        existing = await self._db_execute(
            select(GitHubTask).where(
                GitHubTask.title == title,
                GitHubTask.github_repo == LOCAL_SELF_HEAL_REPO,
                GitHubTask.status.notin_(["failed", "cancelled", "blocked"]),
            )
        )
        if existing.scalar_one_or_none() is not None:
            logger.debug("Autonomous task already exists: %s", title)
            return None

        issue_number = await self._next_local_issue_number()
        branch_name = self._branch_name(issue_number, title, prefix="auto/investigate")
        task = GitHubTask(
            github_issue_number=issue_number,
            github_repo=LOCAL_SELF_HEAL_REPO,
            title=title,
            description=description,
            status="pending",
            classification=classification,
            priority=priority,
            branch_name=branch_name,
        )
        self.db.add(task)
        await self._db_commit()
        logger.info("Queued autonomous investigation: %s", title)
        return task

    def _local_backlog_enabled(self) -> bool:
        raw = os.getenv("KORTANA_LOCAL_BACKLOG_ENABLED")
        if raw is not None:
            return raw.strip().lower() == "true"
        return bool(self.settings.KORTANA_LOCAL_BACKLOG_ENABLED)

    async def _db_execute(self, stmt: Any) -> Any:
        return await self._maybe_await(self.db.execute(stmt))

    async def _db_commit(self) -> None:
        await self._maybe_await(self.db.commit())

    @staticmethod
    async def _maybe_await(value: Any) -> Any:
        if inspect.isawaitable(value):
            return await value
        return value
