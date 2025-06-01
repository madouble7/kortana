from datetime import datetime
from kortana.memory.memory_manager import MemoryManager


class PlanningAgent:
    def __init__(self):
        self.mem = MemoryManager()

    def plan_day(self):
        # 1. Query yesterday's "incomplete tasks" memories
        tasks = self.mem.query("incomplete_task", k=50)
        # 2. Score & sort by significance/emotional_gravity in metadata
        prioritized = sorted(
            tasks, key=lambda x: x.metadata.get("significance_score", 0), reverse=True
        )
        # 3. Generate a to-do list (top 5)
        today = [t.content for t in prioritized[:5]]
        return {"date": datetime.utcnow().date().isoformat(), "today": today}
