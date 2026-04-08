from src.core.context_store import ContextStore
from src.evolution.objective_mapper import ObjectiveMapper

class SynthesisMiddleware:
    def __init__(self):
        self.store = ContextStore()
        self.mapper = ObjectiveMapper()

    def process(self, event_data):
        context = self.store.get_latest_state()
        mapped_task = self.mapper.align(event_data, context)
        self.store.update_state(mapped_task)
        return mapped_task