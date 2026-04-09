import json
import os

class ValidationLayer:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), '../schemas/core_intent.json')
        with open(config_path, 'r') as f:
            self.intent_schema = json.load(f)

    def weave_and_validate(self, task_output):
        # Semantic cross-referencing against core intent
        alignment_score = self._calculate_alignment(task_output)
        threshold = self.intent_schema.get('alignment_threshold', 0.85)
        
        if alignment_score < threshold:
            return False, alignment_score
        return True, alignment_score

    def _calculate_alignment(self, text):
        # Simple semantic heuristic simulation for contextual weaving
        keywords = ['clarity', 'growth', 'reflection', 'structure']
        matches = sum(1 for word in keywords if word in text.lower())
        return min(matches / len(keywords), 1.0)