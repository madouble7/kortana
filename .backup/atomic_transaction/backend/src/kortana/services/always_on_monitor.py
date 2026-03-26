from ..utils.concurrency import recursion_guard

# ... within AlwaysOnMonitor ...

    def verify_state(self, controller_state):
        with recursion_guard() as can_proceed:
            if not can_proceed:
                return
            # Existing verification logic continues here
            if controller_state == "Unknown":
                self.trigger_emergency_protocol()