class ResonanceStore:
    def __init__(self):
        self.data = {}

    def retrieve(self, task):
        return self.data.get(task, {'status': 'new_evolution'})

    def update(self, task, outcome):
        self.data[task] = outcome