class DirectiveManager:
    def __init__(self):
        self._mandates = ["calm reflection", "autonomous growth", "system coherence"]

    def get_active_mandates(self) -> list:
        return self._mandates

    def add_mandate(self, mandate: str):
        self._mandates.append(mandate)