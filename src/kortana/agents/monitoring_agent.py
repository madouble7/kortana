import psutil


class MonitoringAgent:
    def check_health(self):
        errs = []
        # 1. Check if memory usage > 80%
        if psutil.virtual_memory().percent > 80:
            errs.append("High memory usage")
        # 2. (Extend: read your logs for ERROR entries in last hour)
        return errs

    def heal(self, errors):
        fixes = []
        for e in errors:
            if "memory" in e:
                fixes.append("Restarting vector store connector")
                # pseudo-code: self.restart_vector_store()
        return fixes
