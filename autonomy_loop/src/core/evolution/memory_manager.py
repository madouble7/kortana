class MemoryManager:
    def __init__(self):
        self.buffer = []
        self.max_size = 100

    def update(self, entry):
        self.buffer.append(entry)
        if len(self.buffer) > self.max_size:
            self.buffer.pop(0)

    def get_recent_threads(self):
        return self.buffer