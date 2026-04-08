from src.middleware.validator import IntentValidator

class ContextualWeaver:
    def __init__(self):
        self.validator = IntentValidator()

    def evaluate_alignment(self, output):
        is_aligned, details = self.validator.validate(output)
        return is_aligned, details