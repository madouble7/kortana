"""
Project Kor'tana - Sacred Circuit Development Platform
Autonomous AI Agent Development and Management System
"""

__version__ = "1.0.0"
__author__ = "Project Kor'tana Development Team"
__description__ = "Autonomous AI Agent Development Platform with Sacred Circuit Principles"

# Core imports for convenience
from .config import load_config, get_config, get_api_key
from .core.brain import Brain
from .core.autonomous_development_engine import AutonomousDevelopmentEngine
from .memory.memory_manager import MemoryManager
from .agents.autonomous_agents import AutonomousAgents

__all__ = [
    "load_config",
    "get_config", 
    "get_api_key",
    "Brain",
    "AutonomousDevelopmentEngine",
    "MemoryManager",
    "AutonomousAgents",
]
