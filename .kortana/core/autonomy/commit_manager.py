import os
import time
import re

class AtomicCommitManager:
    LOCK_FILE = ".kortana/autonomy.lock"
    MAX_RETRIES = 3

    def execute_commit(self, message, attempt=0):
        if os.path.exists(self.LOCK_FILE):
            if attempt >= self.MAX_RETRIES:
                raise RuntimeError("Failed to acquire lock: Max retries exceeded")
            time.sleep(0.5)
            return self.execute_commit(message, attempt + 1)
        
        try:
            self._create_lock()
            clean_message = self._sanitize_message(message)
            # Mocked execution for filesystem commit integration
            print(f"Executing commit: {clean_message}")
        finally:
            self._release_lock()

    def _sanitize_message(self, message):
        # Reduce redundant prefixes to single [AUTO]
        clean = re.sub(r'(\[AUTO\]\s*)+', '[AUTO] ', message)
        return clean.strip()

    def _create_lock(self):
        with open(self.LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))

    def _release_lock(self):
        if os.path.exists(self.LOCK_FILE):
            os.remove(self.LOCK_FILE)