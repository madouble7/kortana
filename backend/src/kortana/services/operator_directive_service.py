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
    protocol_version: str = "v1"
    active_count: int = 0
    pause_requested: bool = False
    focus_topics: list[str] = field(default_factory=list)
    avoid_topics: list[str] = field(default_factory=list)
    max_tasks_override: int | None = None
    execution_mode: str | None = None
    approval_mode: str | None = None
    approval_required: bool = False
    handoff_rules: list[str] = field(default_factory=list)
    override_mode: str | None = None
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
        ordered_directives = sorted(
            directives,
            key=lambda directive: directive.created_at or datetime.min,
        )

        latest_limit_created_at = None
        latest_mode_created_at = None
        latest_approval_created_at = None
        latest_override_created_at = None
        for directive in ordered_directives:
            payload = directive.directive_data or {}
            override_mode = payload.get("override_mode")
            if override_mode == "clear":
                summary.pause_requested = False
                summary.focus_topics = []
                summary.avoid_topics = []
                summary.max_tasks_override = None
                summary.execution_mode = None
                summary.approval_mode = None
                summary.approval_required = False
                summary.handoff_rules = []
                summary.notes = []
                summary.override_mode = "clear"

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

            execution_mode = payload.get("execution_mode")
            if execution_mode and (
                latest_mode_created_at is None
                or (
                    directive.created_at is not None
                    and directive.created_at >= latest_mode_created_at
                )
            ):
                summary.execution_mode = str(execution_mode)
                latest_mode_created_at = directive.created_at

            approval_mode = payload.get("approval_mode")
            if approval_mode and (
                latest_approval_created_at is None
                or (
                    directive.created_at is not None
                    and directive.created_at >= latest_approval_created_at
                )
            ):
                summary.approval_mode = str(approval_mode)
                summary.approval_required = str(approval_mode) == "manual"
                latest_approval_created_at = directive.created_at

            if override_mode and (
                latest_override_created_at is None
                or (
                    directive.created_at is not None
                    and directive.created_at >= latest_override_created_at
                )
            ):
                summary.override_mode = str(override_mode)
                latest_override_created_at = directive.created_at

            for handoff_rule in payload.get("handoff_rules", []):
                if handoff_rule not in summary.handoff_rules:
                    summary.handoff_rules.append(str(handoff_rule))

            if directive.directive_type == "comment" or payload.get("notes"):
                summary.notes.append(directive.content)

            summary.directives.append(self.serialize(directive))

        summary.prompt_preamble = self.build_prompt_preamble(summary)
        return summary

    @staticmethod
    def parse_content(
        content: str, directive_type: str | None = None
    ) -> dict[str, Any]:
        text = content.strip()
        lowered = text.lower()
        parsed: dict[str, Any] = {
            "protocol_version": "v1",
            "raw": text,
            "directive_type": directive_type,
            "pause_requested": False,
            "resume_requested": False,
            "focus_topics": [],
            "avoid_topics": [],
            "max_tasks_override": None,
            "execution_mode": None,
            "approval_mode": None,
            "approval_required": False,
            "handoff_rules": [],
            "override_mode": None,
            "notes": [],
        }

        if directive_type == "pause" or re.search(
            r"\b(pause|hold|stand by|stop)\b", lowered
        ):
            parsed["pause_requested"] = True

        if directive_type == "resume" or re.search(
            r"\b(resume|continue|unpause)\b", lowered
        ):
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

        if directive_type == "mode":
            mode_match = re.search(r"(observe|plan|execute)", lowered)
        else:
            mode_match = re.search(
                r"(?:mode\s*:?\s*|run in\s+)(observe|plan|execute)\b", lowered
            )
        if mode_match:
            parsed["execution_mode"] = mode_match.group(1)

        if directive_type == "approval":
            approval_match = re.search(
                r"(manual|auto|self-aware|self aware|autonomous)", lowered
            )
        else:
            approval_match = re.search(
                r"(?:approval\s*:?\s*|approval mode\s*:?\s*|require approval|manual approval|auto approval|self-aware approval|autonomous approval)(manual|auto|self-aware|self aware|autonomous)?",
                lowered,
            )
        if approval_match:
            inferred = approval_match.group(1)
            if inferred is None:
                if "manual" in lowered or "require approval" in lowered:
                    inferred = "manual"
                elif (
                    "self-aware" in lowered
                    or "self aware" in lowered
                    or "autonomous" in lowered
                ):
                    inferred = "self-aware"
                else:
                    inferred = "auto"
            if inferred in {"self aware", "autonomous"}:
                inferred = "self-aware"
            parsed["approval_mode"] = inferred
            parsed["approval_required"] = inferred == "manual"

        handoff_match = re.search(
            r"(?:handoff\s*:?\s*)(.+?)(?=(?:\s*[;|]\s*(?:focus|avoid|mode|approval|limit|override|note)\s*:)|$)",
            text,
            re.IGNORECASE,
        )
        if directive_type == "handoff" and not handoff_match:
            handoff_match = re.search(r"(.+)", text)
        if handoff_match:
            parsed["handoff_rules"] = OperatorDirectiveService._split_handoffs(
                handoff_match.group(1)
            )

        if directive_type == "override":
            override_match = re.search(r"(halt|execute|clear)", lowered)
        else:
            override_match = re.search(
                r"(?:override\s*:?\s*)(halt|execute|clear)\b", lowered
            )
        if override_match:
            parsed["override_mode"] = override_match.group(1)

        if not any(
            [
                parsed["pause_requested"],
                parsed["resume_requested"],
                parsed["focus_topics"],
                parsed["avoid_topics"],
                parsed["max_tasks_override"] is not None,
                parsed["execution_mode"] is not None,
                parsed["approval_mode"] is not None,
                bool(parsed["handoff_rules"]),
                parsed["override_mode"] is not None,
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
        lines.append(f"Directive protocol: {summary.protocol_version}.")
        if summary.override_mode:
            lines.append(f"Operator override is active: {summary.override_mode}.")
        if summary.pause_requested:
            lines.append(
                "Pause direct execution unless the runtime explicitly allows observation-only work."
            )
        if summary.execution_mode:
            lines.append(f"Execution mode: {summary.execution_mode}.")
        if summary.approval_mode:
            lines.append(f"Approval mode: {summary.approval_mode}.")
        if summary.max_tasks_override is not None:
            lines.append(f"Max tasks per cycle: {summary.max_tasks_override}.")
        if summary.focus_topics:
            lines.append("Focus on: " + ", ".join(summary.focus_topics) + ".")
        if summary.avoid_topics:
            lines.append(
                "Avoid or de-prioritize: " + ", ".join(summary.avoid_topics) + "."
            )
        if summary.handoff_rules:
            lines.append(
                "Agent handoff rules: " + " | ".join(summary.handoff_rules[:3])
            )
        if summary.notes:
            lines.append("Recent operator notes: " + " | ".join(summary.notes[:3]))
        return "\n".join(lines)

    @staticmethod
    def protocol_spec() -> dict[str, Any]:
        return {
            "version": "v1",
            "directives": {
                "focus": "FOCUS: backend reliability, tests",
                "avoid": "AVOID: billing, docs churn",
                "mode": "MODE: execute|plan|observe",
                "approval": "APPROVAL: auto|manual|self-aware",
                "limit": "LIMIT: max_tasks=2",
                "handoff": "HANDOFF: analyzer -> planner -> executor",
                "override": "OVERRIDE: halt|execute|clear",
                "note": "NOTE: keep changes surgical",
            },
            "examples": [
                "MODE: plan",
                "APPROVAL: manual",
                "APPROVAL: self-aware",
                "LIMIT: max_tasks=1",
                "HANDOFF: analyzer -> planner -> executor",
                "OVERRIDE: halt",
                "FOCUS: daemon reliability and tests",
            ],
        }

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
            "created_at": directive.created_at.isoformat()
            if directive.created_at
            else None,
            "updated_at": directive.updated_at.isoformat()
            if directive.updated_at
            else None,
            "resolved_at": directive.resolved_at.isoformat()
            if directive.resolved_at
            else None,
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
            if parsed.get("execution_mode") and directive.directive_type == "mode":
                directive.status = "resolved"
                directive.resolved_at = datetime.utcnow()
            if parsed.get("approval_mode") and directive.directive_type == "approval":
                directive.status = "resolved"
                directive.resolved_at = datetime.utcnow()
            if parsed.get("override_mode") and directive.directive_type == "override":
                directive.status = "resolved"
                directive.resolved_at = datetime.utcnow()
            if parsed.get("override_mode") == "clear" and directive.status == "active":
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
        if parsed.get("override_mode") is not None:
            return "override"
        if parsed.get("resume_requested"):
            return "resume"
        if parsed.get("pause_requested"):
            return "pause"
        if parsed.get("execution_mode") is not None:
            return "mode"
        if parsed.get("approval_mode") is not None:
            return "approval"
        if parsed.get("max_tasks_override") is not None:
            return "limit"
        if parsed.get("handoff_rules"):
            return "handoff"
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

    @staticmethod
    def _split_handoffs(raw: str) -> list[str]:
        rules: list[str] = []
        for item in re.split(r"\||;|\n", raw):
            cleaned = item.strip(" .")
            if cleaned and cleaned not in rules:
                rules.append(cleaned)
        return rules[:5]

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
