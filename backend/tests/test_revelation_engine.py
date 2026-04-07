"""Tests for src.kortana.services.revelation_engine."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.kortana.models import ConversationMessage, RevelationMemory, SelfMemory
from src.kortana.services.revelation_engine import (
    RevelationEngine,
    _is_duplicate,
    get_revelation_model_info,
    get_token_stats,
)


# ---------------------------------------------------------------------------
# Pure function tests — no DB needed
# ---------------------------------------------------------------------------

class TestIsDuplicate:
    def test_exact_match(self):
        assert _is_duplicate("user builds features at night", ["user builds features at night"])

    def test_high_overlap(self):
        # 5 shared / 5 total = 1.0 overlap
        assert _is_duplicate("user builds at night often", ["user builds at night often now"])

    def test_below_threshold(self):
        # completely different words
        assert not _is_duplicate("database performance degrades slowly", ["user wakes late"])

    def test_empty_new_title(self):
        assert not _is_duplicate("", ["some existing title"])

    def test_empty_existing_list(self):
        assert not _is_duplicate("some new insight", [])

    def test_case_insensitive(self):
        assert _is_duplicate("Matt Prefers Night Coding", ["matt prefers night coding"])

    def test_partial_overlap_below_threshold(self):
        # 1 shared word "coding" out of 6 unique total = ~0.17, below 0.7
        assert not _is_duplicate("coding is fun today", ["swimming is great sport"])


class TestGetRevelationModelInfo:
    def test_returns_expected_keys(self):
        info = get_revelation_model_info()
        assert "preferred_model" in info
        assert "model" in info
        assert "model_lane" in info

    def test_values_are_strings(self):
        info = get_revelation_model_info()
        for v in info.values():
            assert isinstance(v, str)


class TestGetTokenStats:
    def test_returns_expected_keys(self):
        stats = get_token_stats()
        assert "session_tokens_used" in stats
        assert "session_token_budget" in stats
        assert "budget_remaining" in stats
        assert "budget_pct_used" in stats

    def test_remaining_is_non_negative(self):
        stats = get_token_stats()
        assert stats["budget_remaining"] >= 0

    def test_pct_is_between_0_and_100(self):
        stats = get_token_stats()
        assert 0.0 <= stats["budget_pct_used"] <= 100.0


# ---------------------------------------------------------------------------
# RevelationEngine with in-memory async session
# ---------------------------------------------------------------------------

def _make_session(rows: list | None = None) -> AsyncMock:
    """Build a minimal AsyncMock session that returns *rows* from execute()."""
    session = AsyncMock()
    result = MagicMock()
    if rows is None:
        rows = []
    result.scalars.return_value.all.return_value = rows
    result.scalar_one_or_none.return_value = rows[0] if rows else None
    result.scalar.return_value = len(rows)
    result.all.return_value = [(r.title,) for r in rows if hasattr(r, "title")]
    session.execute = AsyncMock(return_value=result)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    return session


def _make_revelation(**kwargs) -> RevelationMemory:
    defaults = dict(
        id=str(uuid.uuid4()),
        title="Test revelation title",
        content="This is the content of the revelation.",
        evidence=[],
        revelation_type="pattern",
        confidence=0.8,
        surfaced=False,
        acknowledged_at=None,
        source="revelation_engine",
        created_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    r = RevelationMemory(**{k: v for k, v in defaults.items()})
    return r


class TestShouldRun:
    @pytest.mark.asyncio
    async def test_should_run_when_no_recent_revelations(self):
        session = _make_session(rows=[])
        engine = RevelationEngine(session)
        assert await engine.should_run() is True

    @pytest.mark.asyncio
    async def test_should_not_run_when_recent_revelation_exists(self):
        recent = _make_revelation()
        session = _make_session(rows=[recent])
        engine = RevelationEngine(session)
        assert await engine.should_run() is False

    @pytest.mark.asyncio
    async def test_force_bypasses_cooldown(self):
        recent = _make_revelation()
        session = _make_session(rows=[recent])
        engine = RevelationEngine(session)
        # With force=True should always be True regardless of recent revelations
        assert await engine.should_run(force=True) is True


class TestGetUnsurfaced:
    @pytest.mark.asyncio
    async def test_returns_only_unsurfaced(self):
        unsurfaced = _make_revelation(surfaced=False)
        session = _make_session(rows=[unsurfaced])
        engine = RevelationEngine(session)
        results = await engine.get_unsurfaced()
        assert len(results) == 1
        assert results[0].surfaced is False

    @pytest.mark.asyncio
    async def test_respects_limit(self):
        rows = [_make_revelation(title=f"Revelation {i}") for i in range(10)]
        session = _make_session(rows=rows[:3])
        engine = RevelationEngine(session)
        results = await engine.get_unsurfaced(limit=3)
        assert len(results) <= 3


class TestMarkSurfaced:
    @pytest.mark.asyncio
    async def test_marks_and_returns_true(self):
        rev = _make_revelation()
        session = _make_session(rows=[rev])
        engine = RevelationEngine(session)
        result = await engine.mark_surfaced(rev.id)
        assert result is True
        assert rev.surfaced is True
        assert rev.acknowledged_at is not None

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self):
        session = _make_session(rows=[])
        engine = RevelationEngine(session)
        result = await engine.mark_surfaced("nonexistent-id")
        assert result is False


class TestListRevelations:
    @pytest.mark.asyncio
    async def test_returns_rows(self):
        rows = [_make_revelation(title=f"R{i}") for i in range(5)]
        session = _make_session(rows=rows)
        engine = RevelationEngine(session)
        results = await engine.list_revelations()
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_empty_list(self):
        session = _make_session(rows=[])
        engine = RevelationEngine(session)
        results = await engine.list_revelations()
        assert results == []


class TestGetStatus:
    @pytest.mark.asyncio
    async def test_returns_all_status_keys(self):
        rev = _make_revelation()
        session = AsyncMock()

        call_count = [0]

        async def execute_side_effect(stmt):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] <= 2:
                # count queries
                mock_result.scalar.return_value = call_count[0]
                mock_result.scalar_one_or_none.return_value = None
            else:
                # latest revelation query
                mock_result.scalar_one_or_none.return_value = rev
                mock_result.scalar.return_value = 2
            return mock_result

        session.execute = AsyncMock(side_effect=execute_side_effect)

        engine = RevelationEngine(session)
        status = await engine.get_status()

        assert status["status"] == "active"
        assert "total_revelations" in status
        assert "unsurfaced_revelations" in status
        assert "cooldown_hours" in status
        assert "minimum_observations" in status
        assert "model" in status
        assert "session_token_budget" in status


class TestParseAndStore:
    @pytest.mark.asyncio
    async def test_parses_valid_json_and_stores(self):
        session = AsyncMock()

        # Need to handle multiple execute() calls: _recent_revelation_titles returns []
        titles_result = MagicMock()
        titles_result.all.return_value = []
        session.execute = AsyncMock(return_value=titles_result)
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        engine = RevelationEngine(session)
        raw = json.dumps([
            {
                "title": "Matt codes consistently at night",
                "content": "Over the past month, nearly all commits happen after 10pm.",
                "evidence": ["git log shows 22:00+ timestamps"],
                "revelation_type": "pattern",
                "confidence": 0.85,
            }
        ])
        written = await engine._parse_and_store(raw)
        assert len(written) == 1
        assert written[0].title == "Matt codes consistently at night"
        assert written[0].confidence == pytest.approx(0.85)
        session.add.assert_called_once()
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_skips_low_confidence_revelations(self):
        session = AsyncMock()
        titles_result = MagicMock()
        titles_result.all.return_value = []
        session.execute = AsyncMock(return_value=titles_result)
        session.add = MagicMock()

        engine = RevelationEngine(session)
        raw = json.dumps([
            {
                "title": "Some weak pattern",
                "content": "Not very confident.",
                "evidence": [],
                "revelation_type": "pattern",
                "confidence": 0.3,  # below CONFIDENCE_THRESHOLD of 0.65
            }
        ])
        written = await engine._parse_and_store(raw)
        assert written == []
        session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_json_array_writes_nothing(self):
        session = AsyncMock()
        titles_result = MagicMock()
        titles_result.all.return_value = []
        session.execute = AsyncMock(return_value=titles_result)
        session.add = MagicMock()

        engine = RevelationEngine(session)
        written = await engine._parse_and_store("[]")
        assert written == []
        session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_json_returns_empty_list(self):
        session = AsyncMock()
        engine = RevelationEngine(session)
        written = await engine._parse_and_store("not valid json {{")
        assert written == []

    @pytest.mark.asyncio
    async def test_strips_markdown_code_blocks(self):
        session = AsyncMock()
        titles_result = MagicMock()
        titles_result.all.return_value = []
        session.execute = AsyncMock(return_value=titles_result)
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        engine = RevelationEngine(session)
        raw = "```json\n" + json.dumps([
            {
                "title": "Night owl pattern observed",
                "content": "Matt consistently works late.",
                "evidence": [],
                "revelation_type": "pattern",
                "confidence": 0.9,
            }
        ]) + "\n```"
        written = await engine._parse_and_store(raw)
        assert len(written) == 1

    @pytest.mark.asyncio
    async def test_deduplicates_similar_titles(self):
        session = AsyncMock()
        # Return a "recent" title that overlaps heavily
        existing_title = MagicMock()
        existing_title.__iter__ = MagicMock(return_value=iter([("Night owl pattern observed",)]))
        titles_result = MagicMock()
        titles_result.all.return_value = [("Night owl pattern observed",)]
        session.execute = AsyncMock(return_value=titles_result)
        session.add = MagicMock()

        engine = RevelationEngine(session)
        # Title with high word overlap to "Night owl pattern observed"
        raw = json.dumps([
            {
                "title": "night owl pattern observed again",
                "content": "Same insight repackaged.",
                "evidence": [],
                "revelation_type": "pattern",
                "confidence": 0.9,
            }
        ])
        written = await engine._parse_and_store(raw)
        assert written == []
        session.add.assert_not_called()


class TestSynthesise:
    @pytest.mark.asyncio
    async def test_skips_when_cooldown_active(self):
        recent = _make_revelation()
        session = _make_session(rows=[recent])
        engine = RevelationEngine(session)
        # should_run returns False (recent revelation exists) → synthesise returns []
        with patch.object(engine, "should_run", AsyncMock(return_value=False)):
            result = await engine.synthesise()
        assert result == []

    @pytest.mark.asyncio
    async def test_skips_when_too_few_observations(self):
        session = AsyncMock()

        async def execute_side_effect(stmt):
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_result.scalar_one_or_none.return_value = None
            return mock_result

        session.execute = AsyncMock(side_effect=execute_side_effect)

        engine = RevelationEngine(session)
        with patch.object(engine, "should_run", AsyncMock(return_value=True)):
            with patch(
                "src.kortana.services.revelation_engine._gather_git_activity",
                return_value=[],
            ):
                result = await engine.synthesise()
        assert result == []

    @pytest.mark.asyncio
    async def test_full_synthesis_flow(self):
        session = AsyncMock()

        call_index = [0]

        async def execute_side_effect(stmt):
            call_index[0] += 1
            mock_result = MagicMock()
            if call_index[0] == 1:
                # _gather_self_memories
                mem = MagicMock(spec=SelfMemory)
                mem.created_at = datetime.utcnow()
                mem.source = "test"
                mem.summary = "Test memory summary " * 3
                mock_result.scalars.return_value.all.return_value = [mem] * 6
            elif call_index[0] == 2:
                # _gather_conversation_topics
                msg = MagicMock(spec=ConversationMessage)
                msg.created_at = datetime.utcnow()
                msg.content = "A test conversation message."
                mock_result.scalars.return_value.all.return_value = [msg] * 6
            else:
                # _recent_revelation_titles
                mock_result.all.return_value = []
                mock_result.scalars.return_value.all.return_value = []
            return mock_result

        session.execute = AsyncMock(side_effect=execute_side_effect)
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        llm_response = json.dumps([
            {
                "title": "High focus on voice integration",
                "content": "Matt has been consistently focusing on voice features this week.",
                "evidence": ["voice_daemon.py changed 3 times", "voice-related conversation topics"],
                "revelation_type": "pattern",
                "confidence": 0.78,
            }
        ])

        engine = RevelationEngine(session)
        with patch.object(engine, "should_run", AsyncMock(return_value=True)):
            with patch(
                "src.kortana.services.revelation_engine._gather_git_activity",
                return_value=["2026-04-05 feat: voice mode improvements"] * 8,
            ):
                with patch(
                    "src.kortana.services.revelation_engine._call_gemini_revelation",
                    AsyncMock(return_value=llm_response),
                ):
                    written = await engine.synthesise()

        assert len(written) == 1
        assert written[0].title == "High focus on voice integration"
        assert written[0].confidence == pytest.approx(0.78)

    @pytest.mark.asyncio
    async def test_synthesise_with_force(self):
        session = AsyncMock()

        async def execute_side_effect(stmt):
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_result.all.return_value = []
            return mock_result

        session.execute = AsyncMock(side_effect=execute_side_effect)

        engine = RevelationEngine(session)
        # force=True should bypass cooldown check but still return [] because
        # there are too few observations
        with patch(
            "src.kortana.services.revelation_engine._gather_git_activity",
            return_value=[],
        ):
            result = await engine.synthesise(force=True)
        assert result == []


class TestGatherHelpers:
    @pytest.mark.asyncio
    async def test_gather_self_memories_formats_entries(self):
        from src.kortana.services.revelation_engine import _gather_self_memories

        mem = MagicMock(spec=SelfMemory)
        mem.created_at = datetime(2026, 4, 5, 10, 0, 0)
        mem.source = "voice-diary"
        mem.summary = "Today I coded a lot."
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [mem]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result_mock)

        lines = await _gather_self_memories(session, limit=10)
        assert len(lines) == 1
        assert "2026-04-05" in lines[0]
        assert "voice-diary" in lines[0]
        assert "Today I coded a lot." in lines[0]

    @pytest.mark.asyncio
    async def test_gather_conversation_topics_formats_entries(self):
        from src.kortana.services.revelation_engine import _gather_conversation_topics

        msg = MagicMock(spec=ConversationMessage)
        msg.created_at = datetime(2026, 4, 5, 11, 0, 0)
        msg.content = "What time is it?"
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [msg]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result_mock)

        lines = await _gather_conversation_topics(session, limit=10)
        assert len(lines) == 1
        assert "2026-04-05" in lines[0]
        assert "What time is it?" in lines[0]

    def test_gather_git_activity_returns_list(self):
        from src.kortana.services.revelation_engine import _gather_git_activity

        lines = _gather_git_activity(repo_root="c:/kortana", limit=5)
        # Should return a list (empty is fine if git not accessible)
        assert isinstance(lines, list)

    def test_gather_git_activity_handles_failure_gracefully(self):
        from src.kortana.services.revelation_engine import _gather_git_activity

        lines = _gather_git_activity(repo_root="/nonexistent/path/xyz", limit=5)
        assert lines == []
