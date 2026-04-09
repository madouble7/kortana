from src.knowledge.synthesis_engine import SynthesisEngine

class PurposeFilter:
    def __init__(self):
        self.synthesis_engine = SynthesisEngine()

    def process_output(self, task, result, status="success", error=None):
        metadata = {"task": task, "status": status, "error": error}
        self.synthesis_engine.parse_event(metadata)
        return result