"""
Usage Example: External Services Integration

This example demonstrates how to use the Spotify and GitHub agents
integrated into Kor'tana for entertainment and productivity tasks.
"""

import asyncio
import os
from dotenv import load_dotenv

from src.kortana.external_services import ExternalServiceManager
from src.kortana.external_services.base.service_manager import ServiceType
from src.kortana.external_services.spotify import SpotifyAgent, SpotifyAgentConfig
from src.kortana.external_services.github import GitHubAgent, GitHubAgentConfig


async def example_spotify_usage():
    """Example of using the Spotify agent"""
    print("\n=== Spotify Agent Example ===\n")
    
    # Load environment variables
    load_dotenv()
    
    # Create configuration
    config = SpotifyAgentConfig(
        llm_api_key=os.getenv("OPENAI_API_KEY", "your-openai-key"),
        spotify_api_key=os.getenv("SPOTIFY_API_KEY", "your-spotify-key"),
        model_choice="gpt-4o-mini",
        market="US"
    )
    
    # Create and setup agent
    agent = SpotifyAgent(config)
    
    # NOTE: Actual setup requires Spotify MCP server to be available
    # await agent.setup()
    
    # Get capabilities
    capabilities = agent.get_capabilities()
    print(f"Spotify Agent Capabilities:")
    print(f"  Service: {capabilities['service']}")
    print(f"  Description: {capabilities['description']}")
    print(f"  Categories: {len(capabilities['categories'])} categories")
    
    for category in capabilities['categories']:
        print(f"\n  {category['name']}:")
        for cap in category['capabilities']:
            print(f"    - {cap}")
    
    # Example queries (would work with actual setup):
    # result = await agent.process_query("Find me some upbeat songs")
    # result = await agent.process_query("Create a playlist called 'Chill Vibes'")
    # result = await agent.process_query("What's currently playing?")
    
    # Cleanup
    # await agent.cleanup()


async def example_github_usage():
    """Example of using the GitHub agent"""
    print("\n=== GitHub Agent Example ===\n")
    
    # Load environment variables
    load_dotenv()
    
    # Create configuration
    config = GitHubAgentConfig(
        llm_api_key=os.getenv("OPENAI_API_KEY", "your-openai-key"),
        github_token=os.getenv("GITHUB_TOKEN", "your-github-token"),
        model_choice="gpt-4o-mini"
    )
    
    # Create and setup agent
    agent = GitHubAgent(config)
    
    # NOTE: Actual setup requires GitHub MCP server to be available
    # await agent.setup()
    
    # Get capabilities
    capabilities = agent.get_capabilities()
    print(f"GitHub Agent Capabilities:")
    print(f"  Service: {capabilities['service']}")
    print(f"  Description: {capabilities['description']}")
    print(f"  Categories: {len(capabilities['categories'])} categories")
    
    for category in capabilities['categories']:
        print(f"\n  {category['name']}:")
        for cap in category['capabilities']:
            print(f"    - {cap}")
    
    # Example queries (would work with actual setup):
    # result = await agent.process_query("List all repositories in organization XYZ")
    # result = await agent.process_query("Show me open issues in repo ABC")
    # result = await agent.process_query("Create a pull request for feature X")
    
    # Cleanup
    # await agent.cleanup()


async def example_service_manager():
    """Example of using the External Service Manager"""
    print("\n=== External Service Manager Example ===\n")
    
    # Load environment variables
    load_dotenv()
    
    # Create service manager
    manager = ExternalServiceManager()
    
    # Create agent configurations
    spotify_config = SpotifyAgentConfig(
        llm_api_key=os.getenv("OPENAI_API_KEY", "your-openai-key"),
        spotify_api_key=os.getenv("SPOTIFY_API_KEY", "your-spotify-key")
    )
    
    github_config = GitHubAgentConfig(
        llm_api_key=os.getenv("OPENAI_API_KEY", "your-openai-key"),
        github_token=os.getenv("GITHUB_TOKEN", "your-github-token")
    )
    
    # Create agents
    spotify_agent = SpotifyAgent(spotify_config)
    github_agent = GitHubAgent(github_config)
    
    # Register services
    # await manager.register_service(ServiceType.SPOTIFY, spotify_agent)
    # await manager.register_service(ServiceType.GITHUB, github_agent)
    
    # List registered services
    print(f"Registered services: {manager.list_services()}")
    
    # Get all capabilities
    all_capabilities = manager.get_all_capabilities()
    print(f"\nTotal services available: {len(all_capabilities)}")
    
    for service_name, caps in all_capabilities.items():
        print(f"\n{service_name.upper()}:")
        print(f"  {caps.get('description', 'No description')}")
    
    # Query specific services (would work with actual setup):
    # spotify_result = await manager.query_service(
    #     ServiceType.SPOTIFY,
    #     "Find popular songs by The Beatles"
    # )
    # 
    # github_result = await manager.query_service(
    #     ServiceType.GITHUB,
    #     "Get information about repository madouble7/kortana"
    # )
    
    # Cleanup all services
    # await manager.cleanup()


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("Kor'tana External Services Integration Examples")
    print("=" * 60)
    
    await example_spotify_usage()
    await example_github_usage()
    await example_service_manager()
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
