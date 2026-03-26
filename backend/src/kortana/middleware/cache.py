class LoggingCacheMiddleware:
    def __init__(self):
        self._local_cache = {}

    def resolve_log_description(self, log_id):
        # Return cached state to prevent live-querying the orchestrator
        if log_id in self._local_cache:
            return self._local_cache[log_id]
        return "UNKNOWN_STATE"