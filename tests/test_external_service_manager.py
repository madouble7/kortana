"""
Unit tests for External Service Manager

Tests the service manager's ability to register, manage, and route
requests to multiple external service agents.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.kortana.external_services.base.service_manager import (
    ExternalServiceManager,
    ServiceType
)
from src.kortana.external_services.base.agent_base import BaseExternalAgent


class MockAgent(BaseExternalAgent):
    """Mock agent for testing"""
    
    async def setup(self):
        self.agent = MagicMock()
    
    async def process_query(self, query: str):
        return {
            "result": f"Mock result for: {query}",
            "elapsed_time": 0.1,
            "metadata": {}
        }
    
    def get_capabilities(self):
        return {
            "service": "mock",
            "description": "Mock service for testing"
        }


class TestServiceType:
    """Tests for ServiceType enum"""
    
    def test_service_types_exist(self):
        """Test that expected service types are defined"""
        assert ServiceType.SPOTIFY == "spotify"
        assert ServiceType.GITHUB == "github"
    
    def test_service_type_is_string(self):
        """Test that service types can be used as strings"""
        assert isinstance(ServiceType.SPOTIFY.value, str)
        assert isinstance(ServiceType.GITHUB.value, str)


class TestExternalServiceManager:
    """Tests for ExternalServiceManager"""
    
    @pytest.fixture
    def manager(self):
        """Create a service manager instance"""
        return ExternalServiceManager()
    
    @pytest.fixture
    def mock_spotify_agent(self):
        """Create a mock Spotify agent"""
        from src.kortana.external_services.base.agent_base import AgentConfig
        config = AgentConfig(llm_api_key="test-key")
        agent = MockAgent(config)
        agent.service_name = "spotify"
        return agent
    
    @pytest.fixture
    def mock_github_agent(self):
        """Create a mock GitHub agent"""
        from src.kortana.external_services.base.agent_base import AgentConfig
        config = AgentConfig(llm_api_key="test-key")
        agent = MockAgent(config)
        agent.service_name = "github"
        return agent
    
    def test_manager_initialization(self, manager):
        """Test service manager initialization"""
        assert manager._services == {}
        assert manager._initialized == False
        assert manager.logger is not None
    
    @pytest.mark.asyncio
    async def test_register_service(self, manager, mock_spotify_agent):
        """Test registering a service"""
        await manager.register_service(ServiceType.SPOTIFY, mock_spotify_agent)
        
        assert ServiceType.SPOTIFY in manager._services
        assert manager._services[ServiceType.SPOTIFY] == mock_spotify_agent
    
    @pytest.mark.asyncio
    async def test_register_multiple_services(self, manager, mock_spotify_agent, mock_github_agent):
        """Test registering multiple services"""
        await manager.register_service(ServiceType.SPOTIFY, mock_spotify_agent)
        await manager.register_service(ServiceType.GITHUB, mock_github_agent)
        
        assert len(manager._services) == 2
        assert ServiceType.SPOTIFY in manager._services
        assert ServiceType.GITHUB in manager._services
    
    def test_get_service(self, manager, mock_spotify_agent):
        """Test getting a registered service"""
        manager._services[ServiceType.SPOTIFY] = mock_spotify_agent
        
        agent = manager.get_service(ServiceType.SPOTIFY)
        assert agent == mock_spotify_agent
    
    def test_get_nonexistent_service(self, manager):
        """Test getting a service that doesn't exist"""
        agent = manager.get_service(ServiceType.SPOTIFY)
        assert agent is None
    
    def test_list_services_empty(self, manager):
        """Test listing services when none registered"""
        services = manager.list_services()
        assert services == []
    
    def test_list_services_with_registered(self, manager, mock_spotify_agent):
        """Test listing services when some are registered"""
        manager._services[ServiceType.SPOTIFY] = mock_spotify_agent
        
        services = manager.list_services()
        assert len(services) == 1
        assert ServiceType.SPOTIFY in services
    
    @pytest.mark.asyncio
    async def test_query_service(self, manager, mock_spotify_agent):
        """Test querying a registered service"""
        await manager.register_service(ServiceType.SPOTIFY, mock_spotify_agent)
        
        result = await manager.query_service(ServiceType.SPOTIFY, "test query")
        
        assert result["service"] == "spotify"
        assert result["success"] == True
        assert "result" in result
        assert "elapsed_time" in result
    
    @pytest.mark.asyncio
    async def test_query_nonexistent_service(self, manager):
        """Test querying a service that doesn't exist"""
        with pytest.raises(ValueError, match="not registered"):
            await manager.query_service(ServiceType.SPOTIFY, "test query")
    
    @pytest.mark.asyncio
    async def test_query_service_error_handling(self, manager, mock_spotify_agent):
        """Test error handling when query fails"""
        # Make the agent raise an error
        mock_spotify_agent.process_query = AsyncMock(side_effect=Exception("Test error"))
        
        await manager.register_service(ServiceType.SPOTIFY, mock_spotify_agent)
        
        result = await manager.query_service(ServiceType.SPOTIFY, "test query")
        
        assert result["service"] == "spotify"
        assert result["success"] == False
        assert "error" in result
        assert "Test error" in result["error"]
    
    def test_get_service_capabilities(self, manager, mock_spotify_agent):
        """Test getting capabilities of a service"""
        manager._services[ServiceType.SPOTIFY] = mock_spotify_agent
        
        capabilities = manager.get_service_capabilities(ServiceType.SPOTIFY)
        
        assert capabilities["service"] == "mock"
        assert "description" in capabilities
    
    def test_get_service_capabilities_nonexistent(self, manager):
        """Test getting capabilities of nonexistent service"""
        with pytest.raises(ValueError, match="not registered"):
            manager.get_service_capabilities(ServiceType.SPOTIFY)
    
    def test_get_all_capabilities_empty(self, manager):
        """Test getting all capabilities when no services registered"""
        capabilities = manager.get_all_capabilities()
        assert capabilities == {}
    
    def test_get_all_capabilities(self, manager, mock_spotify_agent, mock_github_agent):
        """Test getting all capabilities with registered services"""
        manager._services[ServiceType.SPOTIFY] = mock_spotify_agent
        manager._services[ServiceType.GITHUB] = mock_github_agent
        
        capabilities = manager.get_all_capabilities()
        
        assert len(capabilities) == 2
        assert "spotify" in capabilities
        assert "github" in capabilities
    
    @pytest.mark.asyncio
    async def test_cleanup(self, manager, mock_spotify_agent, mock_github_agent):
        """Test cleanup of all services"""
        mock_spotify_agent.cleanup = AsyncMock()
        mock_github_agent.cleanup = AsyncMock()
        
        await manager.register_service(ServiceType.SPOTIFY, mock_spotify_agent)
        await manager.register_service(ServiceType.GITHUB, mock_github_agent)
        
        await manager.cleanup()
        
        mock_spotify_agent.cleanup.assert_called_once()
        mock_github_agent.cleanup.assert_called_once()
        assert manager._services == {}
        assert manager._initialized == False
    
    @pytest.mark.asyncio
    async def test_cleanup_with_error(self, manager, mock_spotify_agent):
        """Test cleanup handles errors gracefully"""
        mock_spotify_agent.cleanup = AsyncMock(side_effect=Exception("Cleanup error"))
        
        await manager.register_service(ServiceType.SPOTIFY, mock_spotify_agent)
        
        # Should not raise exception
        await manager.cleanup()
        
        # Services should still be cleared
        assert manager._services == {}


class TestServiceManagerIntegration:
    """Integration tests for service manager"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete workflow: register, query, cleanup"""
        from src.kortana.external_services.base.agent_base import AgentConfig
        
        # Create manager and mock agents
        manager = ExternalServiceManager()
        
        spotify_agent = MockAgent(AgentConfig(llm_api_key="test-key"))
        github_agent = MockAgent(AgentConfig(llm_api_key="test-key"))
        
        # Register services
        await manager.register_service(ServiceType.SPOTIFY, spotify_agent)
        await manager.register_service(ServiceType.GITHUB, github_agent)
        
        # Verify registration
        assert len(manager.list_services()) == 2
        
        # Query services
        spotify_result = await manager.query_service(ServiceType.SPOTIFY, "find songs")
        github_result = await manager.query_service(ServiceType.GITHUB, "list repos")
        
        assert spotify_result["success"] == True
        assert github_result["success"] == True
        
        # Get capabilities
        all_caps = manager.get_all_capabilities()
        assert len(all_caps) == 2
        
        # Cleanup
        await manager.cleanup()
        assert len(manager.list_services()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
