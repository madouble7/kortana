"""Tests for operator directives and always-on guidance synthesis."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from src.kortana.models import OperatorDirective
from src.kortana.services.operator_directive_service import (
    DirectiveSummary,
    OperatorDirectiveService,
)


def make_directive(
    *,
    directive_type: str,
    content: str,
    directive_data: dict,
    created_at: datetime,
) -> OperatorDirective:
    return OperatorDirective(
        id=f"id-{directive_type}-{int(created_at.timestamp())}",
        directive_type=directive_type,
        content=content,
        status="active",
        source="user",
        priority=50,
        scope="global",
        directive_data=directive_data,
        created_at=created_at,
    )


class TestOperatorDirectiveService:
    def test_parse_content_extracts_runtime_intent(self) -> None:
        parsed = OperatorDirectiveService.parse_content(
            "Pause execution, focus on flaky tests, avoid billing, max tasks 2"
        )

        assert parsed["pause_requested"] is True
        assert parsed["focus_topics"] == ["flaky tests"]
        assert parsed["avoid_topics"] == ["billing"]
        assert parsed["max_tasks_override"] == 2

    def test_parse_content_extracts_protocol_directives(self) -> None:
        parsed = OperatorDirectiveService.parse_content(
            "MODE: plan; APPROVAL: manual; HANDOFF: analyzer -> planner -> executor; OVERRIDE: halt"
        )

        assert parsed["execution_mode"] == "plan"
        assert parsed["approval_mode"] == "manual"
        assert parsed["approval_required"] is True
        assert parsed["handoff_rules"] == ["analyzer -> planner -> executor"]
        assert parsed["override_mode"] == "halt"

    def test_parse_content_supports_self_aware_approval(self) -> None:
        parsed = OperatorDirectiveService.parse_content("APPROVAL: self-aware")

        assert parsed["approval_mode"] == "self-aware"
        assert parsed["approval_required"] is False

    def test_build_prompt_preamble_renders_operator_guidance(self) -> None:
        summary = DirectiveSummary(
            active_count=2,
            execution_mode="plan",
            approval_mode="manual",
            approval_required=True,
            handoff_rules=["analyzer -> planner -> executor"],
            focus_topics=["tests", "daemon"],
            avoid_topics=["billing"],
            notes=["Keep changes small"],
        )

        preamble = OperatorDirectiveService.build_prompt_preamble(summary)

        assert "Operator guidance is active" in preamble
        assert "Execution mode: plan." in preamble
        assert "Approval mode: manual." in preamble
        assert "Focus on: tests, daemon." in preamble
        assert "Avoid or de-prioritize: billing." in preamble
        assert "Agent handoff rules: analyzer -> planner -> executor" in preamble
        assert "Keep changes small" in preamble

    def test_protocol_spec_exposes_supported_commands(self) -> None:
        spec = OperatorDirectiveService.protocol_spec()

        assert spec["version"] == "v1"
        assert "mode" in spec["directives"]
        assert "override" in spec["directives"]
        assert "self-aware" in spec["directives"]["approval"]

    @pytest.mark.asyncio
    async def test_active_summary_merges_directives(self) -> None:
        service = OperatorDirectiveService()
        now = datetime.utcnow()
        directives = [
            make_directive(
                directive_type="focus",
                content="focus on tests",
                directive_data={
                    "focus_topics": ["tests"],
                    "avoid_topics": [],
                    "pause_requested": False,
                    "max_tasks_override": None,
                    "notes": [],
                },
                created_at=now - timedelta(minutes=5),
            ),
            make_directive(
                directive_type="avoid",
                content="avoid billing",
                directive_data={
                    "focus_topics": [],
                    "avoid_topics": ["billing"],
                    "pause_requested": False,
                    "max_tasks_override": None,
                    "notes": [],
                },
                created_at=now - timedelta(minutes=4),
            ),
            make_directive(
                directive_type="limit",
                content="max tasks 2",
                directive_data={
                    "focus_topics": [],
                    "avoid_topics": [],
                    "pause_requested": False,
                    "max_tasks_override": 2,
                    "execution_mode": None,
                    "approval_mode": None,
                    "handoff_rules": [],
                    "override_mode": None,
                    "notes": [],
                },
                created_at=now - timedelta(minutes=3),
            ),
            make_directive(
                directive_type="mode",
                content="mode: plan",
                directive_data={
                    "focus_topics": [],
                    "avoid_topics": [],
                    "pause_requested": False,
                    "max_tasks_override": None,
                    "execution_mode": "plan",
                    "approval_mode": None,
                    "handoff_rules": [],
                    "override_mode": None,
                    "notes": [],
                },
                created_at=now - timedelta(minutes=2, seconds=30),
            ),
            make_directive(
                directive_type="approval",
                content="approval: manual",
                directive_data={
                    "focus_topics": [],
                    "avoid_topics": [],
                    "pause_requested": False,
                    "max_tasks_override": None,
                    "execution_mode": None,
                    "approval_mode": "manual",
                    "handoff_rules": [],
                    "override_mode": None,
                    "notes": [],
                },
                created_at=now - timedelta(minutes=2, seconds=15),
            ),
            make_directive(
                directive_type="handoff",
                content="handoff: analyzer -> planner -> executor",
                directive_data={
                    "focus_topics": [],
                    "avoid_topics": [],
                    "pause_requested": False,
                    "max_tasks_override": None,
                    "execution_mode": None,
                    "approval_mode": None,
                    "handoff_rules": ["analyzer -> planner -> executor"],
                    "override_mode": None,
                    "notes": [],
                },
                created_at=now - timedelta(minutes=2, seconds=5),
            ),
            make_directive(
                directive_type="comment",
                content="keep changes surgical",
                directive_data={
                    "focus_topics": [],
                    "avoid_topics": [],
                    "pause_requested": False,
                    "max_tasks_override": None,
                    "execution_mode": None,
                    "approval_mode": None,
                    "handoff_rules": [],
                    "override_mode": None,
                    "notes": ["keep changes surgical"],
                },
                created_at=now - timedelta(minutes=2),
            ),
        ]

        service.list_directives = AsyncMock(return_value=directives)
        summary = await service.get_active_summary()

        assert summary.active_count == 7
        assert summary.focus_topics == ["tests"]
        assert summary.avoid_topics == ["billing"]
        assert summary.max_tasks_override == 2
        assert summary.execution_mode == "plan"
        assert summary.approval_mode == "manual"
        assert summary.approval_required is True
        assert summary.handoff_rules == ["analyzer -> planner -> executor"]
        assert "keep changes surgical" in summary.prompt_preamble

    @pytest.mark.asyncio
    async def test_active_summary_clear_override_resets_prior_course(self) -> None:
        service = OperatorDirectiveService()
        now = datetime.utcnow()
        directives = [
            make_directive(
                directive_type="focus",
                content="focus on tests",
                directive_data={
                    "focus_topics": ["tests"],
                    "avoid_topics": [],
                    "pause_requested": False,
                    "max_tasks_override": None,
                    "execution_mode": None,
                    "approval_mode": None,
                    "handoff_rules": [],
                    "override_mode": None,
                    "notes": [],
                },
                created_at=now - timedelta(minutes=3),
            ),
            make_directive(
                directive_type="override",
                content="override: clear",
                directive_data={
                    "focus_topics": [],
                    "avoid_topics": [],
                    "pause_requested": False,
                    "max_tasks_override": None,
                    "execution_mode": None,
                    "approval_mode": None,
                    "handoff_rules": [],
                    "override_mode": "clear",
                    "notes": [],
                },
                created_at=now - timedelta(minutes=2),
            ),
            make_directive(
                directive_type="focus",
                content="focus on daemon",
                directive_data={
                    "focus_topics": ["daemon"],
                    "avoid_topics": [],
                    "pause_requested": False,
                    "max_tasks_override": None,
                    "execution_mode": None,
                    "approval_mode": None,
                    "handoff_rules": [],
                    "override_mode": None,
                    "notes": [],
                },
                created_at=now - timedelta(minutes=1),
            ),
        ]

        service.list_directives = AsyncMock(return_value=directives)
        summary = await service.get_active_summary()

        assert summary.focus_topics == ["daemon"]
        assert summary.override_mode == "clear"

    @pytest.mark.asyncio
    async def test_with_session_uses_session_scope_for_owned_sessions(self) -> None:
        service = OperatorDirectiveService()
        session = AsyncMock()
        lifecycle: list[str] = []

        class DummyManager:
            @asynccontextmanager
            async def session_scope(self):
                lifecycle.append("enter")
                yield session
                lifecycle.append("exit")

        service._db_manager = DummyManager()

        async def callback(current):
            return current

        result = await service._with_session(callback)

        assert result is session
        assert lifecycle == ["enter", "exit"]
