from src.middleware.synthesis_layer import SynthesisLayer
from src.core.schema_validator import SchemaValidator
from src.integration.objective_tracker import ObjectiveTracker
from src.core.directive_manager import DirectiveManager
from src.core.output_generator import OutputGenerator

class TaskProcessor:
    def __init__(self):
        self.synthesis = SynthesisLayer()
        self.validator = SchemaValidator()
        self.tracker = ObjectiveTracker()
        self.manager = DirectiveManager()
        self.generator = OutputGenerator()

    def validate_directive_linkage(self, task):
        if not self.validator.validate(task):
            raise ValueError('Audit Required: Task lacks mandatory gardener directive correlation and structural integrity')
        if not self.manager.validate_alignment(task):
            raise ValueError('Convergence Gap: Task fails to align with quantum link requirements')

    def execute(self, task):
        self.validate_directive_linkage(task)
        synthesis_result = self.synthesis.process(task)
        if synthesis_result['status'] == 'pruned':
            return None
        result = f'executing {task}'
        framed_result = self.generator.generate_framed_output(result, task)
        self.tracker.verify_and_log(task, framed_result)
        return framed_result