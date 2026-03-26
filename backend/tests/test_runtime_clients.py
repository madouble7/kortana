"""Runtime-focused tests for provider and HTTP client wiring."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import httpx


class TestAIConsensusRuntime:
    def test_openai_init_uses_explicit_httpx_client(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        mock_openai = MagicMock()
        with patch.dict("sys.modules", {"openai": mock_openai}):
            from src.kortana.services.ai_consensus import AIConsensusEngine

            engine = AIConsensusEngine()
            engine._try_openai()

        kwargs = mock_openai.AsyncOpenAI.call_args.kwargs
        assert kwargs["api_key"] == "sk-test"
        assert isinstance(kwargs["http_client"], httpx.AsyncClient)
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
        asyncio.run(kwargs["http_client"].aclose())


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
