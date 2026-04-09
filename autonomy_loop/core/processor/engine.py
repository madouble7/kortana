from core.directives.manager import DirectiveManager
from core.middleware.weaving_protocol import WeavingProtocol

class IntelligenceEngine:
    def __init__(self):
        self.directive_manager = DirectiveManager()
        self.weaver = WeavingProtocol(self.directive_manager)

    def execute_task(self, input_data: str) -> str:
        raw_output = f"processing: {input_data}"
        return self.weaver.weave(raw_output)