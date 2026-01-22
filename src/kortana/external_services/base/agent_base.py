"""
Base Agent Configuration and Abstract Classes

Provides the foundational Pydantic-based agent infrastructure for
external service integration with efficiency and low latency in mind.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field
import logging
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


class AgentConfig(BaseModel):
    """Configuration model for external service agents"""
    
    model_choice: str = Field(default="gpt-4o-mini", description="LLM model to use")
    base_url: str = Field(default="https://api.openai.com/v1", description="API base URL")
    llm_api_key: str = Field(description="API key for LLM provider")
    service_api_key: Optional[str] = Field(default=None, description="Service-specific API key")
    service_token: Optional[str] = Field(default=None, description="Service-specific token")
    log_level: str = Field(default="INFO", description="Logging level")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    class Config:
        """Pydantic model configuration"""
        extra = "allow"  # Allow additional fields for service-specific configs


class BaseExternalAgent(ABC):
    """
    Abstract base class for external service agents.
    
    Provides common functionality for Pydantic AI-based agents
    that interact with external services like Spotify and GitHub.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the base agent.
        
        Args:
            config: AgentConfig instance with agent configuration
        """
        self.config = config
        self.logger = self._setup_logging()
        self.agent: Optional[Agent] = None
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the agent"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(getattr(logging, self.config.log_level))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _get_model(self) -> OpenAIModel:
        """
        Initialize the OpenAI model with the provided configuration.
        
        Returns:
            OpenAIModel instance
        """
        try:
            model = OpenAIModel(
                self.config.model_choice,
                provider=OpenAIProvider(
                    base_url=self.config.base_url,
                    api_key=self.config.llm_api_key
                )
            )
            self.logger.debug(f"Initialized model: {self.config.model_choice}")
            return model
        except Exception as e:
            self.logger.error(f"Error initializing model: {e}")
            raise
    
    @abstractmethod
    async def setup(self) -> None:
        """
        Set up and initialize the agent with service-specific configuration.
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query using the agent.
        
        Args:
            query: User's query string
            
        Returns:
            Dictionary containing result, metrics, and metadata
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this agent.
        
        Returns:
            Dictionary describing agent capabilities
        """
        pass
    
    async def cleanup(self) -> None:
        """Clean up resources used by the agent"""
        self.logger.info(f"Cleaning up {self.__class__.__name__}")
        # Default cleanup - can be overridden by subclasses
