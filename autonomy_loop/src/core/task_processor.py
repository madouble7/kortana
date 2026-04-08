from src.middleware.synthesis_layer import SynthesisLayer

class TaskProcessor:
    def __init__(self):
        self.synthesis = SynthesisLayer()

    def validate_directive_linkage(self, task):
        if 'directive' not in task or 'quantum_link_id' not in task['directive']:
            raise ValueError('Audit Required: Task lacks mandatory gardener directive correlation')

    def execute(self, task):
        self.validate_directive_linkage(task)
        synthesis_result = self.synthesis.process(task)
        if synthesis_result['status'] == 'pruned':
            return None
        return f'executing {task}'