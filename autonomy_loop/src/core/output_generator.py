from src.core.directive_manager import DirectiveManager

class OutputGenerator:
    @staticmethod
    def generate_framed_output(result, task):
        directive = DirectiveManager.get_quantum_link()
        return {
            "output": result,
            "context": "framed as a node within the quantum link network",
            "directive_reference": directive,
            "alignment_status": "active"
        }