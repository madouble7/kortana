from typing import Dict, Any
from src.interfaces.directive import GardenersDirective

class TaskRegistry:
    def __init__(self):
        self._registry: Dict[str, GardenersDirective] = {}

    def register_task(self, task_id: str, directive: GardenersDirective):
        if not directive.get('quantum_link_id'):
            raise ValueError('Task must be linked to a quantum-link module')
        self._registry[task_id] = directive

    def get_directive(self, task_id: str) -> Optional[GardenersDirective]:
        return self._registry.get(task_id)