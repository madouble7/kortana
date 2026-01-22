"""
Unit tests for GitHub Agent

Tests the GitHub agent implementation including configuration,
setup, query processing, and capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pydantic import ValidationError

from src.kortana.external_services.github import GitHubAgent, GitHubAgentConfig, GitHubDeps


class TestGitHubAgentConfig:
    """Tests for GitHubAgentConfig"""
    
    def test_config_creation_with_required_fields(self):
        """Test creating config with required fields"""
        config = GitHubAgentConfig(
            llm_api_key="test-llm-key",
            github_token="test-github-token"
        )
        
        assert config.llm_api_key == "test-llm-key"
        assert config.github_token == "test-github-token"
        assert config.model_choice == "gpt-4o-mini"  # Default value
    
    def test_config_with_custom_values(self):
        """Test creating config with custom values"""
        config = GitHubAgentConfig(
            llm_api_key="test-llm-key",
            github_token="test-github-token",
            model_choice="gpt-4",
            log_level="DEBUG",
            timeout=60
        )
        
        assert config.model_choice == "gpt-4"
        assert config.log_level == "DEBUG"
        assert config.timeout == 60
    
    def test_config_missing_required_fields(self):
        """Test that missing required fields raises validation error"""
        with pytest.raises(ValidationError):
            GitHubAgentConfig(llm_api_key="test-key")
        
        with pytest.raises(ValidationError):
            GitHubAgentConfig(github_token="test-token")


class TestGitHubAgent:
    """Tests for GitHubAgent"""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing"""
        return GitHubAgentConfig(
            llm_api_key="test-llm-key",
            github_token="test-github-token",
            log_level="ERROR"  # Suppress logs during tests
        )
    
    @pytest.fixture
    def agent(self, mock_config):
        """Create a GitHub agent instance"""
        return GitHubAgent(mock_config)
    
    def test_agent_initialization(self, agent, mock_config):
        """Test agent initialization"""
        assert agent.config == mock_config
        assert agent.agent is None
        assert agent.mcp_server is None
        assert agent.http_client is None
        assert agent.logger is not None
    
    def test_system_prompt_defined(self, agent):
        """Test that system prompt is defined"""
        assert agent.SYSTEM_PROMPT is not None
        assert "GitHub" in agent.SYSTEM_PROMPT
        assert "repository" in agent.SYSTEM_PROMPT.lower()
    
    def test_get_capabilities(self, agent):
        """Test getting agent capabilities"""
        capabilities = agent.get_capabilities()
        
        assert capabilities["service"] == "github"
        assert "description" in capabilities
        assert "categories" in capabilities
        assert "requirements" in capabilities
        
        # Check categories
        category_names = [cat["name"] for cat in capabilities["categories"]]
        assert "Repositories" in category_names
        assert "Issues" in category_names
        assert "Pull Requests" in category_names
        assert "Users & Organizations" in category_names
    
    @pytest.mark.asyncio
    async def test_setup_agent(self, agent):
        """Test agent setup with mocked MCP server"""
        with patch('src.kortana.external_services.github.agent.MCPServerStdio') as mock_mcp:
            with patch('src.kortana.external_services.github.agent.httpx.AsyncClient') as mock_client:
                with patch.object(agent, '_get_model') as mock_model:
                    with patch('src.kortana.external_services.github.agent.Agent') as mock_agent_class:
                        # Setup mocks
                        mock_server = MagicMock()
                        mock_mcp.return_value = mock_server
                        
                        mock_http_client = MagicMock()
                        mock_client.return_value = mock_http_client
                        
                        mock_ai_agent = MagicMock()
                        mock_agent_class.return_value = mock_ai_agent
                        
                        # Run setup
                        await agent.setup()
                        
                        # Verify setup was called correctly
                        assert agent.mcp_server is not None
                        assert agent.agent is not None
                        assert agent.http_client is not None
    
    @pytest.mark.asyncio
    async def test_process_query_without_setup(self, agent):
        """Test that processing query without setup raises error"""
        with pytest.raises(RuntimeError, match="Agent not initialized"):
            await agent.process_query("test query")
    
    @pytest.mark.asyncio
    async def test_process_query_success(self, agent):
        """Test successful query processing"""
        # Setup mock agent and client
        mock_result = MagicMock()
        mock_result.data = "GitHub query result"
        
        agent.agent = AsyncMock()
        agent.agent.run = AsyncMock(return_value=mock_result)
        agent.http_client = MagicMock()
        
        # Process query
        result = await agent.process_query("get repo info")
        
        # Verify result
        assert "result" in result
        assert "elapsed_time" in result
        assert "metadata" in result
        assert result["result"] == "GitHub query result"
        assert result["elapsed_time"] >= 0
    
    @pytest.mark.asyncio
    async def test_cleanup(self, agent):
        """Test agent cleanup"""
        agent.mcp_server = MagicMock()
        agent.http_client = AsyncMock()
        agent.http_client.aclose = AsyncMock()
        
        await agent.cleanup()
        
        assert agent.mcp_server is None
        assert agent.http_client is None


class TestGitHubDeps:
    """Tests for GitHubDeps dataclass"""
    
    def test_github_deps_creation(self):
        """Test creating GitHubDeps instance"""
        client = MagicMock()
        deps = GitHubDeps(client=client, github_token="test-token")
        
        assert deps.client == client
        assert deps.github_token == "test-token"
    
    def test_github_deps_optional_token(self):
        """Test GitHubDeps with optional token"""
        client = MagicMock()
        deps = GitHubDeps(client=client)
        
        assert deps.client == client
        assert deps.github_token is None


class TestGitHubAgentIntegration:
    """Integration tests for GitHub agent (mocked)"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_query_flow(self):
        """Test complete query flow from setup to cleanup"""
        config = GitHubAgentConfig(
            llm_api_key="test-llm-key",
            github_token="test-github-token",
            log_level="ERROR"
        )
        
        agent = GitHubAgent(config)
        
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
