from src.utils.similarity_engine import get_similarity_score

class Scheduler:
    def __init__(self):
        self.pending_tasks = []
        self.similarity_threshold = 0.85

    def schedule(self, task):
        for existing_task in self.pending_tasks:
            score = get_similarity_score(task['description'], existing_task['description'])
            if score >= self.similarity_threshold:
                return False
        
        self.pending_tasks.append(task)
        return True