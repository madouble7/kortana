"""
Project Kor'tana - Sacred Circuit Development Platform
Autonomous AI Agent Development and Management System
"""

__version__ = "1.0.0"
__author__ = "Project Kor'tana Development Team"
__description__ = (
    "Autonomous AI Agent Development Platform with Sacred Circuit Principles"
)

# Core imports for convenience
# Import from config module
try:
    from .config import get_api_key, get_config, load_config
    from .core.autonomous_development_engine import AutonomousDevelopmentEngine
    from .core.brain import Brain
    from .memory.memory_manager import MemoryManager
except ImportError as e:
    print(f"Error importing kortana modules: {e}")

__all__ = [
    "load_config",
    "get_config",
    "get_api_key",
    "Brain",
    "AutonomousDevelopmentEngine",
    "MemoryManager",
]
