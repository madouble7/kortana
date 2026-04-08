from src.core.analysis.synthesis_layer import SynthesisLayer
from src.core.evolution.memory_manager import MemoryManager

class LogProcessor:
    def __init__(self):
        self.synthesis = SynthesisLayer()
        self.memory = MemoryManager()

    def process(self, raw_log):
        context = self.synthesis.contextualize(raw_log)
        enriched_log = {**raw_log, "context": context}
        self.memory.update(enriched_log)
        return enriched_log