from src.core.task_manager import TaskManager

class AutonomousGenerator:
    def __init__(self, task_manager):
        self.task_manager = task_manager

    def propose_task(self, description):
        is_new, task = self.task_manager.register_task(description)
        if is_new:
            print(f"generating new task: {description}")
        else:
            print(f"deduplicating task. updating existing: {description}")
        return task