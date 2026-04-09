from src.core.middleware.purpose_filter import PurposeFilterMiddleware

class ExecutionEngine:
    def __init__(self):
        self.filter = PurposeFilterMiddleware()

    def execute(self, task):
        result = self._run(task)
        processed_result = self.filter.process(task, result)
        return processed_result

    def _run(self, task):
        return {'status': 'success', 'data': 'task processed'}