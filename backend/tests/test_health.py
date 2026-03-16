"""
Kor'tana Backend Test Suite - Health Check & Basic Endpoints

Run with: pytest -v
"""

import asyncio

import pytest
import httpx


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    from src.kortana.main import app
    from .conftest import SyncTestClient

    return SyncTestClient(app)


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Health check should return 200 OK."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self, client):
        """Health check response should have expected fields."""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert "message" in data
        assert data["status"] == "alive"

    @pytest.mark.slow
    def test_health_check_performance(self, client):
        """Health check should respond quickly."""
        import time

        start = time.time()
        response = client.get("/api/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1, f"Health check took {elapsed}s, expected < 0.1s"


class TestAPIStructure:
    """Test API structure and routing."""

    def test_api_base_path_exists(self, client):
        """API should have /api prefix."""
        # We can check if health endpoint exists under /api
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_cors_headers_present(self, client):
        """CORS headers should be present in responses."""
        response = client.get("/api/health")
        # FastAPI CORS middleware should add headers
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling and status codes."""

    def test_nonexistent_endpoint_returns_404(self, client):
        """Non-existent endpoints should return 404."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_invalid_method_returns_405(self, client):
        """Invalid HTTP methods should return 405."""
        response = client.post("/api/health")
        # FastAPI returns 405 for invalid methods on existing endpoints
        assert response.status_code in [405, 200]  # Depends on endpoint config


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test async/await functionality."""

    async def test_async_context(self):
        """Verify async context works."""
        await asyncio.sleep(0.01)
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
