from ..utils.concurrency import recursion_guard

class AlwaysOnMonitor:
    def __init__(self):
        self.is_running = False

    def verify_state(self, controller_state):
        with recursion_guard() as can_proceed:
            if not can_proceed:
                return
            if controller_state == "Unknown":
                self.trigger_emergency_protocol()
                
    def trigger_emergency_protocol(self):
        pass

monitor = AlwaysOnMonitor()

def get_always_on_monitor():
    return monitor

def start_always_on_monitor():
    monitor.is_running = True
    return monitor
    
def stop_always_on_monitor():
    monitor.is_running = False
    return monitor
