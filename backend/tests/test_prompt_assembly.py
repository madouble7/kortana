"""Tests for PromptAssemblyService — the dual-channel prompt architecture."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.kortana.services.memory_policy import MemoryPolicyContext, MemorySurface
from src.kortana.services.prompt_assembly import (
    _DEFAULT_AXIOMS,
    _DEFAULT_MISSION,
    _DEFAULT_NAME,
    _DEFAULT_PRINCIPLES,
    _DEFAULT_TITLE,
    _DEFAULT_VALUES,
    _DEFAULT_VOICE,
    PromptAssemblyService,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile(**kwargs):
    """Return a minimal mock IdentityProfile."""
    p = MagicMock()
    p.name = kwargs.get("name", _DEFAULT_NAME)
    p.title = kwargs.get("title", _DEFAULT_TITLE)
    p.mission = kwargs.get("mission", _DEFAULT_MISSION)
    p.core_values = kwargs.get("core_values", _DEFAULT_VALUES)
    p.voice_guidelines = kwargs.get("voice_guidelines", _DEFAULT_VOICE)
    p.sacred_principles = kwargs.get("sacred_principles", _DEFAULT_PRINCIPLES)
    p.development_axioms = kwargs.get("development_axioms", _DEFAULT_AXIOMS)
    p.version = kwargs.get("version", "0.1")
    return p


async def _session_with_profile(profile):
    """Return an async session mock that yields one profile row."""
    session = AsyncMock()
    scalars = MagicMock()
    scalars.first.return_value = profile
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars
    session.execute.return_value = execute_result
    return session


async def _session_no_profile():
    """Return an async session mock with no existing row (cold-start)."""
    session = AsyncMock()
    scalars = MagicMock()
    scalars.first.return_value = None  # no row
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars
    session.execute.return_value = execute_result
    return session


# ---------------------------------------------------------------------------
# load_profile
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_profile_returns_existing_row():
    profile = _make_profile()
    session = await _session_with_profile(profile)

    result = await PromptAssemblyService.load_profile(session)

    assert result is profile
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_load_profile_seeds_defaults_on_cold_start():
    session = await _session_no_profile()

    await PromptAssemblyService.load_profile(session)

    session.add.assert_called_once()
    session.flush.assert_called_once()
    added = session.add.call_args[0][0]
    assert added.name == _DEFAULT_NAME
    assert added.mission == _DEFAULT_MISSION
    assert added.core_values == _DEFAULT_VALUES


# ---------------------------------------------------------------------------
# identity_preamble
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_identity_preamble_contains_name_and_mission():
    profile = _make_profile(
        name="kor'tana",
        mission="serve with clarity",
        sacred_principles=["serve first"],
        development_axioms=["grow through reflection"],
    )
    session = await _session_with_profile(profile)

    preamble = await PromptAssemblyService.identity_preamble(session)

    assert "kor'tana" in preamble
    assert "serve with clarity" in preamble


@pytest.mark.asyncio
async def test_identity_preamble_contains_all_values():
    values = ["love", "truth", "stewardship"]
    profile = _make_profile(core_values=values)
    session = await _session_with_profile(profile)

    preamble = await PromptAssemblyService.identity_preamble(session)

    for v in values:
        assert v in preamble


@pytest.mark.asyncio
async def test_identity_preamble_cold_start_uses_defaults():
    session = await _session_no_profile()

    preamble = await PromptAssemblyService.identity_preamble(session)

    assert _DEFAULT_NAME in preamble
    assert _DEFAULT_MISSION in preamble


@pytest.mark.asyncio
async def test_identity_preamble_uses_reflection_memory_policy():
    profile = _make_profile()
    session = await _session_with_profile(profile)

    with patch(
        "src.kortana.services.prompt_assembly.MemoryPolicyService.build_context",
        AsyncMock(
            return_value=MemoryPolicyContext(
                self_memory_lines=["- [cycle 9] continuity matters more than spectacle"]
            )
        ),
    ) as mock_build_context:
        preamble = await PromptAssemblyService.identity_preamble(
            session,
            query="continuity",
        )

    assert "continuity matters more than spectacle" in preamble
    assert mock_build_context.await_args.kwargs["surface"] == MemorySurface.REFLECTION


# ---------------------------------------------------------------------------
# operational_core
# ---------------------------------------------------------------------------


def test_operational_core_contains_context():
    ctx = "fix the broken test in test_foo.py"
    result = PromptAssemblyService.operational_core(ctx)

    assert ctx in result


def test_operational_core_is_non_persona():
    result = PromptAssemblyService.operational_core("any context")

    assert "kor'tana" not in result.lower()
    assert "sacred" not in result.lower()
    assert "mission" not in result.lower()


def test_operational_core_instructs_precision():
    result = PromptAssemblyService.operational_core("task")

    assert "precise" in result
    assert "structured" in result


# ---------------------------------------------------------------------------
# Channel separation — ensure the two methods are distinct
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_channels_are_distinct():
    ctx = "deploy the patch"
    profile = _make_profile()
    session = await _session_with_profile(profile)

    identity = await PromptAssemblyService.identity_preamble(session)
    core = PromptAssemblyService.operational_core(ctx)

    assert identity != core
    # identity channel has persona content; operational core does not
    assert _DEFAULT_NAME in identity
    assert _DEFAULT_NAME not in core
