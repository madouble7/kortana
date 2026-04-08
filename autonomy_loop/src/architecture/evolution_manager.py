class EvolutionManager:
    def __init__(self):
        self.state = "evolving"

    def register_contribution(self, task_result):
        return f"Contribution integrated: {task_result}. System state: {self.state}."