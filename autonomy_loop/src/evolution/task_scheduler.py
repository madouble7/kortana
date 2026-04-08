class TaskScheduler:
    def __init__(self):
        self.active_tasks = []
    def schedule(self, task_node):
        self.active_tasks.append(task_node)
        return True