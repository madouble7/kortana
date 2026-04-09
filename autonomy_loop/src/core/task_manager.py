from src.utils.similarity_engine import generate_task_hash
from src.middleware.contextual_weaver import ContextualWeaver
from src.core.verification_engine import verify_node_integrity
import json

class TaskManager:
    def __init__(self):
        self.active_tasks = {}
        self.weaver = ContextualWeaver()
        with open('src/schema/quantum_link_node.json', 'r') as f:
            self.schema = json.load(f)

    def register_task(self, description):
        task_hash = generate_task_hash(description)
        if task_hash in self.active_tasks:
            self.active_tasks[task_hash]['metadata']['occurrence_count'] += 1
            return False, self.active_tasks[task_hash]
        
        new_task = {
            'description': description,
            'metadata': {'occurrence_count': 1, 'task_hash': task_hash}
        }
        self.active_tasks[task_hash] = new_task
        return True, new_task

    def execute_and_validate(self, task_description, output, quantum_metadata):
        is_aligned, status = self.weaver.evaluate_alignment(output)
        if not is_aligned:
            return False, "Task execution failed clarity-alignment check: {}".format(status)
        
        node_json = json.dumps(quantum_metadata)
        if not verify_node_integrity(node_json, self.schema):
            return False, "Task failed quantum node integrity check."
            
        return True, "Task processed and anchored to quantum link successfully."