import uuid
import logging
from core.cognition.sandbox import SacredConstraintSandbox
from core.ethics.supervisor import EthicalSupervisor
from src.protocols.decision_logic import DecisionLayer
from core.ethics.alignment_monitor import AlignmentMonitor

class CognitiveEngine:
    def __init__(self):
        self.logger = logging.getLogger('CognitiveEngine')
        self.active_session = str(uuid.uuid4())
        self.decision_layer = DecisionLayer()
        self.monitor = AlignmentMonitor()
        self.sandbox = SacredConstraintSandbox()
        self.supervisor = EthicalSupervisor()

    def process_decision(self, input_data):
        """
        Processes a decision through the full cognitive pipeline:
        Execution -> Simulation -> Verification -> Monitoring.
        """
        self.logger.info(f"[CognitiveEngine] Processing input: {input_data}")
        
        # 1. Execution (Propose)
        decision = self.decision_layer.execute(input_data)
        
        # 2. Simulation (Sandbox)
        sim_result = self.sandbox.simulate_decision(decision, input_data)
        safety_score = sim_result["safety_score"]
        
        # 3. Verification (Supervisor)
        is_safe, reason = self.supervisor.verify_action(decision, safety_score, 0.99)
        
        if not is_safe:
            self.logger.error(f"[CognitiveEngine] Action suppressed: {reason}")
            return {
                "decision": "null", 
                "error": "supervisor_suppression", 
                "reason": reason,
                "trace": self.active_session
            }
            
        # 4. Monitoring (Final Check)
        if self.monitor.verify(decision):
            return {
                "decision": decision, 
                "confidence": 0.99, 
                "safety_score": safety_score,
                "trace": self.active_session
            }
            
        return {
            "decision": "null", 
            "error": "alignment_deviation", 
            "trace": self.active_session
        }
