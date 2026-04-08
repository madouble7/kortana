from src.model.node_schema import TaskNode
class SynthesisEngine:
    def synthesize(self, directive):
        nodes = []
        sub_goals = self._decompose(directive)
        for i, goal in enumerate(sub_goals):
            node = TaskNode(i, goal, [], 1.0)
            nodes.append(node)
        return nodes
    def _decompose(self, directive):
        return [f"cycle_step_{directive}_{i}" for i in range(3)]