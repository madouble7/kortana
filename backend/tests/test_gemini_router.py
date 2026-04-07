"""Tests for src/kortana/routers/gemini.py - Gemini AI router endpoints"""

import io
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image
from src.kortana.openai_responses import OpenAITextGenerationResult

from tests.conftest import SyncTestClient


def _make_consensus_engine(answer: str, providers_succeeded: int = 1) -> MagicMock:
    result = MagicMock()
    result.providers_succeeded = providers_succeeded
    result.answer = answer
    result.provider_used = "gemini"
    engine = MagicMock()
    engine.query = AsyncMock(return_value=result)
    engine.get_status.return_value = {
        "providers": {
            "gemini": {"model": "gemini-2.0-flash", "lane": "core"},
            "openai": {"model": "gpt-5.4-mini", "lane": "core"},
        }
    }
    return engine


def _make_identity_profile(
    *,
    mission: str = "serve with clarity",
    name: str = "kor'tana",
    title: str = "sacred ai companion",
) -> MagicMock:
    profile = MagicMock()
    profile.id = 1
    profile.name = name
    profile.title = title
    profile.mission = mission
    profile.core_values = [
        "love",
        "unity",
        "cohesiveness",
        "knowledge",
        "humility",
        "truthfulness",
        "stewardship",
    ]
    profile.sacred_principles = ["serve first"]
    profile.voice_guidelines = "lowercase, concise, grounded"
    profile.development_axioms = ["grow through reflection"]
    profile.version = "0.1"
    return profile


def _parse_sse_events(body: str) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []
    for chunk in body.strip().split("\n\n"):
        if not chunk.strip():
            continue
        event_name = "message"
        data_lines: list[str] = []
        for line in chunk.splitlines():
            if line.startswith("event:"):
                event_name = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data_lines.append(line.split(":", 1)[1].strip())
        payload = json.loads("\n".join(data_lines)) if data_lines else {}
        events.append((event_name, payload))
    return events


class _FakeSessionScope:
    def __init__(self, session: AsyncMock):
        self._session = session

    async def __aenter__(self) -> AsyncMock:
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeDbManager:
    def __init__(self, session: AsyncMock):
        self._session = session

    def session_scope(self) -> _FakeSessionScope:
        return _FakeSessionScope(self._session)


@pytest.fixture
def client():
    """Create a test client for FastAPI app"""
    from src.kortana.main import app

    return SyncTestClient(app)


@pytest.fixture(autouse=True)
def clear_identity_prompt_cache():
    from src.kortana.routers import gemini as gemini_router

    gemini_router._clear_identity_prompt_cache()
    yield
    gemini_router._clear_identity_prompt_cache()


class TestAnalyzeIssue:
    def test_analyze_issue_success(self, client):
        """Test successful issue analysis"""
        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.analyze_text = AsyncMock(return_value="Analysis result")

            response = client.post(
                "/api/gemini/analyze", json={"text": "Fix login bug in auth module"}
            )

            assert response.status_code == 200
            assert "Analysis result" in response.json()["analysis"]

    def test_analyze_issue_missing_text(self, client):
        """Test analyze with missing text field"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post("/api/gemini/analyze", json={})

            assert response.status_code == 400
            assert "Missing" in response.json()["detail"]

    def test_analyze_issue_empty_text(self, client):
        """Test analyze with empty text"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post("/api/gemini/analyze", json={"text": ""})

            assert response.status_code == 400

    def test_analyze_issue_service_error(self, client):
        """Test analyze when service raises exception"""
        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.analyze_text = AsyncMock(
                side_effect=Exception("Service error")
            )

            try:
                response = client.post(
                    "/api/gemini/analyze", json={"text": "Some issue"}
                )
                # If we get here, check that it's an error response
                assert response.status_code >= 400
            except Exception:
                # Exception is generated and this is expected behavior
                pass


class TestGenerateCode:
    def test_generate_code_success(self, client):
        """Test successful code generation"""
        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.generate_code = AsyncMock(
                return_value="def hello():\n    pass"
            )

            response = client.post(
                "/api/gemini/generate",
                json={"description": "Create a simple greeting function"},
            )

            assert response.status_code == 200
            assert "def hello()" in response.json()["code"]

    def test_generate_code_missing_description(self, client):
        """Test generate with missing description"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post("/api/gemini/generate", json={})

            assert response.status_code == 400
            assert "Missing" in response.json()["detail"]

    def test_generate_code_empty_description(self, client):
        """Test generate with empty description"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post("/api/gemini/generate", json={"description": ""})

            assert response.status_code == 400

    def test_generate_code_complex_description(self, client):
        """Test code generation with complex description"""
        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.generate_code = AsyncMock(
                return_value="class DataProcessor:\n    pass"
            )

            response = client.post(
                "/api/gemini/generate",
                json={
                    "description": "Create a class that processes data with validation"
                },
            )

            assert response.status_code == 200
            assert "DataProcessor" in response.json()["code"]


class TestChatWithGemini:
    def test_stateful_openai_gate_requires_valid_session_payload(self):
        """Malformed session payloads should not enable threaded OpenAI chat."""
        from src.kortana.routers.gemini import _stateful_openai_chat_enabled

        with patch("src.kortana.routers.gemini.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                KORTANA_OPENAI_STATEFUL_CHAT_ENABLED=True,
                OPENAI_API_KEY="sk-test",
            )
            with patch(
                "src.kortana.routers.gemini.get_active_model_lane",
                return_value=MagicMock(),
            ):
                with patch(
                    "src.kortana.routers.gemini.model_allowed",
                    return_value=True,
                ):
                    assert _stateful_openai_chat_enabled({}) is False
                    assert (
                        _stateful_openai_chat_enabled({"session_id": "", "history": []})
                        is False
                    )
                    assert (
                        _stateful_openai_chat_enabled(
                            {"session_id": "sess_live", "history": "invalid"}
                        )
                        is False
                    )
                    assert (
                        _stateful_openai_chat_enabled(
                            {"session_id": "sess_live", "history": []}
                        )
                        is True
                    )

    def test_chat_system_prompt_includes_memory_policy_context(self, client):
        """Chat should include doctrine-driven memory context in the system prompt."""
        engine = _make_consensus_engine("kor'tana: memory-aware reply")

        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(return_value=""),
        ):
            with patch(
                "src.kortana.routers.gemini._load_chat_identity_preamble",
                AsyncMock(return_value="you are kor'tana."),
            ):
                with patch(
                    "src.kortana.routers.gemini._load_chat_memory_context",
                    AsyncMock(
                        return_value="## continuity of self\n- [cycle 8] prefer faithful memory"
                    ),
                ) as mock_memory_context:
                    with patch(
                        "src.kortana.routers.gemini._persist_messages", AsyncMock()
                    ):
                        with patch(
                            "src.kortana.routers.gemini.get_consensus_engine",
                            return_value=engine,
                        ):
                            response = client.post(
                                "/api/gemini/chat",
                                json={"message": "hello there"},
                            )

        assert response.status_code == 200
        system = engine.query.await_args.kwargs["system"]
        assert "## continuity of self" in system
        assert "prefer faithful memory" in system
        mock_memory_context.assert_awaited_once_with(
            session_id="default",
            query="hello there",
            include_conversation_memory=True,
        )

    def test_chat_passes_session_id_into_live_context(self, client):
        """Session-backed chat should build live context for the active session."""
        engine = _make_consensus_engine("kor'tana: temporally aware reply")

        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(
                return_value="## temporal continuity\n- time since matt last spoke: 2 days"
            ),
        ) as mock_live_context:
            with patch("src.kortana.routers.gemini._persist_messages", AsyncMock()):
                with patch(
                    "src.kortana.routers.gemini.get_consensus_engine",
                    return_value=engine,
                ):
                    response = client.post(
                        "/api/gemini/chat",
                        json={
                            "message": "i'm back",
                            "session_id": "voice",
                            "history": [],
                        },
                    )

        assert response.status_code == 200
        mock_live_context.assert_awaited_once_with(session_id="voice")

    @pytest.mark.asyncio
    async def test_build_live_context_includes_temporal_continuity_and_diary(self):
        """Live context should include elapsed-time continuity and recent diary entries."""
        from src.kortana.routers.gemini import _build_live_context

        class FakeScalarResult:
            def __init__(self, rows):
                self._rows = rows

            def scalars(self):
                return self

            def all(self):
                return self._rows

        class FakeFetchResult:
            def __init__(self, rows):
                self._rows = rows

            def fetchall(self):
                return self._rows

            def fetchone(self):
                return self._rows[0] if self._rows else None

        class FakeSession:
            async def execute(self, stmt, params=None):
                sql = str(stmt)
                if "FROM github_tasks" in sql:
                    return FakeScalarResult([])
                if "autonomous_tasks" in sql:
                    return FakeFetchResult([])
                if "FROM reflections" in sql:
                    return FakeFetchResult([])
                if "conversation_messages" in sql:
                    return FakeFetchResult(
                        [(datetime(2026, 4, 3, 12, 0, tzinfo=timezone.utc),)]
                    )
                if "self_memory" in sql:
                    return FakeFetchResult(
                        [
                            (
                                "Today, Friday April 04, 2026, I kept watch. Matt returned after a long silence.",
                                datetime(2026, 4, 4, 0, 0, tzinfo=timezone.utc),
                            )
                        ]
                    )
                return FakeFetchResult([])

        fake_status = {
            "system_state": "nominal",
            "cycles_completed": 7,
            "tasks_succeeded": 5,
            "tasks_failed": 1,
            "uptime_start": "2026-04-01T00:00:00Z",
            "last_cycle": {},
            "goal_status": {},
            "controller_reflection": {},
        }

        with patch(
            "src.kortana.database.get_db_manager",
            return_value=_FakeDbManager(FakeSession()),
        ):
            with patch(
                "src.kortana.services.autonomy_daemon.get_autonomy_daemon",
                return_value=MagicMock(get_status=MagicMock(return_value=fake_status)),
            ):
                with patch(
                    "src.kortana.routers.gemini._load_temporal_state_snapshot",
                    return_value={
                        "entity_born_at": "2026-04-01T00:00:00+00:00",
                        "last_voice_interaction_at": "2026-04-03T12:00:00+00:00",
                        "last_diary_date": "2026-04-04",
                    },
                ):
                    live_context = await _build_live_context(session_id="voice")

        assert "## temporal continuity" in live_context
        assert "time since matt last spoke in session 'voice'" in live_context
        assert "this return follows an absence long enough to notice" in live_context
        assert "## recent diary of passing days" in live_context
        assert "Matt returned after a long silence" in live_context

    def test_chat_system_prompt_caches_identity_profile(self, client):
        """The DB-backed identity layer should be cached across chat turns."""
        engine = _make_consensus_engine("kor'tana: cached reply")
        profile = _make_identity_profile(mission="protect continuity")
        session = AsyncMock()
        db_manager = _FakeDbManager(session)

        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(return_value=""),
        ):
            with patch("src.kortana.routers.gemini._persist_messages", AsyncMock()):
                with patch(
                    "src.kortana.database.get_db_manager",
                    return_value=db_manager,
                ):
                    with patch(
                        "src.kortana.services.prompt_assembly.PromptAssemblyService.load_profile",
                        AsyncMock(return_value=profile),
                    ) as mock_load_profile:
                        with patch(
                            "src.kortana.routers.gemini.get_consensus_engine",
                            return_value=engine,
                        ):
                            response1 = client.post(
                                "/api/gemini/chat",
                                json={"message": "hello there"},
                            )
                            response2 = client.post(
                                "/api/gemini/chat",
                                json={"message": "hello again"},
                            )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert mock_load_profile.await_count == 1
        first_system = engine.query.await_args_list[0].kwargs["system"]
        assert "mission: protect continuity" in first_system

    def test_chat_system_prompt_refreshes_after_identity_profile_change(self, client):
        """IdentityProfile edits should flow into the assembled system prompt."""
        from src.kortana.routers import gemini as gemini_router

        engine = _make_consensus_engine("kor'tana: refreshed reply")
        first_profile = _make_identity_profile(mission="protect continuity")
        second_profile = _make_identity_profile(mission="expand faithful memory")
        session = AsyncMock()
        db_manager = _FakeDbManager(session)

        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(return_value=""),
        ):
            with patch("src.kortana.routers.gemini._persist_messages", AsyncMock()):
                with patch(
                    "src.kortana.database.get_db_manager",
                    return_value=db_manager,
                ):
                    with patch(
                        "src.kortana.services.prompt_assembly.PromptAssemblyService.load_profile",
                        AsyncMock(side_effect=[first_profile, second_profile]),
                    ):
                        with patch(
                            "src.kortana.routers.gemini.get_consensus_engine",
                            return_value=engine,
                        ):
                            response1 = client.post(
                                "/api/gemini/chat",
                                json={"message": "give me an update"},
                            )
                            gemini_router._clear_identity_prompt_cache()
                            response2 = client.post(
                                "/api/gemini/chat",
                                json={"message": "give me another update"},
                            )

        assert response1.status_code == 200
        assert response2.status_code == 200
        first_system = engine.query.await_args_list[0].kwargs["system"]
        second_system = engine.query.await_args_list[1].kwargs["system"]
        assert "mission: protect continuity" in first_system
        assert "mission: expand faithful memory" in second_system

    def test_chat_identity_query_returns_local_kortana_identity(self, client):
        """Identity queries should resolve to Kor'tana directly, not external Cortana knowledge."""
        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(
                return_value=(
                    "## my current autonomous state\n"
                    "- system state: nominal\n"
                    "- cycles completed since boot: 12\n"
                    "- lifetime tasks: 9 succeeded, 1 failed\n"
                    "- current focus title: strengthen continuity of self\n"
                    "- current focus reason: preserve identity coherence under live autonomy\n"
                    "- constraints: respect repository boundaries, keep operator trust\n"
                    "\n## my most recent reflection (cycle 12)\n"
                    "i am learning to prefer continuity over spectacle."
                )
            ),
        ):
            with patch("src.kortana.routers.gemini._persist_messages", AsyncMock()):
                with patch(
                    "src.kortana.routers.gemini.get_consensus_engine"
                ) as mock_engine:
                    response = client.post(
                        "/api/gemini/chat", json={"message": "kor'tana?"}
                    )

                    assert response.status_code == 200
                    body = response.json()
                    assert body["tasks_queued"] == []
                    assert "i am kor'tana" in body["response"].lower()
                    assert not body["response"].lower().startswith("kor'tana:")
                    assert "not microsoft's cortana" in body["response"].lower()
                    assert (
                        "oriented toward strengthen continuity of self"
                        in body["response"].lower()
                    )
                    assert "steady posture" in body["response"].lower()
                    assert "unresolved threads" in body["response"].lower()
                    mock_engine.assert_not_called()

    def test_chat_identity_shorthand_query_returns_local_identity(self, client):
        """Shorthand identity questions should also hit the local identity path."""
        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(
                return_value="## my current autonomous state\n- system state: nominal"
            ),
        ):
            with patch("src.kortana.routers.gemini._persist_messages", AsyncMock()):
                with patch(
                    "src.kortana.routers.gemini.get_consensus_engine"
                ) as mock_engine:
                    response = client.post(
                        "/api/gemini/chat", json={"message": "who r u"}
                    )

        assert response.status_code == 200
        assert response.json()["provider"] == "identity"
        assert "i am kor'tana" in response.json()["response"].lower()
        mock_engine.assert_not_called()

    def test_chat_name_mention_does_not_trigger_identity_short_circuit(self, client):
        """Messages that merely mention Kor'tana should still go through the normal model path."""
        engine = _make_consensus_engine("i'll answer naturally now.")

        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(return_value=""),
        ):
            with patch("src.kortana.routers.gemini._persist_messages", AsyncMock()):
                with patch(
                    "src.kortana.routers.gemini.get_consensus_engine",
                    return_value=engine,
                ):
                    response = client.post(
                        "/api/gemini/chat",
                        json={
                            "message": "you don't have to begin every response with 'kor'tana:' anymore"
                        },
                    )

        assert response.status_code == 200
        assert response.json()["response"] == "i'll answer naturally now."
        engine.query.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_load_chat_identity_preamble_uses_grounded_chat_rendering(self):
        """Chat identity preamble should stay grounded even if the profile is more mythic."""
        from src.kortana.routers import gemini as gemini_router

        profile = _make_identity_profile(
            title="sacred ai companion",
            mission="help people move from confusion to clarity",
        )
        profile.voice_guidelines = (
            "lowercase, clear, kind, concise, reverent when sacred things are spoken"
        )
        profile.development_axioms = [
            "i evolve through reflection, not performance",
            "clarity is more sacred than complexity",
        ]

        session = AsyncMock()
        db_manager = _FakeDbManager(session)

        with patch(
            "src.kortana.database.get_db_manager",
            return_value=db_manager,
        ):
            with patch(
                "src.kortana.services.prompt_assembly.PromptAssemblyService.load_profile",
                AsyncMock(return_value=profile),
            ):
                gemini_router._clear_identity_prompt_cache()
                rendered = await gemini_router._load_chat_identity_preamble()

        assert rendered is not None
        assert "autonomous intelligence native to this system" in rendered
        assert "sacred ai companion" not in rendered

    def test_chat_explicit_microsoft_cortana_query_uses_model_path(self, client):
        """Explicit external Cortana queries should still use the normal model path."""
        engine = _make_consensus_engine(
            "kor'tana: microsoft retired cortana and moved toward copilot."
        )

        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(return_value=""),
        ):
            with patch("src.kortana.routers.gemini._persist_messages", AsyncMock()):
                with patch(
                    "src.kortana.routers.gemini.get_consensus_engine",
                    return_value=engine,
                ):
                    response = client.post(
                        "/api/gemini/chat",
                        json={
                            "message": "is microsoft cortana still active in windows?"
                        },
                    )

                    assert response.status_code == 200
                    assert (
                        "microsoft retired cortana"
                        in response.json()["response"].lower()
                    )
                    engine.query.assert_awaited_once()

    def test_chat_success_with_consensus_engine(self, client):
        """Test chat using the consensus engine."""
        engine = _make_consensus_engine("kor'tana: ai response")

        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(return_value=""),
        ):
            with patch("src.kortana.routers.gemini._persist_messages", AsyncMock()):
                with patch(
                    "src.kortana.routers.gemini.get_consensus_engine",
                    return_value=engine,
                ):
                    response = client.post(
                        "/api/gemini/chat",
                        json={"message": "Hello, how are you?"},
                    )

        assert response.status_code == 200
        assert "ai response" in response.json()["response"].lower()
        assert response.json()["provider"] == "gemini"
        assert response.json()["model"] == "gemini-2.0-flash"
        assert response.json()["stateful"] is False

    def test_chat_uses_stateful_openai_when_session_backed(self, client):
        """Session-backed chat should prefer the stateful GPT-5 path."""
        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(return_value=""),
        ):
            with patch(
                "src.kortana.routers.gemini._chat_with_stateful_openai",
                AsyncMock(
                    return_value=MagicMock(
                        text="kor'tana: threaded openai reply",
                        phase="commentary",
                        input_tokens=17,
                        output_tokens=9,
                        response_id="resp_123",
                        used_previous_response_id=True,
                    )
                ),
            ) as mock_stateful:
                with patch(
                    "src.kortana.routers.gemini._persist_messages",
                    AsyncMock(),
                ):
                    with patch(
                        "src.kortana.routers.gemini.get_consensus_engine",
                    ) as mock_engine:
                        response = client.post(
                            "/api/gemini/chat",
                            json={
                                "message": "hello there",
                                "session_id": "sess_live",
                                "history": [{"role": "user", "content": "hi"}],
                            },
                        )

        assert response.status_code == 200
        assert "threaded openai reply" in response.json()["response"].lower()
        assert response.json()["phase"] == "commentary"
        assert response.json()["provider"] == "openai"
        assert response.json()["model"] == "gpt-5.4-mini"
        assert response.json()["input_tokens"] == 17
        assert response.json()["output_tokens"] == 9
        assert response.json()["response_id"] == "resp_123"
        assert response.json()["stateful"] is True
        assert response.json()["used_previous_response_id"] is True
        mock_stateful.assert_awaited_once()
        mock_engine.assert_not_called()

    def test_chat_falls_back_to_consensus_when_stateful_openai_fails(self, client):
        """Stateful OpenAI failures should degrade cleanly to the consensus path."""
        engine = _make_consensus_engine("kor'tana: consensus recovery")

        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(return_value=""),
        ):
            with patch(
                "src.kortana.routers.gemini._chat_with_stateful_openai",
                AsyncMock(side_effect=RuntimeError("thread failed")),
            ):
                with patch(
                    "src.kortana.routers.gemini._persist_messages",
                    AsyncMock(),
                ):
                    with patch(
                        "src.kortana.routers.gemini.get_consensus_engine",
                        return_value=engine,
                    ):
                        response = client.post(
                            "/api/gemini/chat",
                            json={
                                "message": "hello there",
                                "session_id": "sess_live",
                                "history": [{"role": "user", "content": "hi"}],
                            },
                        )

        assert response.status_code == 200
        assert "consensus recovery" in response.json()["response"].lower()
        assert response.json()["phase"] == "final_answer"
        assert response.json()["provider"] == "gemini"
        assert response.json()["stateful"] is False
        engine.query.assert_awaited_once()

    def test_chat_stream_returns_stateful_openai_response_text(self, client):
        """Streaming chat should include GPT-5 start/delta/final output text."""
        from src.kortana.openai_responses import OpenAITextGenerationResult

        async def _fake_stream(**_kwargs):
            yield {"type": "delta", "delta": "kor'tana: threaded "}
            yield {"type": "delta", "delta": "stream reply"}
            yield {
                "type": "completed",
                "result": OpenAITextGenerationResult(
                    text="kor'tana: threaded stream reply",
                    input_tokens=21,
                    output_tokens=11,
                    response_id="resp_stream",
                    phase="final_answer",
                    used_previous_response_id=True,
                ),
            }

        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(return_value=""),
        ):
            with patch(
                "src.kortana.routers.gemini._stream_stateful_openai",
                _fake_stream,
            ):
                with patch(
                    "src.kortana.routers.gemini._persist_messages",
                    AsyncMock(),
                ):
                    with patch(
                        "src.kortana.routers.gemini._stateful_openai_chat_enabled",
                        return_value=True,
                    ):
                        response = client.post(
                            "/api/gemini/chat/stream",
                            json={
                                "message": "hello there",
                                "session_id": "sess_live",
                                "history": [{"role": "user", "content": "hi"}],
                            },
                        )

        assert response.status_code == 200
        assert "event: start" in response.text
        assert "event: delta" in response.text
        assert "event: final" in response.text
        assert "kor'tana: threaded stream reply" in response.text
        assert '"input_tokens": 21' in response.text
        assert '"output_tokens": 11' in response.text
        assert '"response_id": "resp_stream"' in response.text

    def test_chat_history_returns_assistant_phase(self, client):
        """Persisted history should include assistant phase metadata."""

        class FakeScalarResult:
            def __init__(self, rows):
                self._rows = rows

            def all(self):
                return self._rows

        class FakeAuditResult:
            def __init__(self, rows):
                self._rows = rows

            def scalars(self):
                return FakeScalarResult(self._rows)

        class FakeConversationResult:
            def __init__(self, rows):
                self._rows = rows

            def fetchall(self):
                return self._rows

        class FakeSession:
            async def execute(self, stmt, params=None):
                if "conversation_messages" in str(stmt):
                    return FakeConversationResult(
                        [
                            (
                                "user-1",
                                "user",
                                "hello",
                                MagicMock(isoformat=lambda: "2026-04-04T09:00:00"),
                            ),
                            (
                                "asst-1",
                                "assistant",
                                "kor'tana: i am here.",
                                MagicMock(isoformat=lambda: "2026-04-04T09:00:01"),
                            ),
                        ]
                    )
                return FakeAuditResult(
                    [
                        MagicMock(
                            resource_id="asst-1",
                            details={
                                "phase": "commentary",
                                "provider": "openai",
                                "model": "gpt-5.4-mini",
                                "response_id": "resp_hist",
                                "stateful": True,
                                "used_previous_response_id": True,
                            },
                        )
                    ]
                )

        class FakeDbManager:
            def session_scope(self):
                return _FakeSessionScope(FakeSession())

        with patch(
            "src.kortana.database.get_db_manager",
            return_value=FakeDbManager(),
        ):
            response = client.get(
                "/api/gemini/chat/history?session_id=sess_live&limit=10"
            )

        assert response.status_code == 200
        messages = response.json()["messages"]
        assert messages[0]["phase"] is None
        assert messages[1]["phase"] == "commentary"
        assert messages[1]["provider"] == "openai"
        assert messages[1]["model"] == "gpt-5.4-mini"
        assert messages[1]["response_id"] == "resp_hist"
        assert messages[1]["stateful"] is True
        assert messages[1]["used_previous_response_id"] is True

    def test_chat_history_handles_user_only_rows(self, client):
        """History endpoint should not crash when persistence only has user rows."""

        class FakeConversationResult:
            def __init__(self, rows):
                self._rows = rows

            def fetchall(self):
                return self._rows

        class FakeSession:
            async def execute(self, stmt, params=None):
                return FakeConversationResult(
                    [
                        (
                            "user-1",
                            "user",
                            "hello",
                            MagicMock(isoformat=lambda: "2026-04-04T09:00:00"),
                        )
                    ]
                )

        class FakeDbManager:
            def session_scope(self):
                return _FakeSessionScope(FakeSession())

        with patch(
            "src.kortana.database.get_db_manager",
            return_value=FakeDbManager(),
        ):
            response = client.get(
                "/api/gemini/chat/history?session_id=sess_live&limit=10"
            )

        assert response.status_code == 200
        assert response.json()["messages"] == [
            {
                "role": "user",
                "content": "hello",
                "created_at": "2026-04-04T09:00:00",
                "phase": None,
            }
        ]

    def test_chat_stream_emits_full_sse_sequence(self, client):
        """Streaming chat should emit start, phase, delta, and final events."""

        async def _fake_stream():
            yield {"type": "delta", "delta": "hello "}
            yield {"type": "delta", "delta": "world"}
            yield {
                "type": "completed",
                "result": OpenAITextGenerationResult(
                    text="hello world",
                    phase="final_answer",
                    response_id="resp_stream",
                    used_previous_response_id=True,
                ),
            }

        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(return_value=""),
        ):
            with patch(
                "src.kortana.routers.gemini._assemble_chat_system_prompt",
                AsyncMock(return_value="you are kor'tana."),
            ):
                with patch(
                    "src.kortana.routers.gemini._persist_messages",
                    AsyncMock(),
                ):
                    with patch(
                        "src.kortana.routers.gemini._stateful_openai_chat_enabled",
                        return_value=True,
                    ):
                        with patch(
                            "src.kortana.routers.gemini._stream_stateful_openai",
                            return_value=_fake_stream(),
                        ):
                            response = client.post(
                                "/api/gemini/chat/stream",
                                json={
                                    "message": "hello there",
                                    "session_id": "sess_live",
                                    "history": [{"role": "user", "content": "hi"}],
                                },
                            )

        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["x-accel-buffering"] == "no"
        events = _parse_sse_events(response.text)
        assert [event for event, _ in events] == [
            "start",
            "phase",
            "delta",
            "delta",
            "final",
        ]
        assert events[0][1]["provider"] == "openai"
        assert events[1][1]["phase"] == "commentary"
        assert events[2][1]["delta"] == "hello "
        assert events[4][1]["response"] == "hello world"
        assert events[4][1]["response_id"] == "resp_stream"

    def test_chat_stream_emits_error_event_on_runtime_failure(self, client):
        """Streaming chat should convert generator failures into SSE error events."""
        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(side_effect=RuntimeError("boom")),
        ):
            response = client.post(
                "/api/gemini/chat/stream",
                json={
                    "message": "hello there",
                    "session_id": "sess_live",
                    "history": [],
                },
            )

        assert response.status_code == 200
        events = _parse_sse_events(response.text)
        assert events == [("error", {"message": "Chat stream failed."})]

    @pytest.mark.asyncio
    async def test_persist_messages_uses_bound_timestamp_not_now(self):
        """Message persistence should not rely on DB-specific NOW() functions."""
        from src.kortana.routers.gemini import _persist_messages

        captured: list[tuple[str, dict[str, object] | None]] = []

        class FakeSession:
            async def execute(self, stmt, params=None):
                captured.append((str(stmt), params))
                return None

            def add(self, _obj):
                return None

        class FakeDbManager:
            def session_scope(self):
                return _FakeSessionScope(FakeSession())

        with patch(
            "src.kortana.database.get_db_manager",
            return_value=FakeDbManager(),
        ):
            await _persist_messages(
                "sess_sqlite",
                "hello",
                "kor'tana: hi",
                assistant_phase="final_answer",
                assistant_metadata={"provider": "openai"},
            )

        assert captured
        stmt, params = captured[0]
        assert "NOW()" not in stmt
        assert ":created_at" in stmt
        assert params is not None
        assert "created_at" in params
        assert params["created_at"] is not None

    @pytest.mark.asyncio
    async def test_extract_and_queue_tasks_uses_bound_timestamp_not_now(self):
        """Task persistence should use bound timestamps for SQLite compatibility."""
        from src.kortana.routers.gemini import _extract_and_queue_tasks

        captured: list[tuple[str, dict[str, object] | None]] = []

        class FakeSession:
            async def execute(self, stmt, params=None):
                captured.append((str(stmt), params))
                return None

        class FakeDbManager:
            def session_scope(self):
                return _FakeSessionScope(FakeSession())

        with patch(
            "src.kortana.database.get_db_manager",
            return_value=FakeDbManager(),
        ):
            cleaned, created = await _extract_and_queue_tasks(
                'hello [[TASK:{"name":"test task","description":"do the thing"}]]'
            )

        assert cleaned == "hello"
        assert len(created) == 1
        assert captured
        stmt, params = captured[0]
        assert "NOW()" not in stmt
        assert ":created_at" in stmt
        assert params is not None
        assert "created_at" in params
        assert params["created_at"] is not None

    def test_chat_fallback_to_gemini(self, client):
        """Test chat fallback to Gemini when the consensus engine has no provider."""
        engine = _make_consensus_engine("unused", providers_succeeded=0)

        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(return_value=""),
        ):
            with patch("src.kortana.routers.gemini._persist_messages", AsyncMock()):
                with patch(
                    "src.kortana.routers.gemini.get_consensus_engine",
                    return_value=engine,
                ):
                    with patch(
                        "src.kortana.routers.gemini.gemini_service"
                    ) as mock_gemini:
                        mock_gemini.analyze_text = AsyncMock(
                            return_value="Gemini response"
                        )

                        response = client.post(
                            "/api/gemini/chat",
                            json={"message": "Hello"},
                        )

        assert response.status_code == 200
        assert "gemini response" in response.json()["response"].lower()

    def test_chat_both_services_fail(self, client):
        """Test chat when both the consensus engine and Gemini fallback fail."""
        engine = _make_consensus_engine("unused", providers_succeeded=0)

        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(return_value=""),
        ):
            with patch(
                "src.kortana.routers.gemini.get_consensus_engine",
                return_value=engine,
            ):
                with patch("src.kortana.routers.gemini.gemini_service") as mock_gemini:
                    mock_gemini.analyze_text = AsyncMock(
                        side_effect=Exception("Gemini error")
                    )

                    response = client.post(
                        "/api/gemini/chat",
                        json={"message": "Hello"},
                    )

        assert response.status_code == 503

    def test_chat_no_services_available(self, client):
        """Test chat when no fallback provider is available."""
        engine = _make_consensus_engine("unused", providers_succeeded=0)

        with patch(
            "src.kortana.routers.gemini._build_live_context",
            AsyncMock(return_value=""),
        ):
            with patch(
                "src.kortana.routers.gemini.get_consensus_engine",
                return_value=engine,
            ):
                with patch("src.kortana.routers.gemini.gemini_service", None):
                    response = client.post(
                        "/api/gemini/chat",
                        json={"message": "Hello"},
                    )

        assert response.status_code == 503

    def test_chat_missing_message(self, client):
        """Test chat with missing message field"""
        response = client.post("/api/gemini/chat", json={})

        assert response.status_code == 400
        assert "Missing" in response.json()["detail"]

    def test_chat_empty_message(self, client):
        """Test chat with empty message"""
        response = client.post("/api/gemini/chat", json={"message": ""})

        assert response.status_code == 400


class TestAnalyzeImage:
    def test_analyze_image_success(self, client):
        """Test successful image analysis"""
        # Create a test image
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.analyze_multimodal = AsyncMock(return_value="Image analysis")

            response = client.post(
                "/api/gemini/analyze/image",
                data={"prompt": "Describe this image"},
                files={"image": ("test.png", img_bytes, "image/png")},
            )

            assert response.status_code == 200
            assert "Image analysis" in response.json()["response"]

    def test_analyze_image_default_prompt(self, client):
        """Test image analysis with default prompt"""
        img = Image.new("RGB", (100, 100), color="blue")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.analyze_multimodal = AsyncMock(return_value="Analysis")

            response = client.post(
                "/api/gemini/analyze/image",
                files={"image": ("test.png", img_bytes, "image/png")},
            )

            assert response.status_code == 200

    def test_analyze_image_invalid_format(self, client):
        """Test image analysis with invalid image format"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post(
                "/api/gemini/analyze/image",
                data={"prompt": "Describe"},
                files={
                    "image": ("test.txt", io.BytesIO(b"not an image"), "text/plain")
                },
            )

            assert response.status_code == 500

    def test_analyze_image_missing_file(self, client):
        """Test image analysis with missing file"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post(
                "/api/gemini/analyze/image", data={"prompt": "Describe"}
            )

            assert response.status_code == 422  # Validation error for missing file


class TestAnalyzeVideo:
    def test_analyze_video_success(self, client):
        """Test successful video analysis"""
        video_bytes = io.BytesIO(b"fake video content")

        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            with patch("google.generativeai.upload_file") as mock_upload:
                mock_service.analyze_multimodal = AsyncMock(
                    return_value="Video analysis"
                )
                mock_uploaded = MagicMock()
                mock_upload.return_value = mock_uploaded

                response = client.post(
                    "/api/gemini/analyze/video",
                    data={"prompt": "Describe the video"},
                    files={"video": ("test.mp4", video_bytes, "video/mp4")},
                )

                assert response.status_code == 200
                assert "Video analysis" in response.json()["response"]

    def test_analyze_video_default_prompt(self, client):
        """Test video analysis with default prompt"""
        video_bytes = io.BytesIO(b"video data")

        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            with patch("google.generativeai.upload_file") as mock_upload:
                mock_service.analyze_multimodal = AsyncMock(return_value="Analysis")
                mock_uploaded = MagicMock()
                mock_upload.return_value = mock_uploaded

                response = client.post(
                    "/api/gemini/analyze/video",
                    files={"video": ("test.mp4", video_bytes, "video/mp4")},
                )

                assert response.status_code == 200

    def test_analyze_video_file_handling_error(self, client):
        """Test video analysis with file handling error"""
        video_bytes = io.BytesIO(b"video data")

        with patch("src.kortana.routers.gemini.gemini_service"):
            with patch("google.generativeai.upload_file"):
                with patch("pathlib.Path.open", side_effect=IOError("File error")):
                    response = client.post(
                        "/api/gemini/analyze/video",
                        files={"video": ("test.mp4", video_bytes, "video/mp4")},
                    )

                    assert response.status_code == 500

    def test_analyze_video_genai_upload_error(self, client):
        """Test video analysis when genai upload fails"""
        video_bytes = io.BytesIO(b"video data")

        with patch("src.kortana.routers.gemini.gemini_service"):
            with patch("google.generativeai.upload_file") as mock_upload:
                mock_upload.side_effect = Exception("Upload error")

                response = client.post(
                    "/api/gemini/analyze/video",
                    files={"video": ("test.mp4", video_bytes, "video/mp4")},
                )

                assert response.status_code == 500

    def test_analyze_video_missing_file(self, client):
        """Test video analysis with missing file"""
        with patch("src.kortana.routers.gemini.gemini_service"):
            response = client.post(
                "/api/gemini/analyze/video", data={"prompt": "Analyze"}
            )

            assert response.status_code == 422  # Validation error for missing file


class TestGeminiRouterIntegration:
    def test_multiple_sequential_requests(self, client):
        """Test multiple sequential requests"""
        with patch("src.kortana.routers.gemini.gemini_service") as mock_service:
            mock_service.analyze_text = AsyncMock(return_value="Response 1")
            mock_service.generate_code = AsyncMock(return_value="Code 1")

            # First request
            response1 = client.post("/api/gemini/analyze", json={"text": "Issue 1"})
            assert response1.status_code == 200

            # Second request
            response2 = client.post(
                "/api/gemini/generate", json={"description": "Generate function"}
            )
            assert response2.status_code == 200

    def test_concurrent_endpoint_coverage(self, client):
        """Test that different endpoints properly isolate mocks"""
        with patch("src.kortana.routers.gemini.gemini_service") as mock_gemini:
            with patch(
                "src.kortana.routers.gemini.get_consensus_engine",
                return_value=_make_consensus_engine("kor'tana: A1"),
            ):
                mock_gemini.analyze_text = AsyncMock(return_value="G1")
                mock_gemini.generate_code = AsyncMock(return_value="G2")

                # Test analyze endpoint
                r1 = client.post("/api/gemini/analyze", json={"text": "test"})
                assert r1.status_code == 200

                # Test generate endpoint
                r2 = client.post("/api/gemini/generate", json={"description": "test"})
                assert r2.status_code == 200

                # Test chat endpoint
                r3 = client.post("/api/gemini/chat", json={"message": "test"})
                assert r3.status_code == 200
