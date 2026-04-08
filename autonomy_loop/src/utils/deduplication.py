import time
import hashlib

class TaskDeduplicator:
    def __init__(self, ttl=60):
        self.cache = {}
        self.ttl = ttl

    def is_redundant(self, task_type, params):
        key_data = f"{task_type}:{str(sorted(params.items()))}"
        task_hash = hashlib.sha256(key_data.encode()).hexdigest()
        now = time.time()

        if task_hash in self.cache and (now - self.cache[task_hash]) < self.ttl:
            return True
        
        self.cache[task_hash] = now
        return False