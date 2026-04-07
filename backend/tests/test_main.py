"""
Tests for configuration and health endpoints
"""

import pytest


@pytest.mark.unit
class TestConfig:
    """Configuration tests"""

    def test_config_loads(self, test_settings):
        """Test that configuration loads"""
        assert test_settings.ENVIRONMENT is not None
        assert test_settings.DEBUG is not None
        assert test_settings.PORT > 0

    def test_config_has_required_keys(self, test_settings):
        """Test that config has required API keys"""
        # At least some keys should be configured
        assert (
            test_settings.OPENAI_API_KEY
            or test_settings.ANTHROPIC_API_KEY
            or test_settings.GEMINI_API_KEY
        ), "At least one LLM API key should be configured"

    def test_database_config(self, test_settings):
        """Test database configuration"""
        assert test_settings.DB_HOST is not None
        assert test_settings.DB_PORT > 0
        assert test_settings.DB_NAME is not None


@pytest.mark.unit
class TestHealth:
    """Health check endpoint tests"""

    def test_health_check_success(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"
        assert "environment" in data
        assert "version" in data

    def test_health_check_structure(self, client):
        """Test health check response structure"""
        response = client.get("/api/health")
        data = response.json()

        required_fields = ["status", "message", "environment", "version"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data

    def test_root_head_endpoint(self, client):
        """Test HEAD on root endpoint for platform health checks."""
        response = client.head("/")
        assert response.status_code == 200


@pytest.mark.unit
class TestCORS:
    """CORS configuration tests"""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present for preflight requests"""
        # Include Origin header to simulate real CORS preflight
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        }
        response = client.options("/api/health", headers=headers)
        # CORS preflight should succeed with proper headers
        assert response.status_code == 200

    def test_localhost_allowed(self, client):
        """Test that localhost origins are allowed"""
        headers = {"Origin": "http://localhost:3000"}
        response = client.get("/api/health", headers=headers)
        assert response.status_code == 200


@pytest.mark.unit
class TestSecurityHeaders:
    """Security headers tests"""

    def test_security_headers_present(self, client):
        """Test that security headers are present"""
        response = client.get("/api/health")

        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
        ]

        for header in security_headers:
            assert header in response.headers, f"Missing security header: {header}"

    def test_request_id_header(self, client):
        """Test that X-Request-ID is present"""
        response = client.get("/api/health")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API endpoints"""

    def test_multiple_requests_successful(self, client):
        """Test multiple sequential requests"""
        for _ in range(5):
            response = client.get("/api/health")
            assert response.status_code == 200

    def test_request_error_handling(self, client):
        """Test error handling"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
