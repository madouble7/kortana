import threading
import logging

_actual_logger = logging.getLogger("KortanaMonitor")

class MonitorGuard:
    _lock = threading.Lock()
    _in_progress = False

    @classmethod
    def enter(cls):
        with cls._lock:
            if cls._in_progress: return False
            cls._in_progress = True
            return True

    @classmethod
    def exit(cls):
        with cls._lock:
            cls._in_progress = False

def log_failure_safe(error_msg: str):
    if not MonitorGuard.enter():
        return
    try:
        _actual_logger.error(error_msg)
    finally:
        MonitorGuard.exit()