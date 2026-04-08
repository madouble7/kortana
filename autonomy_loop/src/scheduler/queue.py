import heapq; import threading; from dataclasses import dataclass, field; from typing import Any, Optional
@dataclass(order=True)
class Task:
    priority: int
    autonomy_index: float = field(compare=False)
    data: Any = field(compare=False)
class PriorityQueue:
    def __init__(self):
        self.heap = []
        self.lock = threading.Lock()
    def push(self, task: Task):
        with self.lock:
            heapq.heappush(self.heap, task)
    def pop(self) -> Optional[Task]:
        with self.lock:
            return heapq.heappop(self.heap) if self.heap else None