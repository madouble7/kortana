"""
Database services for Kortana.
"""

# Import all service functions from the main services module
from ..core.services import *
from .database import *


# Maintain backward compatibility
def get_ade_llm_client():
    """Backward compatibility function for ADE LLM client"""
    from ..core.services import get_llm_service

    return get_llm_service()
