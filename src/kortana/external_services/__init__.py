"""
External Services Integration Module for Kor'tana

This module provides modular support for integrating external services
such as Spotify and GitHub, enabling AI agent capabilities for entertainment
and productivity tools.
"""

from .base.agent_base import BaseExternalAgent, AgentConfig
from .base.service_manager import ExternalServiceManager

__all__ = [
    "BaseExternalAgent",
    "AgentConfig",
    "ExternalServiceManager",
]
