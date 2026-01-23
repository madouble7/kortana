"""
External Service Manager

Manages multiple external service agents with modular registration,
discovery, and routing capabilities for low-latency operations.
"""

from typing import Dict, Optional, Any, List
from enum import Enum
import logging
from .agent_base import BaseExternalAgent, AgentConfig


class ServiceType(str, Enum):
    """Enumeration of supported service types"""
    SPOTIFY = "spotify"
    GITHUB = "github"
    # Future services can be added here


class ExternalServiceManager:
    """
    Manages external service agents with modular registration and routing.
    
    Provides a unified interface for interacting with multiple external
    services while maintaining efficiency and low latency.
    """
    
    def __init__(self):
        """Initialize the service manager"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._services: Dict[ServiceType, BaseExternalAgent] = {}
        self._initialized = False
        
    async def register_service(
        self,
        service_type: ServiceType,
        agent: BaseExternalAgent
    ) -> None:
        """
        Register an external service agent.
        
        Args:
            service_type: Type of service to register
            agent: Agent instance to register
        """
        try:
            # Set up the agent if not already done
            if agent.agent is None:
                await agent.setup()
            
            self._services[service_type] = agent
            self.logger.info(f"Registered service: {service_type.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to register service {service_type.value}: {e}")
            raise
    
    def get_service(self, service_type: ServiceType) -> Optional[BaseExternalAgent]:
        """
        Get a registered service agent.
        
        Args:
            service_type: Type of service to retrieve
            
        Returns:
            Agent instance if registered, None otherwise
        """
        return self._services.get(service_type)
    
    def list_services(self) -> List[ServiceType]:
        """
        List all registered services.
        
        Returns:
            List of registered service types
        """
        return list(self._services.keys())
    
    async def query_service(
        self,
        service_type: ServiceType,
        query: str
    ) -> Dict[str, Any]:
        """
        Query a specific service.
        
        Args:
            service_type: Type of service to query
            query: Query string
            
        Returns:
            Query result with metrics and metadata
            
        Raises:
            ValueError: If service is not registered
        """
        agent = self.get_service(service_type)
        if agent is None:
            raise ValueError(f"Service {service_type.value} is not registered")
        
        try:
            result = await agent.process_query(query)
            return {
                "service": service_type.value,
                "success": True,
                **result
            }
        except Exception as e:
            self.logger.error(f"Error querying service {service_type.value}: {e}")
            return {
                "service": service_type.value,
                "success": False,
                "error": str(e)
            }
    
    def get_service_capabilities(self, service_type: ServiceType) -> Dict[str, Any]:
        """
        Get capabilities of a specific service.
        
        Args:
            service_type: Type of service
            
        Returns:
            Service capabilities
            
        Raises:
            ValueError: If service is not registered
        """
        agent = self.get_service(service_type)
        if agent is None:
            raise ValueError(f"Service {service_type.value} is not registered")
        
        return agent.get_capabilities()
    
    def get_all_capabilities(self) -> Dict[str, Any]:
        """
        Get capabilities of all registered services.
        
        Returns:
            Dictionary mapping service types to their capabilities
        """
        return {
            service_type.value: agent.get_capabilities()
            for service_type, agent in self._services.items()
        }
    
    async def cleanup(self) -> None:
        """Clean up all registered services"""
        self.logger.info("Cleaning up all services")
        for service_type, agent in self._services.items():
            try:
                await agent.cleanup()
                self.logger.info(f"Cleaned up service: {service_type.value}")
            except Exception as e:
                self.logger.error(f"Error cleaning up {service_type.value}: {e}")
        
        self._services.clear()
        self._initialized = False
