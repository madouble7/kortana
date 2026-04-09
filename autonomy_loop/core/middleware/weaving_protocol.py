from typing import Any, Dict, List

class WeavingProtocol:
    def __init__(self, manager):
        self.manager = manager

    def weave(self, task_output: str) -> str:
        mandates = self.manager.get_active_mandates()
        refined_output = task_output
        for mandate in mandates:
            refined_output = self._apply_context(refined_output, mandate)
        return refined_output

    def _apply_context(self, content: str, mandate: str) -> str:
        return f"[context: {mandate}] {content}"