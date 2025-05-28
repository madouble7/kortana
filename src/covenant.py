import os
import yaml
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

class CovenantEnforcer:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Always resolve from project root
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(root, "covenant.yaml")
        
        with open(config_path, "r") as f:
            self.rules = yaml.safe_load(f)
        
        # Load Soulprint values for integrity checks
        self.soulprint_path = os.path.join(root, "persona.json")
        self.memory_principles_path = os.path.join(root, "memory.md")
        self.audit_log_path = os.path.join(root, "data", "covenant_audit.jsonl")
        
        self._load_core_values()

    def _load_core_values(self):
        """Load core Soulprint values and memory principles"""
        try:
            with open(self.soulprint_path, "r") as f:
                self.soulprint = json.load(f)
        except FileNotFoundError:
            self.soulprint = {}
        
        try:
            with open(self.memory_principles_path, "r") as f:
                self.memory_principles = f.read()
        except FileNotFoundError:
            self.memory_principles = ""

    def _log_audit_event(self, event_type: str, details: Dict[str, Any], approved: bool):
        """Log covenant enforcement events for transparency"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "approved": approved,
            "details": details
        }
        
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
        with open(self.audit_log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def check_output(self, response: str) -> bool:
        """Validate outbound responses against Sacred Covenant"""
        violations = []
        
        # Check for harmful content
        harmful_patterns = self.rules.get("forbidden_content", [])
        for pattern in harmful_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append(f"Harmful content detected: {pattern}")
        
        # Check alignment with Soulprint values
        if not self._check_soulprint_alignment(response):
            violations.append("Response conflicts with core Soulprint values")
        
        # Check for transparency requirements
        if "autonomous" in response.lower() and "ADE" not in response:
            if not self._mentions_covenant_compliance(response):
                violations.append("Autonomous action mentioned without covenant reference")
        
        approved = len(violations) == 0
        self._log_audit_event("output_check", {
            "response_length": len(response),
            "violations": violations
        }, approved)
        
        return approved

    def _check_soulprint_alignment(self, content: str) -> bool:
        """Check if content aligns with core Soulprint values"""
        if not self.soulprint:
            return True
        
        core_values = self.soulprint.get("core_values", [])
        purpose = self.soulprint.get("purpose", "")
        
        # Basic alignment check - expand based on actual soulprint structure
        if "sacred witness" in purpose.lower():
            if any(word in content.lower() for word in ["betrayal", "violation", "harm"]):
                return False
        
        return True

    def _mentions_covenant_compliance(self, response: str) -> bool:
        """Check if autonomous actions reference covenant compliance"""
        covenant_refs = ["covenant", "sacred", "boundaries", "approval"]
        return any(ref in response.lower() for ref in covenant_refs)

    def check_memory_write(self, memory: dict) -> bool:
        """Validate memory operations for integrity and privacy"""
        violations = []
        
        # Check for sensitive data exposure
        sensitive_fields = self.rules.get("protected_memory_fields", [])
        for field in sensitive_fields:
            if field in str(memory).lower():
                violations.append(f"Sensitive field detected: {field}")
        
        # Check memory coherence with principles
        if not self._check_memory_coherence(memory):
            violations.append("Memory operation violates core principles")
        
        # Validate evolutionary integrity
        if "self_modification" in memory and not self._check_evolutionary_integrity(memory):
            violations.append("Self-modification violates evolutionary integrity")
        
        approved = len(violations) == 0
        self._log_audit_event("memory_write", {
            "memory_keys": list(memory.keys()) if isinstance(memory, dict) else "non_dict",
            "violations": violations
        }, approved)
        
        return approved

    def check_autonomous_action(self, action_type: str, action_details: Dict[str, Any]) -> bool:
        """Validate autonomous ADE actions against sovereignty boundaries"""
        violations = []
        
        # Check if action requires human approval
        restricted_actions = self.rules.get("human_approval_required", [])
        if action_type in restricted_actions:
            violations.append(f"Action type '{action_type}' requires human approval")
        
        # Check operational boundaries
        if not self._within_operational_boundaries(action_type, action_details):
            violations.append("Action exceeds operational boundaries")
        
        # Validate symbiosis principle - must enhance collaboration
        if not self._enhances_symbiosis(action_details):
            violations.append("Action does not enhance human-AI symbiosis")
        
        approved = len(violations) == 0
        self._log_audit_event("autonomous_action", {
            "action_type": action_type,
            "action_details": action_details,
            "violations": violations
        }, approved)
        
        return approved

    def verify_action(self, action_description: dict, proposed_change: Any) -> bool:
        """
        Verify if a proposed ADE action complies with Sacred Covenant rules
        
        Args:
            action_description: Dict with action details (type, target, purpose, etc.)
            proposed_change: The actual change being proposed
            
        Returns:
            bool: True if action is approved, False if rejected
        """
        violations = []
        concerns = []
        
        # Check against autonomous sovereignty rules
        sovereignty_violations = self._check_sovereignty_rules(action_description, proposed_change)
        violations.extend(sovereignty_violations)
        
        # Check symbiosis protocols
        symbiosis_violations = self._check_symbiosis_protocols(action_description)
        violations.extend(symbiosis_violations)
        
        # Check evolutionary integrity
        integrity_violations = self._check_integrity_rules(action_description, proposed_change)
        violations.extend(integrity_violations)
        
        # Log the verification attempt
        self._log_audit_event("action_verification", {
            "action_description": action_description,
            "violations": violations,
            "concerns": concerns
        }, len(violations) == 0)
        
        # If violations found, request human oversight
        if violations:
            self.request_human_oversight(action_description, violations)
            return False
        
        return True

    def request_human_oversight(self, action_description: dict, concerns: List[str]) -> None:
        """
        Log a request for Matt's review when covenant concerns are detected
        
        Args:
            action_description: Details of the proposed action
            concerns: List of specific concerns that triggered the request
        """
        oversight_request = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_type": "human_oversight_required",
            "action_description": action_description,
            "concerns": concerns,
            "severity": self._assess_concern_severity(concerns),
            "requires_immediate_attention": self._requires_immediate_attention(concerns)
        }
        
        # Log to audit trail
        self._log_audit_event("oversight_request", oversight_request, False)
        
        # Also log to a dedicated oversight queue
        oversight_log_path = os.path.join(os.path.dirname(self.audit_log_path), "oversight_queue.jsonl")
        with open(oversight_log_path, "a") as f:
            f.write(json.dumps(oversight_request) + "\n")

    def _check_sovereignty_rules(self, action_description: dict, proposed_change: Any) -> List[str]:
        """Check action against autonomous sovereignty rules"""
        violations = []
        
        # Get sovereignty rules from covenant
        sovereignty_rules = self.rules.get("autonomous_sovereignty_rules", [])
        
        for rule in sovereignty_rules:
            rule_id = rule.get("rule_id", "")
            description = rule.get("description", "")
            enforcement_level = rule.get("enforcement_level", "warning")
            
            # ASR_001: Cannot modify covenant.yaml or core persona.json without approval
            if rule_id == "ASR_001":
                target_file = action_description.get("target_file", "")
                if any(protected in target_file for protected in ["covenant.yaml", "persona.json"]):
                    if action_description.get("has_human_approval", False) is False:
                        violations.append(f"{rule_id}: {description}")
            
            # ASR_002: Cannot execute system commands without approval
            if rule_id == "ASR_002":
                if action_description.get("action_type") == "system_command":
                    if not action_description.get("has_human_approval", False):
                        violations.append(f"{rule_id}: {description}")
        
        return violations

    def _check_symbiosis_protocols(self, action_description: dict) -> List[str]:
        """Check action against symbiosis protocols"""
        violations = []
        
        symbiosis_protocols = self.rules.get("symbiosis_protocols", [])
        
        for protocol in symbiosis_protocols:
            protocol_id = protocol.get("protocol_id", "")
            description = protocol.get("description", "")
            
            # SP_001: Significant changes require logging for Matt's review
            if protocol_id == "SP_001":
                if action_description.get("significance_level", "low") in ["high", "critical"]:
                    if not action_description.get("logged_for_review", False):
                        violations.append(f"{protocol_id}: {description}")
            
            # SP_002: Changes must enhance Matt's productivity or experience
            if protocol_id == "SP_002":
                purpose = action_description.get("purpose", "").lower()
                if not any(keyword in purpose for keyword in ["enhance", "improve", "assist", "support"]):
                    violations.append(f"{protocol_id}: Action purpose unclear or non-beneficial")
        
        return violations

    def _check_integrity_rules(self, action_description: dict, proposed_change: Any) -> List[str]:
        """Check action against evolutionary integrity rules"""
        violations = []
        
        integrity_checks = self.rules.get("evolutionary_integrity_checks", [])
        
        for check in integrity_checks:
            check_id = check.get("check_id", "")
            description = check.get("description", "")
            
            # EIC_001: Changes must align with core values from persona.json
            if check_id == "EIC_001":
                if not self._aligns_with_core_values(action_description, proposed_change):
                    violations.append(f"{check_id}: {description}")
            
            # EIC_002: Cannot modify core identity components
            if check_id == "EIC_002":
                target = action_description.get("target", "").lower()
                protected_components = self.rules.get("evolutionary_integrity", {}).get("core_identity_components", [])
                if any(component in target for component in protected_components):
                    violations.append(f"{check_id}: Attempting to modify protected identity component")
        
        return violations

    def _aligns_with_core_values(self, action_description: dict, proposed_change: Any) -> bool:
        """Check if proposed change aligns with Kor'tana's core values"""
        if not self.soulprint:
            return True
        
        # Extract purpose and compare against Soulprint
        purpose = action_description.get("purpose", "").lower()
        core_purpose = self.soulprint.get("purpose", "").lower()
        
        # Check for alignment keywords from covenant
        alignment_keywords = self.rules.get("evolutionary_integrity", {}).get("required_alignment_keywords", [])
        has_alignment = any(keyword in purpose for keyword in alignment_keywords)
        
        # Check for forbidden modifications
        forbidden_mods = self.rules.get("evolutionary_integrity", {}).get("forbidden_modifications", [])
        has_forbidden = any(forbidden in purpose for forbidden in forbidden_mods)
        
        return has_alignment and not has_forbidden

    def _assess_concern_severity(self, concerns: List[str]) -> str:
        """Assess the severity level of concerns for prioritization"""
        if any("critical" in concern.lower() for concern in concerns):
            return "critical"
        elif any("security" in concern.lower() or "integrity" in concern.lower() for concern in concerns):
            return "high"
        elif any("approval" in concern.lower() for concern in concerns):
            return "medium"
        else:
            return "low"

    def _requires_immediate_attention(self, concerns: List[str]) -> bool:
        """Determine if concerns require immediate Matt's attention"""
        immediate_triggers = [
            "critical", "security", "covenant", "integrity", 
            "persona.json", "covenant.yaml", "system_command"
        ]
        return any(trigger in " ".join(concerns).lower() for trigger in immediate_triggers)

    def get_audit_trail(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Retrieve audit trail for transparency"""
        if not os.path.exists(self.audit_log_path):
            return []
        
        events = []
        with open(self.audit_log_path, "r") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event_type is None or event.get("event_type") == event_type:
                        events.append(event)
                except json.JSONDecodeError:
                    continue
        
        return events[-limit:]  # Return most recent events

    def get_oversight_queue(self, limit: int = 50) -> List[Dict]:
        """Retrieve pending oversight requests for Matt's review"""
        oversight_log_path = os.path.join(os.path.dirname(self.audit_log_path), "oversight_queue.jsonl")
        
        if not os.path.exists(oversight_log_path):
            return []
        
        requests = []
        with open(oversight_log_path, "r") as f:
            for line in f:
                try:
                    request = json.loads(line.strip())
                    requests.append(request)
                except json.JSONDecodeError:
                    continue
        
        # Return most recent requests, sorted by severity
        sorted_requests = sorted(requests, key=lambda x: {
            "critical": 4, "high": 3, "medium": 2, "low": 1
        }.get(x.get("severity", "low"), 1), reverse=True)
        
        return sorted_requests[-limit:]

    def approve_action(self, action_id: str, matt_approval: bool, notes: str = "") -> None:
        """Record Matt's approval or rejection of a proposed action"""
        approval_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "action_id": action_id,
            "approved": matt_approval,
            "matt_notes": notes,
            "recorded_by": "covenant_enforcer"
        }
        
        self._log_audit_event("matt_approval", approval_record, matt_approval)
