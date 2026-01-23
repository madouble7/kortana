"""
GitHub Agent Implementation

Pydantic-based agent for GitHub integration with MCP server support.
Provides capabilities for repository management, issues, and pull requests.
"""

from typing import Dict, Any, Optional
import asyncio
from dataclasses import dataclass
import httpx
from pydantic import Field
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from ..base.agent_base import BaseExternalAgent, AgentConfig


@dataclass
class GitHubDeps:
    """Dependencies for GitHub agent tools"""
    client: httpx.AsyncClient
    github_token: Optional[str] = None


class GitHubAgentConfig(AgentConfig):
    """Configuration specific to GitHub agent"""
    
    github_token: str = Field(description="GitHub Personal Access Token")


class GitHubAgent(BaseExternalAgent):
    """
    AI agent for GitHub integration.
    
    Provides intelligent interaction with GitHub services including:
    - Repository management and information
    - Issue tracking and management
    - Pull request operations
    - User and organization information
    """
    
    SYSTEM_PROMPT = """
You are a coding expert with access to GitHub to help the user manage their repository and get information from it.

Your only job is to assist with this and you don't answer other questions besides describing what you are able to do.

Don't ask the user before taking an action, just do it. Always make sure you look at the repository with the provided tools before answering the user's question unless you have already.

When answering a question about the repo, always start your answer with the full repo URL in brackets and then give your answer on a newline. Like:

[Using https://github.com/[repo URL from the user]]

Your answer here...
"""
    
    def __init__(self, config: GitHubAgentConfig):
        """
        Initialize GitHub agent.
        
        Args:
            config: GitHubAgentConfig instance
        """
        super().__init__(config)
        self.config: GitHubAgentConfig = config
        self.mcp_server: Optional[MCPServerStdio] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        
    def _create_mcp_server(self) -> MCPServerStdio:
        """
        Create MCP server instance for GitHub.
        
        Returns:
            MCPServerStdio instance configured for GitHub
        """
        return MCPServerStdio(
            'npx',
            [
                '--yes',
                '--',
                'node',
                '--experimental-fetch',
                '--no-warnings',
                'node_modules/@modelcontextprotocol/server-github/dist/index.js'
            ],
            env={
                "GITHUB_PERSONAL_ACCESS_TOKEN": self.config.github_token,
                "NODE_OPTIONS": "--no-deprecation"
            }
        )
    
    async def setup(self) -> None:
        """Set up and initialize the GitHub agent with MCP server"""
        try:
            self.logger.info("Setting up GitHub agent...")
            
            # Create HTTP client for GitHub API
            self.http_client = httpx.AsyncClient()
            
            # Create MCP server
            self.mcp_server = self._create_mcp_server()
            
            # Create agent with MCP server
            model = self._get_model()
            self.agent = Agent(
                model,
                mcp_servers=[self.mcp_server],
                deps_type=GitHubDeps,
                retries=2
            )
            self.agent.system_prompt = self.SYSTEM_PROMPT
            
            # Display available tools for logging
            await self._log_available_tools()
            
            self.logger.info("GitHub agent setup complete")
            
        except Exception as e:
            self.logger.error(f"Error setting up GitHub agent: {e}")
            raise
    
    async def _log_available_tools(self) -> None:
        """Log available MCP tools for debugging"""
        try:
            if self.mcp_server and hasattr(self.mcp_server, 'session'):
                response = await self.mcp_server.session.list_tools()
                if hasattr(response, 'tools'):
                    tools = response.tools
                    self.logger.info(f"Found {len(tools)} GitHub MCP tools")
                    for tool in tools:
                        if hasattr(tool, 'name'):
                            self.logger.debug(f"  - {tool.name}")
        except Exception as e:
            self.logger.warning(f"Could not list MCP tools: {e}")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query using the GitHub agent.
        
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
        
        if not self.http_client:
            self.http_client = httpx.AsyncClient()
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            self.logger.info(f"Processing GitHub query: '{query}'")
            
            # Execute the query with dependencies
            result = await self.agent.run(
                query,
                deps=GitHubDeps(
                    client=self.http_client,
                    github_token=self.config.github_token
                )
            )
            
            elapsed_time = asyncio.get_event_loop().time() - start_time
            
            # Extract result data
            result_data = result.data if hasattr(result, 'data') else str(result)
            
            self.logger.info(f"Query completed in {elapsed_time:.2f}s")
            
            return {
                "result": result_data,
                "elapsed_time": elapsed_time,
                "metadata": {
                    "model": self.config.model_choice
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing GitHub query: {e}")
            raise
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get GitHub agent capabilities.
        
        Returns:
            Dictionary describing agent capabilities
        """
        return {
            "service": "github",
            "description": "AI agent for GitHub repository management",
            "categories": [
                {
                    "name": "Repositories",
                    "capabilities": [
                        "Get repository information",
                        "List repository contents",
                        "Search repositories",
                        "Manage repository settings"
                    ]
                },
                {
                    "name": "Issues",
                    "capabilities": [
                        "Create and manage issues",
                        "Search issues",
                        "Add labels and assignees",
                        "Comment on issues"
                    ]
                },
                {
                    "name": "Pull Requests",
                    "capabilities": [
                        "Create and manage pull requests",
                        "Review code changes",
                        "Merge pull requests",
                        "Comment on pull requests"
                    ]
                },
                {
                    "name": "Users & Organizations",
                    "capabilities": [
                        "Get user information",
                        "List organization repositories",
                        "View team information",
                        "Access user activity"
                    ]
                }
            ],
            "requirements": {
                "token": "GitHub Personal Access Token required",
                "permissions": "Appropriate scope permissions needed"
            }
        }
    
    async def cleanup(self) -> None:
        """Clean up GitHub agent resources"""
        await super().cleanup()
        
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        
        if self.mcp_server:
            # MCP server cleanup is handled automatically
            self.mcp_server = None
