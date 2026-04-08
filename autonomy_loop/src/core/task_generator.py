import uuid
from src.utils.similarity_engine import generate_task_hash

class TaskGenerator:
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.seen_hashes = set()

    def generate_task(self, description):
        task_hash = generate_task_hash(description)
        if task_hash in self.seen_hashes:
            return None
        
        task = {
            "id": str(uuid.uuid4()),
            "description": description,
            "hash": task_hash
        }
        self.seen_hashes.add(task_hash)
        self.scheduler.schedule(task)
        return task