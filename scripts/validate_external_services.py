"""
Validation script for external services

Validates the external services module without needing the full Kortana environment.
Run this to verify the basic functionality of the external services integration.
"""

import sys
import os

# Add parent directory to path for module imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kortana.external_services.base.agent_base import AgentConfig, BaseExternalAgent
from src.kortana.external_services.base.service_manager import ExternalServiceManager, ServiceType


def validate_agent_config():
    """Test AgentConfig creation"""
    config = AgentConfig(
        llm_api_key="test-key",
        model_choice="gpt-4o-mini",
        log_level="INFO"
    )
    assert config.llm_api_key == "test-key"
    assert config.model_choice == "gpt-4o-mini"
    print("✓ AgentConfig validated")


def validate_service_manager():
    """Test ExternalServiceManager"""
    manager = ExternalServiceManager()
    assert manager._services == {}
    assert len(manager.list_services()) == 0
    print("✓ ServiceManager validated")


def validate_service_types():
    """Test ServiceType enum"""
    assert ServiceType.SPOTIFY == "spotify"
    assert ServiceType.GITHUB == "github"
    print("✓ ServiceType validated")


def validate_spotify_config():
    """Test Spotify agent config"""
    from src.kortana.external_services.spotify import SpotifyAgentConfig
    
    config = SpotifyAgentConfig(
        llm_api_key="test-llm-key",
        spotify_api_key="test-spotify-key",
        market="US"
    )
    assert config.spotify_api_key == "test-spotify-key"
    assert config.market == "US"
    print("✓ SpotifyAgentConfig validated")


def validate_github_config():
    """Test GitHub agent config"""
    from src.kortana.external_services.github import GitHubAgentConfig
    
    config = GitHubAgentConfig(
        llm_api_key="test-llm-key",
        github_token="test-github-token"
    )
    assert config.github_token == "test-github-token"
    print("✓ GitHubAgentConfig validated")


def validate_spotify_agent_capabilities():
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
    print("✓ Spotify agent capabilities validated")


def validate_github_agent_capabilities():
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
    print("✓ GitHub agent capabilities validated")


def run_all_validations():
    """Run all tests"""
    print("\nRunning external services validation...\n")
    
    try:
        validate_agent_config()
        validate_service_manager()
        validate_service_types()
        validate_spotify_config()
        validate_github_config()
        validate_spotify_agent_capabilities()
        validate_github_agent_capabilities()
        
        print("\n✅ All validations passed!\n")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_validations())
