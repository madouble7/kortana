# External Services Integration

## Overview

This document describes the external services integration module that adds AI agent capabilities to Kor'tana for managing Spotify and GitHub through natural language queries.

## Features

- **Modular Architecture**: Clean separation of concerns with base classes and service-specific implementations
- **Pydantic-Based Agents**: Type-safe configuration and validation using Pydantic models
- **MCP Server Integration**: Uses Model Context Protocol for seamless tool integration
- **Low Latency**: Designed for efficient query processing with minimal overhead
- **Extensible**: Easy to add new services following the same patterns

## Architecture

### Components

```
src/kortana/external_services/
├── __init__.py              # Main module exports
├── base/                    # Base infrastructure
│   ├── agent_base.py       # BaseExternalAgent and AgentConfig
│   └── service_manager.py  # ExternalServiceManager and ServiceType
├── spotify/                 # Spotify integration
│   ├── agent.py            # SpotifyAgent and SpotifyAgentConfig
│   └── __init__.py
└── github/                  # GitHub integration
    ├── agent.py            # GitHubAgent and GitHubAgentConfig
    └── __init__.py
```

### Class Hierarchy

```
BaseExternalAgent (ABC)
├── SpotifyAgent
└── GitHubAgent

AgentConfig (BaseModel)
├── SpotifyAgentConfig
└── GitHubAgentConfig
```

## Installation

The module requires the following dependencies:

```bash
pip install pydantic-ai httpx
```

For Node.js MCP servers (Spotify and GitHub):
```bash
npm install -g npx
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
MODEL_CHOICE=gpt-4o-mini  # optional

# Spotify Configuration
SPOTIFY_API_KEY=your_spotify_api_key

# GitHub Configuration
GITHUB_TOKEN=your_github_personal_access_token
```

### Spotify Agent

```python
from src.kortana.external_services.spotify import SpotifyAgent, SpotifyAgentConfig

config = SpotifyAgentConfig(
    llm_api_key="your-openai-key",
    spotify_api_key="your-spotify-key",
    model_choice="gpt-4o-mini",  # optional
    market="US",                  # optional, default is US
    log_level="INFO"              # optional
)

agent = SpotifyAgent(config)
await agent.setup()
```

### GitHub Agent

```python
from src.kortana.external_services.github import GitHubAgent, GitHubAgentConfig

config = GitHubAgentConfig(
    llm_api_key="your-openai-key",
    github_token="your-github-token",
    model_choice="gpt-4o-mini",  # optional
    log_level="INFO"              # optional
)

agent = GitHubAgent(config)
await agent.setup()
```

## Usage

### Basic Usage

```python
import asyncio
from src.kortana.external_services.spotify import SpotifyAgent, SpotifyAgentConfig

async def main():
    # Configure and setup
    config = SpotifyAgentConfig(
        llm_api_key="your-key",
        spotify_api_key="your-key"
    )
    agent = SpotifyAgent(config)
    await agent.setup()
    
    # Process queries
    result = await agent.process_query("Find popular songs by The Beatles")
    print(result["result"])
    
    # Cleanup
    await agent.cleanup()

asyncio.run(main())
```

### Using the Service Manager

```python
from src.kortana.external_services import ExternalServiceManager
from src.kortana.external_services.base.service_manager import ServiceType
from src.kortana.external_services.spotify import SpotifyAgent, SpotifyAgentConfig
from src.kortana.external_services.github import GitHubAgent, GitHubAgentConfig

async def main():
    # Create manager
    manager = ExternalServiceManager()
    
    # Register services
    spotify_agent = SpotifyAgent(SpotifyAgentConfig(...))
    github_agent = GitHubAgent(GitHubAgentConfig(...))
    
    await manager.register_service(ServiceType.SPOTIFY, spotify_agent)
    await manager.register_service(ServiceType.GITHUB, github_agent)
    
    # Query services
    result = await manager.query_service(
        ServiceType.SPOTIFY,
        "Create a playlist called 'Workout Mix'"
    )
    
    # Get capabilities
    capabilities = manager.get_all_capabilities()
    
    # Cleanup
    await manager.cleanup()
```

## Capabilities

### Spotify Agent

**Categories:**
- **Search**: Songs, albums, artists, recommendations
- **Playlists**: Create, manage, add/remove tracks
- **Playback**: Play, pause, skip, queue management
- **User Library**: Saved tracks, profile, listening history

**Example Queries:**
- "Find upbeat songs for working out"
- "Create a playlist called 'Chill Vibes'"
- "What song is currently playing?"
- "Add this song to my liked songs"

### GitHub Agent

**Categories:**
- **Repositories**: Information, contents, search, settings
- **Issues**: Create, manage, search, comment
- **Pull Requests**: Create, review, merge, comment
- **Users & Organizations**: User info, repos, teams, activity

**Example Queries:**
- "List all repositories in organization XYZ"
- "Show me open issues in repo ABC"
- "Create a pull request for feature X"
- "Get information about user john_doe"

## API Reference

### BaseExternalAgent

Base class for all external service agents.

**Methods:**
- `async setup()`: Initialize the agent
- `async process_query(query: str) -> Dict[str, Any]`: Process a user query
- `get_capabilities() -> Dict[str, Any]`: Get agent capabilities
- `async cleanup()`: Clean up resources

### ExternalServiceManager

Manages multiple external service agents.

**Methods:**
- `async register_service(service_type: ServiceType, agent: BaseExternalAgent)`: Register a service
- `get_service(service_type: ServiceType) -> Optional[BaseExternalAgent]`: Get a registered service
- `list_services() -> List[ServiceType]`: List all registered services
- `async query_service(service_type: ServiceType, query: str) -> Dict[str, Any]`: Query a service
- `get_service_capabilities(service_type: ServiceType) -> Dict[str, Any]`: Get service capabilities
- `get_all_capabilities() -> Dict[str, Any]`: Get all capabilities
- `async cleanup()`: Clean up all services

## Performance Considerations

- **Low Latency**: Agents are designed for efficient query processing
- **Async/Await**: Full async support for non-blocking operations
- **MCP Integration**: Direct tool access without HTTP overhead
- **Logging**: Configurable logging levels to reduce verbosity in production

## Testing

Run the standalone tests:

```bash
python test_external_services_standalone.py
```

Run the full test suite:

```bash
pytest tests/test_spotify_agent.py
pytest tests/test_github_agent.py
pytest tests/test_external_service_manager.py
```

## Extending

To add a new service:

1. Create a new directory: `src/kortana/external_services/myservice/`
2. Create agent config class extending `AgentConfig`
3. Create agent class extending `BaseExternalAgent`
4. Implement required methods: `setup()`, `process_query()`, `get_capabilities()`
5. Add service type to `ServiceType` enum
6. Register with `ExternalServiceManager`

## Troubleshooting

### MCP Server Issues

If you encounter MCP server errors:

1. Ensure Node.js is installed: `node --version`
2. Check npm packages: `npm list -g`
3. Verify API keys are correct
4. Check network connectivity

### Import Errors

If you get import errors:

1. Ensure you're in the correct directory
2. Set PYTHONPATH: `export PYTHONPATH=/path/to/kortana`
3. Install required packages: `pip install pydantic-ai httpx`

## Security

- **API Keys**: Store in `.env` file, never commit to version control
- **Tokens**: Use tokens with minimal required permissions
- **Logging**: Sensitive data is masked in logs
- **Validation**: Pydantic validates all configuration inputs

## Future Enhancements

- [ ] Add more services (Twitter, Slack, etc.)
- [ ] Implement caching for repeated queries
- [ ] Add rate limiting and quota management
- [ ] Support for custom MCP servers
- [ ] Web UI for service management
- [ ] Metrics and monitoring dashboard

## License

This module is part of Kor'tana and follows the same MIT license.
