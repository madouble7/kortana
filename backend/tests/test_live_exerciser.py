"""
Tests for the Live Exerciser router.
Unit tests use mocked externals; the router is tested via SyncTestClient.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.kortana.main import app
from src.kortana.routers.live_exerciser import (
    SYSTEM_AGENT_ID,
    SYSTEM_USER_ID,
    _ensure_bootstrap,
)
from tests.conftest import SyncTestClient

# ------------------------------------------------------------------
# Test client for integration tests
# ------------------------------------------------------------------
sync_client = SyncTestClient(app)


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
    def test_quick_status_endpoint(self):
        """GET /api/live/status should return checks dict."""
        resp = sync_client.get("/api/live/status")
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
        assert "github_token" in checks

    def test_exercise_endpoint_returns_results(self):
        """POST /api/live/exercise should return results for all services."""
        resp = sync_client.post("/api/live/exercise")
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "postgresql" in data
        assert "redis" in data
        assert "gemini_embedding" in data
        assert "gemini_generate" in data
        assert "groq" in data
        assert "github" in data
        assert "memory_store" in data
        # Summary should have counts
        summary = data["summary"]
        assert "services_ok" in summary
        assert "services_total" in summary
        assert "total_ms" in summary
        assert "model_usage_lane" in summary
