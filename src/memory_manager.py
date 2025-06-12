import json
import os
from datetime import datetime
from typing import Any


class MemoryManager:
    """
    Core memory system for Kor'tana with persistent storage and contextual retrieval.
    """
    def __init__(self, memory_file: str = "data/memory.jsonl"):
        self.memory_file = memory_file
        self.ensure_memory_file_exists()

    def ensure_memory_file_exists(self) -> None:
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w') as f:
                f.write("")

    def store_memory(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        timestamp = datetime.now().isoformat()
        memory_entry = {
            "timestamp": timestamp,
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        memory_entry["id"] = f"mem_{timestamp.replace(':', '').replace('.', '').replace('-', '')}"
        with open(self.memory_file, 'a') as f:
            f.write(json.dumps(memory_entry) + "\n")
        return memory_entry

    def retrieve_memories(self, limit: int = 10, role: str | None = None, start_time: str | None = None, end_time: str | None = None, metadata_filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        memories = []
        try:
            with open(self.memory_file) as f:
                for line in f:
                    if line.strip():
                        try:
                            memory = json.loads(line)
                            if role and memory.get("role") != role:
                                continue
                            if start_time and memory.get("timestamp", "") < start_time:
                                continue
                            if end_time and memory.get("timestamp", "") > end_time:
                                continue
                            if metadata_filter:
                                memory_metadata = memory.get("metadata", {})
                                skip = False
                                for key, value in metadata_filter.items():
                                    if memory_metadata.get(key) != value:
                                        skip = True
                                        break
                                if skip:
                                    continue
                            memories.append(memory)
                            if len(memories) >= limit:
                                break
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            self.ensure_memory_file_exists()
        return sorted(memories, key=lambda x: x.get("timestamp", ""), reverse=True)
