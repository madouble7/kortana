from abc import ABC, abstractmethod
from typing import List, Dict, Any

class MemoryStore(ABC):
    @abstractmethod
    def add_memory(self, memory: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def query_memories(self, query: str, top_k: int = 5, tags: List[str] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_memory(self, memory_id: str) -> None:
        pass

    @abstractmethod
    def tag_memory(self, memory_id: str, tags: List[str]) -> None:
        pass
