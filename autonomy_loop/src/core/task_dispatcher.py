from src.core.context_engine import ContextEngine
from src.integrations.quantum_link import QuantumLink

class TaskDispatcher:
    def __init__(self):
        self.context = ContextEngine()
        self.quantum = QuantumLink()

    def dispatch(self, task_input):
        contextual_data = self.context.synthesize(task_input)
        route = self.quantum.anticipate(contextual_data)
        return self._execute_with_evolution(route, contextual_data)

    def _execute_with_evolution(self, route, data):
        result = f"Executing {route} with evolutionary alignment."
        self.context.record_feedback(data, result)
        return result