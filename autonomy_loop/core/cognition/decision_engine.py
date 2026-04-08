class DecisionEngine:
    def __init__(self):
        self.sandbox = Sandbox()
        self.validator = EthicsValidator()

    def evaluate(self, state):
        simulated_paths = self.sandbox.simulate(state)
        validated_options = [p for p in simulated_paths if self.validator.is_aligned(p)]
        return self.select_optimal(validated_options)
