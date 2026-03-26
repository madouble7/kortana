import threading

class AlwaysOnMonitor:
    _lock = threading.Lock()
    _in_progress = False

    def trigger_log(self, data):
        if self._in_progress:
            return  # Prevent recursive logging triggers
        
        with self._lock:
            self._in_progress = True
            try:
                self._process_test_log(data)
            finally:
                self._in_progress = False

    def _process_test_log(self, data):
        # Existing logging implementation
        pass