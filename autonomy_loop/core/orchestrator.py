from core.middleware.weaving import ContextualWeaver
class Orchestrator:
    def __init__(self):
        self.weaver = ContextualWeaver()
    def execute(self, task_output):
        woven_output = self.weaver.weave(task_output)
        return woven_output