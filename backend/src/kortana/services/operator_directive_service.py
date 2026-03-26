"""
Operator directive service.

Stores lightweight operator comments/instructions and turns them into runtime
guidance for the always-on daemon and coding prompts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger
from src.kortana.models import OperatorDirective

logger = get_logger(__name__)


@dataclass
class DirectiveSummary:
    active_count: int = 0
    pause_requested: bool = False
    focus_topics: list[str] = field(default_factory=list)
    avoid_topics: list[str] = field(default_factory=list)
    max_tasks_override: int | None = None
    notes: list[str] = field(default_factory=list)
    directives: list[dict[str, Any]] = field(default_factory=list)
    prompt_preamble: str = ""


class OperatorDirectiveService:
    """Persists operator steering comments and summarizes active intent."""

    def __init__(self, db_session: AsyncSession | None = None) -> None:
        self.db = db_session
        self._db_manager = get_db_manager()

    async def create_directive(
        self,
        *,
        content: str,
        directive_type: str | None = None,
        source: str = "user",
        priority: int = 50,
        scope: str = "global",
    ) -> OperatorDirective:
        parsed = self.parse_content(content, directive_type=directive_type)
        inferred_type = directive_type or self._infer_type(parsed)

        async def _create(session: AsyncSession) -> OperatorDirective:
            existing = await self._find_existing_active(session, content, inferred_type)
            if existing is not None:
                return existing
            await self._retire_conflicts(session, parsed)
            directive = OperatorDirective(
                source=source,
                directive_type=inferred_type,
                priority=priority,
                content=content,
                scope=scope,
                directive_data=parsed,
            )
            session.add(directive)
            await session.flush()
            return directive

        directive = await self._with_session(_create)
        logger.info(
            "Operator directive recorded: "
            f"type={directive.directive_type} priority={directive.priority}"
        )
        return directive

    async def list_directives(
        self, *, status: str | None = "active", limit: int = 20
    ) -> list[OperatorDirective]:
        async def _list(session: AsyncSession) -> list[OperatorDirective]:
            stmt = select(OperatorDirective).order_by(
                OperatorDirective.created_at.desc()
            )
            if status:
                stmt = stmt.where(OperatorDirective.status == status)
            stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

        return await self._with_session(_list)

    async def resolve_directive(self, directive_id: str) -> OperatorDirective | None:
        async def _resolve(session: AsyncSession) -> OperatorDirective | None:
            stmt = select(OperatorDirective).where(OperatorDirective.id == directive_id)
            result = await session.execute(stmt)
            directive = result.scalar_one_or_none()
            if directive is None:
                return None
            directive.status = "resolved"
            directive.resolved_at = datetime.utcnow()
            return directive

        return await self._with_session(_resolve)

    async def get_active_summary(self) -> DirectiveSummary:
        directives = await self.list_directives(status="active", limit=50)
        summary = DirectiveSummary(active_count=len(directives))

        latest_limit_created_at = None
        for directive in reversed(directives):
            payload = directive.directive_data or {}
            if payload.get("pause_requested"):
                summary.pause_requested = True

            for topic in payload.get("focus_topics", []):
                if topic not in summary.focus_topics:
                    summary.focus_topics.append(topic)

            for topic in payload.get("avoid_topics", []):
                if topic not in summary.avoid_topics:
                    summary.avoid_topics.append(topic)

            max_tasks = payload.get("max_tasks_override")
            if max_tasks is not None and (
                latest_limit_created_at is None
                or (
                    directive.created_at is not None
                    and directive.created_at >= latest_limit_created_at
                )
            ):
                summary.max_tasks_override = int(max_tasks)
                latest_limit_created_at = directive.created_at

            if directive.directive_type == "comment" or payload.get("notes"):
                summary.notes.append(directive.content)

            summary.directives.append(self.serialize(directive))

        summary.prompt_preamble = self.build_prompt_preamble(summary)
        return summary

    @staticmethod
    def parse_content(content: str, directive_type: str | None = None) -> dict[str, Any]:
        text = content.strip()
        lowered = text.lower()
        parsed: dict[str, Any] = {
            "raw": text,
            "directive_type": directive_type,
            "pause_requested": False,
            "resume_requested": False,
            "focus_topics": [],
            "avoid_topics": [],
            "max_tasks_override": None,
            "notes": [],
        }

        if directive_type == "pause" or re.search(r"\b(pause|hold|stand by|stop)\b", lowered):
            parsed["pause_requested"] = True

        if directive_type == "resume" or re.search(r"\b(resume|continue|unpause)\b", lowered):
            parsed["resume_requested"] = True

        focus_match = re.search(
            r"(?:focus on|prioritize|prioritise|work on|target)\s+(.+?)(?=\b(?:avoid|ignore|deprioritize|deprioritise|stop working on|max tasks|max concurrency|limit concurrency|pause|resume|continue|unpause)\b|$)",
            lowered,
        )
        if directive_type == "focus" and not focus_match:
            focus_match = re.search(r"(.+)", lowered)
        if focus_match:
            parsed["focus_topics"] = OperatorDirectiveService._split_topics(
                focus_match.group(1)
            )

        avoid_match = re.search(
            r"(?:avoid|ignore|deprioritize|deprioritise|stop working on)\s+(.+?)(?=\b(?:focus on|prioritize|prioritise|work on|target|max tasks|max concurrency|limit concurrency|pause|resume|continue|unpause)\b|$)",
            lowered,
        )
        if directive_type == "avoid" and not avoid_match:
            avoid_match = re.search(r"(.+)", lowered)
        if avoid_match:
            parsed["avoid_topics"] = OperatorDirectiveService._split_topics(
                avoid_match.group(1)
            )

        max_tasks_match = re.search(
            r"(?:max tasks|max concurrency|limit concurrency)\s*(?:to)?\s*(\d+)",
            lowered,
        )
        if directive_type == "limit" and max_tasks_match is None:
            max_tasks_match = re.search(r"(\d+)", lowered)
        if max_tasks_match:
            parsed["max_tasks_override"] = max(1, int(max_tasks_match.group(1)))

        if not any(
            [
                parsed["pause_requested"],
                parsed["resume_requested"],
                parsed["focus_topics"],
                parsed["avoid_topics"],
                parsed["max_tasks_override"] is not None,
            ]
        ):
            parsed["notes"] = [text]

        return parsed

    @staticmethod
    def build_prompt_preamble(summary: DirectiveSummary) -> str:
        if summary.active_count == 0:
            return ""

        lines = [
            "Operator guidance is active. Treat it as higher priority than generic autonomy heuristics."
        ]
        if summary.pause_requested:
            lines.append("Pause direct execution unless the runtime explicitly allows observation-only work.")
        if summary.focus_topics:
            lines.append("Focus on: " + ", ".join(summary.focus_topics) + ".")
        if summary.avoid_topics:
            lines.append("Avoid or de-prioritize: " + ", ".join(summary.avoid_topics) + ".")
        if summary.notes:
            lines.append("Recent operator notes: " + " | ".join(summary.notes[:3]))
        return "\n".join(lines)

    @staticmethod
    def serialize(directive: OperatorDirective) -> dict[str, Any]:
        return {
            "id": directive.id,
            "source": directive.source,
            "directive_type": directive.directive_type,
            "status": directive.status,
            "priority": directive.priority,
            "content": directive.content,
            "scope": directive.scope,
            "directive_data": directive.directive_data or {},
            "created_at": directive.created_at.isoformat() if directive.created_at else None,
            "updated_at": directive.updated_at.isoformat() if directive.updated_at else None,
            "resolved_at": directive.resolved_at.isoformat() if directive.resolved_at else None,
        }

    async def _retire_conflicts(
        self, session: AsyncSession, parsed: dict[str, Any]
    ) -> None:
        stmt = select(OperatorDirective).where(OperatorDirective.status == "active")
        result = await session.execute(stmt)
        directives = list(result.scalars().all())

        for directive in directives:
            if parsed.get("resume_requested") and directive.directive_type == "pause":
                directive.status = "resolved"
                directive.resolved_at = datetime.utcnow()
            if (
                parsed.get("max_tasks_override") is not None
                and directive.directive_type == "limit"
            ):
                directive.status = "resolved"
                directive.resolved_at = datetime.utcnow()

    async def _find_existing_active(
        self, session: AsyncSession, content: str, directive_type: str
    ) -> OperatorDirective | None:
        stmt = select(OperatorDirective).where(
            OperatorDirective.status == "active",
            OperatorDirective.content == content,
            OperatorDirective.directive_type == directive_type,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _infer_type(parsed: dict[str, Any]) -> str:
        if parsed.get("resume_requested"):
            return "resume"
        if parsed.get("pause_requested"):
            return "pause"
        if parsed.get("max_tasks_override") is not None:
            return "limit"
        if parsed.get("focus_topics"):
            return "focus"
        if parsed.get("avoid_topics"):
            return "avoid"
        return "comment"

    @staticmethod
    def _split_topics(raw: str) -> list[str]:
        normalized = re.split(r",| and | then ", raw)
        topics = []
        for item in normalized:
            cleaned = item.strip(" .")
            if cleaned and cleaned not in topics:
                topics.append(cleaned)
        return topics[:5]

    async def _with_session(self, callback):
        if self.db is not None:
            result = await callback(self.db)
            await self.db.commit()
            return result

        async with self._db_manager.session_scope() as session:
            return await callback(session)


async def get_active_operator_summary(
    db_session: AsyncSession | None = None,
) -> DirectiveSummary:
    service = OperatorDirectiveService(db_session)
    return await service.get_active_summary()
