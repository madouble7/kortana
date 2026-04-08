from src.utils.deduplication import TaskDeduplicator

class TaskManager:
    def __init__(self):
        self.deduplicator = TaskDeduplicator(ttl=300)
        self.queue = []

    def dispatch(self, task_data):
        repair_type = task_data.get("type")
        params = task_data.get("context", {})
        
        if self.deduplicator.is_redundant(repair_type, params):
            return
        
        self.queue.append(task_data)
        self._execute_queue()

    def _execute_queue(self):
        while self.queue:
            task = self.queue.pop(0)
            # Process task logic here