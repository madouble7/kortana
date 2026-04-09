import json
from datetime import datetime

class TapestryManager:
    def record_growth_node(self, task, error_data):
        node = {
            'timestamp': datetime.utcnow().isoformat(),
            'task': task,
            'error': error_data,
            'category': 'architectural_evolution'
        }
        self._persist_to_tapestry(node)

    def _persist_to_tapestry(self, node):
        # Appending to central tapestry log
        with open('data/tapestry.json', 'a') as f:
            f.write(json.dumps(node) + '\n')

    def reconcile_tapestry(self):
        # Weekly synthesis of nodes into knowledge graph
        pass