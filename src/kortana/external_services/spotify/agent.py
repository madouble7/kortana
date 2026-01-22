"""
Spotify Agent Implementation

Pydantic-based agent for Spotify integration with MCP server support.
Provides capabilities for music search, playlist management, and playback control.
"""

from typing import Dict, Any, Optional
import asyncio
from pydantic import Field
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from ..base.agent_base import BaseExternalAgent, AgentConfig


class SpotifyAgentConfig(AgentConfig):
    """Configuration specific to Spotify agent"""
    
    spotify_api_key: str = Field(description="Spotify API key")
    market: str = Field(default="US", description="Default market for queries")


class SpotifyAgent(BaseExternalAgent):
    """
    AI agent for Spotify integration.
    
    Provides intelligent interaction with Spotify services including:
    - Music search (songs, albums, artists)
    - Playlist management
    - Playback control
    - User library and recommendations
    """
    
    SYSTEM_PROMPT = """
You are a helpful Spotify assistant that can help users interact with their Spotify account.

Your capabilities include:
- Searching for songs, albums, and artists
- Creating and managing playlists
- Controlling playback (play, pause, skip, etc.)
- Getting information about the user's library and recommendations

IMPORTANT: When using Spotify API tools, be aware of these requirements:
- For searching or getting top tracks, a 'market' parameter (e.g., 'US') is required
- Playlist operations need playlist IDs
- Most track operations require track IDs

When responding to the user, always be concise and helpful. If you don't know how to do something with the available tools, 
explain what you can do instead.
"""
    
    def __init__(self, config: SpotifyAgentConfig):
        """
        Initialize Spotify agent.
        
        Args:
            config: SpotifyAgentConfig instance
        """
        super().__init__(config)
        self.config: SpotifyAgentConfig = config
        self.mcp_server: Optional[MCPServerStdio] = None
        
    def _create_mcp_server(self) -> MCPServerStdio:
        """
        Create MCP server instance for Spotify.
        
        Returns:
            MCPServerStdio instance configured for Spotify
        """
        return MCPServerStdio(
            'npx',
            [
                '-y',
                '@smithery/cli@latest',
                'run',
                '@superseoworld/mcp-spotify',
                '--key',
                self.config.spotify_api_key
            ]
        )
    
    async def setup(self) -> None:
        """Set up and initialize the Spotify agent with MCP server"""
        try:
            self.logger.info("Setting up Spotify agent...")
            
            # Create MCP server
            self.mcp_server = self._create_mcp_server()
            
            # Create agent with MCP server
            model = self._get_model()
            self.agent = Agent(model, mcp_servers=[self.mcp_server])
            self.agent.system_prompt = self.SYSTEM_PROMPT
            
            # Display available tools for logging
            await self._log_available_tools()
            
            self.logger.info("Spotify agent setup complete")
            
        except Exception as e:
            self.logger.error(f"Error setting up Spotify agent: {e}")
            raise
    
    async def _log_available_tools(self) -> None:
        """Log available MCP tools for debugging"""
        try:
            if self.mcp_server and hasattr(self.mcp_server, 'session'):
                response = await self.mcp_server.session.list_tools()
                if hasattr(response, 'tools'):
                    tools = response.tools
                    self.logger.info(f"Found {len(tools)} Spotify MCP tools")
                    for tool in tools:
                        if hasattr(tool, 'name'):
                            self.logger.debug(f"  - {tool.name}")
        except Exception as e:
            self.logger.warning(f"Could not list MCP tools: {e}")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query using the Spotify agent.
        
        Args:
            query: User's query string
            
        Returns:
            Dictionary containing:
                - result: Agent's response
                - elapsed_time: Query processing time
                - metadata: Additional metadata
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call setup() first.")
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            self.logger.info(f"Processing Spotify query: '{query}'")
            
            # Execute the query
            result = await self.agent.run(query)
            
            elapsed_time = asyncio.get_event_loop().time() - start_time
            
            # Extract result data
            result_data = result.data if hasattr(result, 'data') else str(result)
            
            self.logger.info(f"Query completed in {elapsed_time:.2f}s")
            
            return {
                "result": result_data,
                "elapsed_time": elapsed_time,
                "metadata": {
                    "model": self.config.model_choice,
                    "market": self.config.market
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing Spotify query: {e}")
            raise
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get Spotify agent capabilities.
        
        Returns:
            Dictionary describing agent capabilities
        """
        return {
            "service": "spotify",
            "description": "AI agent for Spotify music streaming service",
            "categories": [
                {
                    "name": "Search",
                    "capabilities": [
                        "Search for songs, albums, and artists",
                        "Get top tracks by artist",
                        "Find music recommendations"
                    ]
                },
                {
                    "name": "Playlists",
                    "capabilities": [
                        "Create and manage playlists",
                        "Add/remove tracks from playlists",
                        "Get playlist information"
                    ]
                },
                {
                    "name": "Playback",
                    "capabilities": [
                        "Control playback (play, pause, skip)",
                        "Get current playback state",
                        "Manage playback queue"
                    ]
                },
                {
                    "name": "User Library",
                    "capabilities": [
                        "Access user's saved tracks",
                        "Get user profile information",
                        "View listening history"
                    ]
                }
            ],
            "requirements": {
                "api_key": "Spotify API key required",
                "market": "Market parameter for regional content"
            }
        }
    
    async def cleanup(self) -> None:
        """Clean up Spotify agent resources"""
        await super().cleanup()
        if self.mcp_server:
            # MCP server cleanup is handled automatically
            self.mcp_server = None
