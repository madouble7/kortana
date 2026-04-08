class TaskNode:
    def __init__(self, id, objective, dependencies, alignment_score):
        self.id = id
        self.objective = objective
        self.dependencies = dependencies
        self.alignment_score = alignment_score
    def to_dict(self):
        return {"id": self.id, "objective": self.objective, "dependencies": self.dependencies, "alignment_score": self.alignment_score}