from src.synthesis.engine import SynthesisEngine
class DirectiveProcessor:
    def __init__(self):
        self.engine = SynthesisEngine()
    def process(self, directive):
        return self.engine.synthesize(directive)