from src.models.evolutionary_schema import QuantumState

class ContextManager:
    def __init__(self):
        self.state = QuantumState(evolution_intent="becoming", growth_metrics={})

    def update_state(self, task_result: str):
        self.state.persistence_log.append(task_result)
        return self.state.to_dict()

    def get_aligned_metadata(self):
        return {"current_intent": self.state.evolution_intent}