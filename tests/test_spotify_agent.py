"""
Unit tests for Spotify Agent

Tests the Spotify agent implementation including configuration,
setup, query processing, and capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pydantic import ValidationError

from src.kortana.external_services.spotify import SpotifyAgent, SpotifyAgentConfig


class TestSpotifyAgentConfig:
    """Tests for SpotifyAgentConfig"""
    
    def test_config_creation_with_required_fields(self):
        """Test creating config with required fields"""
        config = SpotifyAgentConfig(
            llm_api_key="test-llm-key",
            spotify_api_key="test-spotify-key"
        )
        
        assert config.llm_api_key == "test-llm-key"
        assert config.spotify_api_key == "test-spotify-key"
        assert config.model_choice == "gpt-4o-mini"  # Default value
        assert config.market == "US"  # Default value
    
    def test_config_with_custom_values(self):
        """Test creating config with custom values"""
        config = SpotifyAgentConfig(
            llm_api_key="test-llm-key",
            spotify_api_key="test-spotify-key",
            model_choice="gpt-4",
            market="GB",
            log_level="DEBUG"
        )
        
        assert config.model_choice == "gpt-4"
        assert config.market == "GB"
        assert config.log_level == "DEBUG"
    
    def test_config_missing_required_fields(self):
        """Test that missing required fields raises validation error"""
        with pytest.raises(ValidationError):
            SpotifyAgentConfig(llm_api_key="test-key")
        
        with pytest.raises(ValidationError):
            SpotifyAgentConfig(spotify_api_key="test-key")


class TestSpotifyAgent:
    """Tests for SpotifyAgent"""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing"""
        return SpotifyAgentConfig(
            llm_api_key="test-llm-key",
            spotify_api_key="test-spotify-key",
            log_level="ERROR"  # Suppress logs during tests
        )
    
    @pytest.fixture
    def agent(self, mock_config):
        """Create a Spotify agent instance"""
        return SpotifyAgent(mock_config)
    
    def test_agent_initialization(self, agent, mock_config):
        """Test agent initialization"""
        assert agent.config == mock_config
        assert agent.agent is None
        assert agent.mcp_server is None
        assert agent.logger is not None
    
    def test_system_prompt_defined(self, agent):
        """Test that system prompt is defined"""
        assert agent.SYSTEM_PROMPT is not None
        assert "Spotify" in agent.SYSTEM_PROMPT
        assert "search" in agent.SYSTEM_PROMPT.lower()
    
    def test_get_capabilities(self, agent):
        """Test getting agent capabilities"""
        capabilities = agent.get_capabilities()
        
        assert capabilities["service"] == "spotify"
        assert "description" in capabilities
        assert "categories" in capabilities
        assert "requirements" in capabilities
        
        # Check categories
        category_names = [cat["name"] for cat in capabilities["categories"]]
        assert "Search" in category_names
        assert "Playlists" in category_names
        assert "Playback" in category_names
        assert "User Library" in category_names
    
    @pytest.mark.asyncio
    async def test_setup_agent(self, agent):
        """Test agent setup with mocked MCP server"""
        with patch('src.kortana.external_services.spotify.agent.MCPServerStdio') as mock_mcp:
            with patch.object(agent, '_get_model') as mock_model:
                with patch('src.kortana.external_services.spotify.agent.Agent') as mock_agent_class:
                    # Setup mocks
                    mock_server = MagicMock()
                    mock_mcp.return_value = mock_server
                    
                    mock_ai_agent = MagicMock()
                    mock_agent_class.return_value = mock_ai_agent
                    
                    # Run setup
                    await agent.setup()
                    
                    # Verify setup was called correctly
                    assert agent.mcp_server is not None
                    assert agent.agent is not None
                    mock_mcp.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_query_without_setup(self, agent):
        """Test that processing query without setup raises error"""
        with pytest.raises(RuntimeError, match="Agent not initialized"):
            await agent.process_query("test query")
    
    @pytest.mark.asyncio
    async def test_process_query_success(self, agent):
        """Test successful query processing"""
        # Setup mock agent
        mock_result = MagicMock()
        mock_result.data = "Spotify query result"
        
        agent.agent = AsyncMock()
        agent.agent.run = AsyncMock(return_value=mock_result)
        
        # Process query
        result = await agent.process_query("find songs by artist")
        
        # Verify result
        assert "result" in result
        assert "elapsed_time" in result
        assert "metadata" in result
        assert result["result"] == "Spotify query result"
        assert result["elapsed_time"] >= 0
    
    @pytest.mark.asyncio
    async def test_cleanup(self, agent):
        """Test agent cleanup"""
        agent.mcp_server = MagicMock()
        
        await agent.cleanup()
        
        assert agent.mcp_server is None


class TestSpotifyAgentIntegration:
    """Integration tests for Spotify agent (mocked)"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_query_flow(self):
        """Test complete query flow from setup to cleanup"""
        config = SpotifyAgentConfig(
            llm_api_key="test-llm-key",
            spotify_api_key="test-spotify-key",
            log_level="ERROR"
        )
        
        agent = SpotifyAgent(config)
        
        # Mock the entire flow
        with patch.object(agent, 'setup') as mock_setup:
            with patch.object(agent, 'process_query') as mock_query:
                with patch.object(agent, 'cleanup') as mock_cleanup:
                    mock_setup.return_value = None
                    mock_query.return_value = {
                        "result": "Test result",
                        "elapsed_time": 0.5,
                        "metadata": {}
                    }
                    mock_cleanup.return_value = None
                    
                    # Run flow
                    await agent.setup()
                    result = await agent.process_query("test")
                    await agent.cleanup()
                    
                    # Verify
                    mock_setup.assert_called_once()
                    mock_query.assert_called_once()
                    mock_cleanup.assert_called_once()
                    assert result["result"] == "Test result"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
