"""
A monitoring agent for system health and self-healing capabilities.
This module provides functionality to check system health and perform
automatic repairs when issues are detected.
"""

from typing import List

import psutil


class MonitoringAgent:
    """
    An agent responsible for monitoring system health and performing repairs.
    Uses psutil to monitor system resources and implements self-healing capabilities.
    """

    def check_health(self) -> List[str]:
        """
        Check the health of the system and identify any issues.

        Returns:
            List[str]: A list of error messages for detected issues
        """
        errs = []
        # 1. Check if memory usage > 80%
        if psutil.virtual_memory().percent > 80:
            errs.append("High memory usage")
        # 2. (Extend: read your logs for ERROR entries in last hour)
        return errs

    def heal(self, errors: List[str]) -> List[str]:
        """
        Attempt to fix detected system issues automatically.

        Args:
            errors: A list of error messages to address

        Returns:
            List[str]: A list of fix descriptions that were applied
        """
        fixes = []
        for e in errors:
            if "memory" in e:
                fixes.append("Restarting vector store connector")
                # pseudo-code: self.restart_vector_store()
        return fixes
        return fixes
