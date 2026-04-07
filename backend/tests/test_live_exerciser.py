"""
Tests for the Live Exerciser router.
Unit tests use mocked externals; the router is tested via SyncTestClient.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.kortana.routers.live_exerciser import (
    SYSTEM_AGENT_ID,
    SYSTEM_USER_ID,
    _ensure_bootstrap,
    _exercise_openai,
)


# ------------------------------------------------------------------
# Bootstrap tests
# ------------------------------------------------------------------
class TestBootstrap:
    @pytest.mark.asyncio
    async def test_ensure_bootstrap_creates_user_and_agent(self):
        """Bootstrap should create system user and agent rows."""
        mock_db = AsyncMock()
        # Simulate empty DB: no user, no agent
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.first.return_value = None
        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        result = await _ensure_bootstrap(mock_db)
        assert result["user_id"] == SYSTEM_USER_ID
        assert result["agent_id"] == SYSTEM_AGENT_ID
        assert mock_db.add.call_count == 2  # user + agent
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ensure_bootstrap_idempotent(self):
        """Bootstrap should not recreate if rows exist."""
        mock_db = AsyncMock()
        existing = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = existing
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await _ensure_bootstrap(mock_db)
        assert result["user_id"] == SYSTEM_USER_ID
        mock_db.add.assert_not_called()


# ------------------------------------------------------------------
# Router endpoint tests (TestClient)
# ------------------------------------------------------------------
class TestLiveExerciserRouter:
    def test_quick_status_accepts_google_api_key_for_gemini(self, client, monkeypatch):
        """Gemini status should accept either GEMINI_API_KEY or GOOGLE_API_KEY."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_API_KEY", "gm-test")

        resp = client.get("/api/live/status")

        assert resp.status_code == 200
        assert resp.json()["checks"]["gemini_key"] == "ok"

    def test_quick_status_endpoint(self, client):
        """GET /api/live/status should return checks dict."""
        resp = client.get("/api/live/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "checks" in data
        assert "status" in data
        assert "model_usage_lane" in data
        assert "models" in data
        # Should have all key checks
        checks = data["checks"]
        assert "postgresql" in checks
        assert "redis" in checks
        assert "gemini_key" in checks
        assert "groq_key" in checks
        assert "openai_key" in checks
        assert "github_token" in checks

        models = data["models"]
        assert "openai_generate" in models

    def test_exercise_endpoint_returns_results(self, client):
        """POST /api/live/exercise should return results for all services."""
        resp = client.post("/api/live/exercise")
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "postgresql" in data
        assert "redis" in data
        assert "gemini_embedding" in data
        assert "gemini_generate" in data
        assert "groq" in data
        assert "openai" in data
        assert "github" in data
        assert "memory_store" in data
        # Summary should have counts
        summary = data["summary"]
        assert "services_ok" in summary
        assert "services_total" in summary
        assert "total_ms" in summary
        assert "model_usage_lane" in summary

    @pytest.mark.asyncio
    async def test_exercise_openai_returns_phase_and_response_id(self, monkeypatch):
        """OpenAI exercise should surface GPT-5 response metadata for diagnostics."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        mock_openai_module = MagicMock()
        mock_openai_module.OpenAI.return_value = MagicMock()

        with (
            patch.dict(sys.modules, {"openai": mock_openai_module}),
            patch(
                "src.kortana.routers.live_exerciser.sync_generate_turn",
                return_value=MagicMock(
                    text="lanes preserve reliability boundaries",
                    input_tokens=8,
                    output_tokens=5,
                    response_id="resp_live",
                    phase="final_answer",
                ),
            ),
        ):
            result = await _exercise_openai()

        assert result["status"] == "ok"
        assert result["response_id"] == "resp_live"
        assert result["phase"] == "final_answer"
