from src.utils.metadata_injector import inject_quantum_node
from src.core.verification_engine import verify_node_integrity
import json

def generate_report(task_data, objective_id, impact_vector, relevance):
    schema = json.load(open('src/schemas/node_schema.json'))
    node = inject_quantum_node(objective_id, impact_vector, relevance)
    if verify_node_integrity(node, schema):
        return {"task": task_data, "quantum_node": json.loads(node)}
    raise ValueError("Alignment verification failed.")