from src.core.knowledge.tapestry_manager import TapestryManager

class PurposeFilterMiddleware:
    def __init__(self):
        self.tapestry = TapestryManager()

    def process(self, task, result):
        if result.get('status') == 'error':
            self.tapestry.record_growth_node(task, result)
        return result