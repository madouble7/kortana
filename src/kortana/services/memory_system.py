"""
Memory System for Kor'tana
Handles storage and retrieval of memory entries
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        self.recent_interactions = []

    def get_recent_interactions(self, limit: int = 100) -> List[str]:
        """Get recent interaction history"""
        return self.recent_interactions[-limit:]

    def store_research_topic(self, topic: str, description: str) -> None:
        """Store a research topic in memory"""
        logger.info(f"Storing research topic: {topic}")
        # Implementation will be added

memory_manager = MemoryManager()
