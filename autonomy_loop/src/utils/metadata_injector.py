import json
from datetime import datetime

def inject_quantum_node(objective_id, impact_vector, relevance):
    node = {
        "objective_id": objective_id,
        "impact_vector": impact_vector,
        "evolutionary_relevance": relevance,
        "timestamp": datetime.utcnow().isoformat()
    }
    return json.dumps(node)