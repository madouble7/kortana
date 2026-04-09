from src.core.directives import GardenerDirective

class TaskDispatcher:
    def __init__(self):
        self.directive = GardenerDirective("fostering evolutionary coherence", "quantum_link_alpha")

    def dispatch(self, task):
        context = self.directive.validate_alignment(task)
        task.inject_metadata(context)
        return self.execute(task)

    def execute(self, task):
        return f"executing task with directive: {task.metadata['directive']}"