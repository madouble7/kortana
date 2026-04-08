from src.directives.quantum_link import QuantumLinkDirective

class SynthesisLayer:
    @staticmethod
    def process(task):
        intent = task.get('intent', '')
        is_aligned = QuantumLinkDirective.evaluate_intent(intent)
        if not is_aligned:
            return {'status': 'pruned', 'reason': 'non-aligned peripheral task'}
        return {'status': 'accepted', 'task': task}