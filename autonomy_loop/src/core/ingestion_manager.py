from src.core.synthesis_layer import SynthesisMiddleware

class IngestionManager:
    def __init__(self):
        self.synthesis_layer = SynthesisMiddleware()

    def process_event(self, event_data):
        return self.synthesis_layer.process(event_data)