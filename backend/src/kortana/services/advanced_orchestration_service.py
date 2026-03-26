from ..utils.concurrency import recursion_guard

# ... within AdvancedOrchestrationService ...

    def log_failure(self, error_data):
        with recursion_guard() as can_proceed:
            if can_proceed:
                self._write_to_db(error_data)
            else:
                self.logger.warning("Recursive log attempt blocked in OrchestrationService.")