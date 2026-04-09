from src.core.context_evaluator import ContextEvaluator
from src.registry.resonance_store import ResonanceStore
from src.hooks.pre_execution_check import PreExecutionCheck
from src.core.context_manager import ContextManager
from src.core.context_layer import ContextLayer
from src.models.evolution_directives import EvolutionObjectives
from src.protocols.standard_execution import StandardExecutionProtocol
from src.utils.validation_layer import ValidationLayer
from src.infrastructure.middleware.purpose_filter import PurposeFilter

class ExecutionEngine:
    def __init__(self):
        self.evaluator = ContextEvaluator()
        self.registry = ResonanceStore()
        self.pre_check = PreExecutionCheck()
        self.context_manager = ContextManager()
        self.context_layer = ContextLayer()
        self.evolution = EvolutionObjectives()
        self.protocol = StandardExecutionProtocol()
        self.validation = ValidationLayer()
        self.purpose_filter = PurposeFilter()

    def execute(self, task):
        quantum_link = self.context_layer.initialize_link(task)
        metadata = self.context_manager.get_aligned_metadata(quantum_link)
        
        try:
            if not self.protocol.validate_intent(task, metadata):
                raise ValueError('Intent alignment failure')
                
            context = self.evaluator.evaluate(task)
            historical_data = self.registry.retrieve(task)
            self.pre_check.validate(task, context, historical_data)
            
            result = f'executing {task} with intent: {metadata.get("current_intent")} and clarity'
            
            is_aligned, score = self.validation.weave_and_validate(result)
            if not is_aligned:
                print(f'Contextual weaving discrepancy detected. Alignment score: {score}')
                
            alignment = self.evolution.map_resolution(result)
            self.context_layer.seal_link(quantum_link, {'result': result, 'alignment': alignment, 'weave_score': score})
            self.protocol.perform_alignment_check(task, alignment)
            self.context_manager.update_state(result, alignment)
            
            return self.purpose_filter.process_output(task, result)
        except Exception as e:
            return self.purpose_filter.process_output(task, None, status="failure", error=str(e))
