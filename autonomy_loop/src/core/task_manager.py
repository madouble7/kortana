from src.utils.similarity_engine import generate_task_hash
from src.middleware.contextual_weaver import ContextualWeaver

class TaskManager:
    def __init__(self):
        self.active_tasks = {}
        self.weaver = ContextualWeaver()

    def register_task(self, description):
        task_hash = generate_task_hash(description)
        if task_hash in self.active_tasks:
            self.active_tasks[task_hash]['metadata']['occurrence_count'] += 1
            return False, self.active_tasks[task_hash]
        
        new_task = {
            'description': description,
            'metadata': {'occurrence_count': 1}
        }
        self.active_tasks[task_hash] = new_task
        return True, new_task

    def execute_and_validate(self, task_description, output):
        is_aligned, status = self.weaver.evaluate_alignment(output)
        if not is_aligned:
            return False, "Task execution failed clarity-alignment check: {}".format(status)
        return True, "Task processed successfully."