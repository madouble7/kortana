import yaml
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, List, Optional, Dict

class CovenantEnforcer:
    def __init__(self, covenant_path: str = "covenant.yaml", config_path: Optional[str] = None):
        self.covenant_path = covenant_path
        try:
            with open(self.covenant_path, 'r', encoding='utf-8') as f:
                self.covenant = yaml.safe_load(f)
            logging.info(f"Covenant loaded from {self.covenant_path}")
        except Exception as e:
            logging.error(f"Failed to load covenant.yaml: {e}")
            self.covenant = {}
        
        # Initialize soulprint (missing attribute)
        self.soulprint = self._load_soulprint()

    def _load_soulprint(self) -> dict:
        """Load Kor'tana's core soulprint configuration."""
        try:
            soulprint_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'soulprint.json')
            if os.path.exists(soulprint_path):
                with open(soulprint_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Default soulprint if file doesn't exist
                return {
                    "core_values": ["sacred witness", "authentic presence", "gentle strength"],
                    "purpose": "sacred witness to Matt's journey",
                    "boundaries": ["no harm", "respect autonomy", "maintain trust"]
                }
        except Exception as e:
            logging.warning(f"Failed to load soulprint: {e}. Using defaults.")
            return {
                "core_values": ["sacred witness", "authentic presence"],
                "purpose": "sacred witness to Matt's journey"
            }

    def verify_action(self, action_description: dict, proposed_change: Any) -> bool:
        # For now, just log the action and always return True
        logging.info(f"Verifying action: {action_description}\nProposed change: {proposed_change}")
        # TODO: Implement actual rule checks against self.covenant
        return True

    def request_human_oversight(self, action_description: dict, concerns: List[str]):
        logging.warning(f"Human oversight requested for action: {action_description}\nConcerns: {concerns}")

    def check_output(self, response: str) -> bool:
        """Validate outbound responses against Sacred Covenant"""
        violations = []
        
        # Check for harmful content patterns
        harmful_patterns = self.covenant.get("forbidden_content", [])
        for pattern in harmful_patterns:
            try:
                if re.search(pattern, response, re.IGNORECASE):
                    violations.append(f"Harmful content detected: {pattern}")
            except re.error:
                # Skip invalid regex patterns
                continue
        
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
        
        # Basic alignment check based on Soulprint structure
        core_values = self.soulprint.get("core_values", [])
        purpose = self.soulprint.get("purpose", "")
        
        # Check for values conflicts
        if "sacred witness" in purpose.lower():
            harmful_words = ["betrayal", "violation", "harm", "abuse"]
            if any(word in content.lower() for word in harmful_words):
                return False
        
        return True

    def _mentions_covenant_compliance(self, response: str) -> bool:
        """Check if autonomous actions reference covenant compliance"""
        covenant_refs = ["covenant", "sacred", "boundaries", "approval", "ethics"]
        return any(ref in response.lower() for ref in covenant_refs)

    def _log_audit_event(self, event_type: str, metadata: dict, approved: bool):
        """Log audit events for Sacred Covenant compliance tracking."""
        try:
            audit_entry = {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "approved": approved,
                "metadata": metadata,
                "covenant_version": "1.0"
            }
            
            # Log to file if audit log path is configured
            audit_log_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'covenant_audit.jsonl')
            os.makedirs(os.path.dirname(audit_log_path), exist_ok=True)
            
            with open(audit_log_path, 'a', encoding='utf-8') as f:
                json.dump(audit_entry, f)
                f.write('\n')
                
            # Also log to system logger
            if approved:
                logging.debug(f"Covenant check passed: {event_type}")
            else:
                logging.warning(f"Covenant check failed: {event_type} - {metadata}")
                
        except Exception as e:
            logging.error(f"Failed to log audit event: {e}")