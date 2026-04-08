from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class QuantumState:
    evolution_intent: str
    growth_metrics: Dict[str, float] = field(default_factory=dict)
    persistence_log: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {"intent": self.evolution_intent, "metrics": self.growth_metrics, "logs": self.persistence_log}