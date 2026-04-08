import json

class IntentValidator:
    def __init__(self):
        with open('src/config/intent_schema.json', 'r') as f:
            self.schema = json.load(f)

    def validate(self, output):
        alignment_score = self._calculate_alignment(output)
        is_aligned = alignment_score >= self.schema['alignment_threshold']
        return is_aligned, {"score": alignment_score, "objective": self.schema['core_objective']}

    def _calculate_alignment(self, output):
        # Simulation of contextual weaving alignment check
        keywords = self.schema['pillars']
        matches = sum(1 for kw in keywords if kw.lower() in output.lower())
        return min(matches / len(keywords), 1.0)