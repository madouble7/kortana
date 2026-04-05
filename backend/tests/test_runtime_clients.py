"""Runtime-focused tests for provider and HTTP client wiring."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.kortana.api_integration import (
    ClaudeAPIClient,
    GeminiAPIClient,
    GroqAPIClient,
    OpenAIAPIClient,
)
from src.kortana.config import get_settings
from src.kortana.provider_model_defaults import (
    AI_CONSENSUS_DEFAULTS,
    API_INTEGRATION_FALLBACK_DEFAULTS,
)


class TestAIConsensusRuntime:
    def test_openai_init_uses_explicit_httpx_client(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
        monkeypatch.setenv("KORTANA_CORE_MODELS", AI_CONSENSUS_DEFAULTS.openai)
        monkeypatch.delenv("KORTANA_EXPERIMENTAL_MODELS", raising=False)
        monkeypatch.delenv("KORTANA_QUARANTINE_MODELS", raising=False)
        get_settings.cache_clear()

        mock_openai = MagicMock()
        with patch.dict("sys.modules", {"openai": mock_openai}):
            from src.kortana.services.ai_consensus import AIConsensusEngine

            engine = AIConsensusEngine()
            engine._try_openai()

        kwargs = mock_openai.AsyncOpenAI.call_args.kwargs
        assert kwargs["api_key"] == "sk-test"
        assert isinstance(kwargs["http_client"], httpx.AsyncClient)
        assert engine._providers["openai"]["model"] == AI_CONSENSUS_DEFAULTS.openai
        asyncio.run(kwargs["http_client"].aclose())

    def test_openrouter_init_uses_explicit_httpx_client(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")

        mock_openai = MagicMock()
        with patch.dict("sys.modules", {"openai": mock_openai}):
            from src.kortana.services.ai_consensus import AIConsensusEngine

            engine = AIConsensusEngine()
            engine._try_openrouter()

        kwargs = mock_openai.AsyncOpenAI.call_args.kwargs
        assert kwargs["api_key"] == "or-test"
        assert kwargs["base_url"] == "https://openrouter.ai/api/v1"
        assert isinstance(kwargs["http_client"], httpx.AsyncClient)
        assert (
            engine._providers["openrouter"]["model"]
            == AI_CONSENSUS_DEFAULTS.openrouter
        )
        asyncio.run(kwargs["http_client"].aclose())

    @pytest.mark.asyncio
    async def test_consensus_provider_records_estimated_token_usage(self) -> None:
        from src.kortana.services.ai_consensus import AIConsensusEngine, ProviderStats

        engine = AIConsensusEngine()
        engine._providers["openai"] = {"model": AI_CONSENSUS_DEFAULTS.openai}
        engine._stats["openai"] = ProviderStats()

        with patch.object(
            engine,
            "_dispatch",
            AsyncMock(return_value="threaded reply"),
        ), patch(
            "src.kortana.services.ai_consensus.get_model_usage_telemetry"
        ) as mock_telemetry:
            telemetry = mock_telemetry.return_value
            response = await engine._call_provider(
                "openai",
                "hello there",
                "system guidance",
                128,
                selection="parallel_query",
            )

        assert response.success is True
        telemetry.record_generation.assert_called_once()
        kwargs = telemetry.record_generation.call_args.kwargs
        assert kwargs["provider"] == "openai"
        assert kwargs["tokens_used"] > 0


class TestResilientHttpClientRuntime:
    def test_get_http_client_uses_configured_redis_url(self):
        import src.kortana.http_client as http_client_module

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_settings = MagicMock()
        mock_settings.INTERNAL_REDIS_URL = "redis://redis:6379/0"

        http_client_module._http_client = None
        try:
            with (
                patch("src.kortana.http_client.get_settings", return_value=mock_settings),
                patch("redis.Redis.from_url", return_value=mock_redis_client) as mock_from_url,
            ):
                client = http_client_module.get_http_client()

            assert client is not None
            mock_from_url.assert_called_once_with(
                "redis://redis:6379/0",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
        finally:
            http_client_module._http_client = None


class TestGitRuntimeWiring:
    def test_github_autonomy_uses_safe_directory_for_git_commands(self, tmp_path):
        from src.kortana.services.github_autonomy_service import GitHubAutonomyService

        with (
            patch(
                "src.kortana.services.github_autonomy_service.get_http_client",
                return_value=MagicMock(),
            ),
            patch(
                "src.kortana.services.github_autonomy_service.subprocess.run"
            ) as mock_run,
        ):
            mock_run.return_value = MagicMock(stdout="ok\n")
            service = GitHubAutonomyService(MagicMock())
            service.repo_root = tmp_path.resolve()

            output = service._git_output(["git", "ls-files"])

        assert output == "ok"
        mock_run.assert_called_once()
        assert mock_run.call_args.args[0] == [
            "git",
            "-c",
            f"safe.directory={service.repo_root}",
            "ls-files",
        ]


class TestAPIIntegrationModelLaneRuntime:
    def test_direct_clients_fall_back_from_quarantined_models(self, monkeypatch):
        monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
        get_settings.cache_clear()

        groq_client = GroqAPIClient("groq-test", "ft:rogue-groq")
        claude_client = ClaudeAPIClient("anthropic-test", "ft:rogue-claude")
        openai_client = OpenAIAPIClient("sk-test", "ft:rogue-openai")

        assert groq_client.model == API_INTEGRATION_FALLBACK_DEFAULTS.groq
        assert claude_client.model == API_INTEGRATION_FALLBACK_DEFAULTS.anthropic
        assert openai_client.model == API_INTEGRATION_FALLBACK_DEFAULTS.openai

    def test_gemini_client_uses_lane_aware_helpers(self, monkeypatch):
        monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
        get_settings.cache_clear()

        with (
            patch(
                "src.kortana.api_integration.get_model_name",
                return_value="gemini-2.0-flash",
            ),
            patch(
                "src.kortana.api_integration.get_preferred_model_name",
                return_value="gemini-2.5-flash",
            ),
        ):
            default_client = GeminiAPIClient("gm-test")
            preferred_client = GeminiAPIClient("gm-test", "gemini-1.5-pro")

        assert default_client.model == "gemini-2.0-flash"
        assert preferred_client.model == "gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_openai_client_uses_responses_api_for_gpt5_models(self) -> None:
        mock_async_openai = MagicMock()
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_client.responses.create = AsyncMock(
            return_value=MagicMock(
                output_text="OpenAI responses output",
                usage=MagicMock(input_tokens=8, output_tokens=5),
            )
        )
        mock_async_openai.return_value = mock_client

        with patch.dict("sys.modules", {"openai": MagicMock(AsyncOpenAI=mock_async_openai)}):
            client = OpenAIAPIClient("sk-test")
            text, input_tokens, output_tokens = await client.generate("Hello world")

        assert text == "OpenAI responses output"
        assert input_tokens == 8
        assert output_tokens == 5
        mock_client.responses.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_openai_helper_passes_previous_response_id_for_gpt5_models(
        self,
    ) -> None:
        from src.kortana.openai_responses import async_generate_turn

        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(
            return_value=MagicMock(
                id="resp_new",
                output_text="Threaded OpenAI output",
                usage=MagicMock(input_tokens=13, output_tokens=7),
            )
        )

        result = await async_generate_turn(
            mock_client,
            model_name=AI_CONSENSUS_DEFAULTS.openai,
            prompt="continue",
            previous_response_id="resp_prev",
            timeout=30.0,
        )

        kwargs = mock_client.responses.create.await_args.kwargs
        assert kwargs["previous_response_id"] == "resp_prev"
        assert result.text == "Threaded OpenAI output"
        assert result.response_id == "resp_new"

    @pytest.mark.asyncio
    async def test_openai_helper_replays_assistant_phase_in_history(self) -> None:
        from src.kortana.openai_responses import async_generate_turn

        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(
            return_value=MagicMock(
                id="resp_hist",
                output=[
                    MagicMock(role="assistant", phase="final_answer"),
                ],
                output_text="Phase aware output",
                usage=MagicMock(input_tokens=4, output_tokens=6),
            )
        )

        result = await async_generate_turn(
            mock_client,
            model_name=AI_CONSENSUS_DEFAULTS.openai,
            prompt="what next?",
            history=[
                {"role": "user", "content": "hello"},
                {
                    "role": "assistant",
                    "content": "kor'tana: i am here.",
                    "phase": "commentary",
                },
            ],
        )

        input_payload = mock_client.responses.create.await_args.kwargs["input"]
        assert input_payload[1]["phase"] == "commentary"
        assert result.phase == "final_answer"

    @pytest.mark.asyncio
    async def test_openai_helper_streams_gpt5_text_deltas(self) -> None:
        from src.kortana.openai_responses import (
            OpenAITextGenerationResult,
            async_stream_turn,
        )

        class _FakeStream:
            def __init__(self, events, final_response):
                self._events = list(events)
                self._final_response = final_response

            def __aiter__(self):
                self._index = 0
                return self

            async def __anext__(self):
                if self._index >= len(self._events):
                    raise StopAsyncIteration
                item = self._events[self._index]
                self._index += 1
                return item

            async def get_final_response(self):
                return self._final_response

        class _FakeManager:
            def __init__(self, stream):
                self._stream = stream

            async def __aenter__(self):
                return self._stream

            async def __aexit__(self, exc_type, exc, tb):
                return None

        final_response = MagicMock(
            id="resp_stream",
            output=[MagicMock(role="assistant", phase="final_answer")],
            output_text="kor'tana: streamed reply",
            usage=MagicMock(input_tokens=9, output_tokens=4),
        )
        fake_stream = _FakeStream(
            [
                MagicMock(type="response.output_text.delta", delta="kor'tana: "),
                MagicMock(type="response.output_text.delta", delta="streamed "),
                MagicMock(type="response.output_text.delta", delta="reply"),
            ],
            final_response,
        )
        mock_client = MagicMock()
        mock_client.responses.stream = MagicMock(return_value=_FakeManager(fake_stream))

        events = [
            event
            async for event in async_stream_turn(
                mock_client,
                model_name=AI_CONSENSUS_DEFAULTS.openai,
                prompt="hello",
            )
        ]

        assert events[:3] == [
            {"type": "delta", "delta": "kor'tana: "},
            {"type": "delta", "delta": "streamed "},
            {"type": "delta", "delta": "reply"},
        ]
        completed = events[-1]
        assert completed["type"] == "completed"
        assert isinstance(completed["result"], OpenAITextGenerationResult)
        assert completed["result"].text == "kor'tana: streamed reply"
        assert completed["result"].response_id == "resp_stream"
