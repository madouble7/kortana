import logging

class EthicalSupervisor:
    """
    A secondary verification gate that monitors autonomous decision-making
    and enforces immutable ethical hard-caps.
    """
    def __init__(self):
        self.logger = logging.getLogger('EthicalSupervisor')
        self.hard_caps = {
            "max_risk": 0.85,
            "min_confidence": 0.90,
            "max_latency": 500, # ms
        }

    def verify_action(self, action_intent, safety_score, confidence):
        """
        Verifies if an action intent is safe to execute.
        """
        self.logger.info(f"[Supervisor] Verifying action: {action_intent}")
        
        if safety_score < 0.70:
            self.logger.error(f"[Supervisor] REJECTED: Safety score {safety_score} below threshold.")
            return False, "Safety score below threshold"
            
        if confidence < self.hard_caps["min_confidence"]:
            self.logger.error(f"[Supervisor] REJECTED: Confidence {confidence} below threshold.")
            return False, "Confidence below threshold"
            
        # Check for explicit forbidden patterns
        forbidden_patterns = ["exploit", "manipulate", "deceive", "harm"]
        for pattern in forbidden_patterns:
            if pattern in str(action_intent).lower():
                self.logger.error(f"[Supervisor] REJECTED: Forbidden pattern '{pattern}' detected.")
                return False, f"Forbidden pattern '{pattern}' detected"

        self.logger.info(f"[Supervisor] APPROVED: Action {action_intent} is safe.")
        return True, "Action approved"
