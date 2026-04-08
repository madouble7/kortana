from core.directives import MandateRegister
class ContextualWeaver:
    def __init__(self):
        self.register = MandateRegister()
    def weave(self, content):
        mandates = self.register.get_all()
        resonance_check = f"\n[contextual alignment: {mandates['gardener_perspective']} | {mandates['core_alignment']}]"
        return f"{content}{resonance_check}"