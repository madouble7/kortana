import time

class LinkMonitor:
    def __init__(self):
        self.history = []

    def record_latency(self, latency: float):
        self.history.append({'ts': time.time(), 'latency': latency})

    def get_stability(self) -> float:
        if not self.history: return 1.0
        return 1.0 / (sum(h['latency'] for h in self.history) / len(self.history) + 1)