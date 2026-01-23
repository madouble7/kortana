"""
Standalone test for external services

Simple test that can run without the full Kortana environment.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kortana.external_services.base.agent_base import AgentConfig, BaseExternalAgent
from src.kortana.external_services.base.service_manager import ExternalServiceManager, ServiceType


def test_agent_config():
    """Test AgentConfig creation"""
    config = AgentConfig(
        llm_api_key="test-key",
        model_choice="gpt-4o-mini",
        log_level="INFO"
    )
    assert config.llm_api_key == "test-key"
    assert config.model_choice == "gpt-4o-mini"
    print("✓ AgentConfig test passed")


def test_service_manager():
    """Test ExternalServiceManager"""
    manager = ExternalServiceManager()
    assert manager._services == {}
    assert len(manager.list_services()) == 0
    print("✓ ServiceManager test passed")


def test_service_types():
    """Test ServiceType enum"""
    assert ServiceType.SPOTIFY == "spotify"
    assert ServiceType.GITHUB == "github"
    print("✓ ServiceType test passed")


def test_spotify_config():
    """Test Spotify agent config"""
    from src.kortana.external_services.spotify import SpotifyAgentConfig
    
    config = SpotifyAgentConfig(
        llm_api_key="test-llm-key",
        spotify_api_key="test-spotify-key",
        market="US"
    )
    assert config.spotify_api_key == "test-spotify-key"
    assert config.market == "US"
    print("✓ SpotifyAgentConfig test passed")


def test_github_config():
    """Test GitHub agent config"""
    from src.kortana.external_services.github import GitHubAgentConfig
    
    config = GitHubAgentConfig(
        llm_api_key="test-llm-key",
        github_token="test-github-token"
    )
    assert config.github_token == "test-github-token"
    print("✓ GitHubAgentConfig test passed")


def test_spotify_agent_capabilities():
    """Test Spotify agent capabilities"""
    from src.kortana.external_services.spotify import SpotifyAgent, SpotifyAgentConfig
    
    config = SpotifyAgentConfig(
        llm_api_key="test-key",
        spotify_api_key="test-key",
        log_level="ERROR"
    )
    agent = SpotifyAgent(config)
    capabilities = agent.get_capabilities()
    
    assert capabilities["service"] == "spotify"
    assert "categories" in capabilities
    assert len(capabilities["categories"]) == 4  # Search, Playlists, Playback, User Library
    print("✓ Spotify agent capabilities test passed")


def test_github_agent_capabilities():
    """Test GitHub agent capabilities"""
    from src.kortana.external_services.github import GitHubAgent, GitHubAgentConfig
    
    config = GitHubAgentConfig(
        llm_api_key="test-key",
        github_token="test-key",
        log_level="ERROR"
    )
    agent = GitHubAgent(config)
    capabilities = agent.get_capabilities()
    
    assert capabilities["service"] == "github"
    assert "categories" in capabilities
    assert len(capabilities["categories"]) == 4  # Repositories, Issues, PRs, Users
    print("✓ GitHub agent capabilities test passed")


def run_all_tests():
    """Run all tests"""
    print("\nRunning external services integration tests...\n")
    
    try:
        test_agent_config()
        test_service_manager()
        test_service_types()
        test_spotify_config()
        test_github_config()
        test_spotify_agent_capabilities()
        test_github_agent_capabilities()
        
        print("\n✅ All tests passed!\n")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
