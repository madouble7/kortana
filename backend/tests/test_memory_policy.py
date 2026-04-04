"""Tests for prompt-facing memory retrieval doctrine."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.kortana.services.memory_policy import (
    MemoryPolicyContext,
    MemoryPolicyService,
    MemorySurface,
)


def _make_self_memory(cycle_number: int, summary: str) -> MagicMock:
    memory = MagicMock()
    memory.cycle_number = cycle_number
    memory.summary = summary
    return memory


def _make_conversation_message(role: str, content: str) -> MagicMock:
    message = MagicMock()
    message.role = role
    message.content = content
    return message


def _make_architecture_memory(
    component_name: str,
    description: str,
    *,
    knowledge_factors: object | None = None,
    confidence_score: float = 0.95,
) -> MagicMock:
    memory = MagicMock()
    memory.component_name = component_name
    memory.description = description
    memory.knowledge_factors = knowledge_factors
    memory.confidence_score = confidence_score
    return memory


def _make_incident(
    incident_type: str,
    description: str,
    *,
    incident_id: str = "incident-1",
    resolution_strategy: str | None = None,
    resolved: bool = False,
    fix_status: str | None = None,
) -> MagicMock:
    incident = MagicMock()
    incident.id = incident_id
    incident.incident_type = incident_type
    incident.description = description
    incident.resolution_strategy = resolution_strategy
    incident.resolved = resolved
    incident.fix_status = fix_status
    incident.stack_trace = None
    return incident


@pytest.mark.asyncio
async def test_reflection_surface_only_uses_self_memory() -> None:
    session = AsyncMock()

    with patch.object(
        MemoryPolicyService,
        "semantic_self_memory",
        AsyncMock(return_value=[_make_self_memory(7, "hold continuity")]),
    ) as mock_self_memory:
        with patch.object(
            MemoryPolicyService,
            "recent_conversation",
            AsyncMock(return_value=[_make_conversation_message("user", "hello")]),
        ) as mock_conversation:
            with patch.object(
                MemoryPolicyService,
                "unresolved_incidents",
                AsyncMock(return_value=[_make_incident("db", "unresolved")]),
            ) as mock_incidents:
                context = await MemoryPolicyService.build_context(
                    session,
                    surface=MemorySurface.REFLECTION,
                    query="continuity",
                    session_id="default",
                )

    assert context.self_memory_lines == ["- [cycle 7] hold continuity"]
    assert context.conversation_lines == []
    assert context.incident_lines == []
    mock_self_memory.assert_awaited_once()
    mock_conversation.assert_not_called()
    mock_incidents.assert_not_called()


@pytest.mark.asyncio
async def test_chat_surface_includes_self_memory_conversation_and_incidents() -> None:
    session = AsyncMock()

    with patch.object(
        MemoryPolicyService,
        "semantic_self_memory",
        AsyncMock(return_value=[_make_self_memory(12, "preserve coherent selfhood")]),
    ):
        with patch.object(
            MemoryPolicyService,
            "recent_conversation",
            AsyncMock(
                return_value=[
                    _make_conversation_message("user", "who are you"),
                    _make_conversation_message("assistant", "i am kor'tana"),
                ]
            ),
        ):
            with patch.object(
                MemoryPolicyService,
                "unresolved_incidents",
                AsyncMock(
                    return_value=[
                        _make_incident("scheduler", "pending queue drift detected")
                    ]
                ),
            ):
                context = await MemoryPolicyService.build_context(
                    session,
                    surface=MemorySurface.CHAT,
                    query="identity",
                    session_id="default",
                )

    rendered = context.render()
    assert "## continuity of self" in rendered
    assert "## recent conversation continuity" in rendered
    assert "## unresolved incident memory" in rendered
    assert "preserve coherent selfhood" in rendered
    assert "user: who are you" in rendered
    assert "[scheduler] pending queue drift detected" in rendered


@pytest.mark.asyncio
async def test_operational_surface_returns_empty_context() -> None:
    session = AsyncMock()

    with patch.object(
        MemoryPolicyService,
        "semantic_self_memory",
        AsyncMock(return_value=[_make_self_memory(1, "should not load")]),
    ) as mock_self_memory:
        context = await MemoryPolicyService.build_context(
            session,
            surface=MemorySurface.OPERATIONAL,
            query="fix patch",
            session_id="default",
        )

    assert context == MemoryPolicyContext()
    assert context.render() == ""
    mock_self_memory.assert_not_called()


@pytest.mark.asyncio
async def test_patch_analysis_surface_includes_architecture_and_related_incidents() -> None:
    session = AsyncMock()
    incident = _make_incident(
        "scheduler_error",
        "queue drift detected in scheduler loop",
        incident_id="current-incident",
    )

    with patch.object(
        MemoryPolicyService,
        "semantic_self_memory",
        AsyncMock(return_value=[_make_self_memory(99, "should not load")]),
    ) as mock_self_memory:
        with patch.object(
            MemoryPolicyService,
            "relevant_architecture_memory",
            AsyncMock(
                return_value=[
                    _make_architecture_memory(
                        "scheduler_loop",
                        "Owns queue reconciliation and worker wake-ups",
                        knowledge_factors={"risks": ["queue drift"]},
                    )
                ]
            ),
        ) as mock_architecture:
            with patch.object(
                MemoryPolicyService,
                "related_incidents",
                AsyncMock(
                    return_value=[
                        _make_incident(
                            "scheduler_error",
                            "Historical queue drift under worker saturation",
                            incident_id="prior-incident",
                            resolution_strategy="Restart scheduler workers and clear stale lease",
                            resolved=True,
                            fix_status="closed",
                        )
                    ]
                ),
            ) as mock_related_incidents:
                context = await MemoryPolicyService.build_context(
                    session,
                    surface=MemorySurface.PATCH_ANALYSIS,
                    query="scheduler queue drift",
                    incident=incident,
                )

    rendered = context.render()
    assert "## relevant architecture memory" in rendered
    assert "## related incident history" in rendered
    assert "scheduler_loop" in rendered
    assert "Historical queue drift under worker saturation" in rendered
    assert "Restart scheduler workers and clear stale lease" in rendered
    assert context.self_memory_lines == []
    assert context.conversation_lines == []
    assert context.incident_lines == []
    mock_self_memory.assert_not_called()
    mock_architecture.assert_awaited_once()
    mock_related_incidents.assert_awaited_once()
