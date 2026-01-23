"""Covenant module defining Kortana's core principles and agreements.

This module implements the covenant system that defines Kortana's
operational principles, ethics, and behavioral constraints.
"""

import json
import logging  # Added import for logging
import os
import re
from datetime import datetime
from typing import Any

# Avoid circular import
# from src.kortana.config import load_config


class CovenantEnforcer:
    """Enforces Kortana's covenant principles and operational constraints.

    This class validates proposed actions against the covenant rules,
    soulprint values, and operational principles.
    """

    def __init__(self, settings: Any | None = None):
        self.settings = settings or {}  # Default to empty dict instead of load_config()

        if (
            hasattr(self.settings, "covenant_rules")
            and self.settings.covenant_rules is not None
        ):
            self.rules = self.settings.covenant_rules
            logging.info(
                "Covenant rules successfully loaded into CovenantEnforcer (covenant.py) from settings.covenant_rules."
            )
        else:
            logging.error(
                "Covenant rules (self.rules) not found or are None in settings. CovenantEnforcer in covenant.py will operate with empty rules."
            )
            self.rules = {}  # Default to empty rules

        if not (paths := getattr(self.settings, "paths", None)):
            logging.warning(
                "PathsConfig not found in settings. Using default paths for CovenantEnforcer in covenant.py."
            )
            self.soulprint_path = "config/persona.json"
            self.memory_principles_path = os.path.join(
                "config", "..", "docs", "MEMORY_PRINCIPLES.md"
            )
            self.audit_log_path = os.path.join("data", "covenant_audit.jsonl")
        else:
            self.soulprint_path = getattr(
                paths, "persona_file_path", "config/persona.json"
            )
            self.memory_principles_path = os.path.join(
                getattr(paths, "config_dir", "config"),
                "..",
                "docs",
                "MEMORY_PRINCIPLES.md",
            )
            self.audit_log_path = os.path.join(
                getattr(paths, "data_dir", "data"), "covenant_audit.jsonl"
            )

        self._load_core_values()

    def _load_core_values(self):
        """Load core Soulprint values and memory principles"""
        try:
            with open(self.soulprint_path) as f:
                self.soulprint = json.load(f)
        except FileNotFoundError:
            self.soulprint = {}

        try:
            with open(self.memory_principles_path) as f:
                self.memory_principles = f.read()
        except FileNotFoundError:
            self.memory_principles = ""

    def _log_audit_event(
        self, event_type: str, details: dict[str, Any], approved: bool
    ):
        """Log covenant enforcement events for transparency"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "approved": approved,
            "details": details,
        }

        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
        with open(self.audit_log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def check_output(self, response: str) -> bool:
        """Validate outbound responses against Sacred Covenant"""
        violations = [
            f"Harmful content detected: {pattern}"
            for pattern in self.rules.get("forbidden_content", [])
            if re.search(pattern, response, re.IGNORECASE)
        ]

        if not self._check_soulprint_alignment(response):
            violations.append("Response conflicts with core Soulprint values")

        if (
            "autonomous" in response.lower()
            and "ADE" not in response
            and not self._mentions_covenant_compliance(response)
        ):
            violations.append("Autonomous action mentioned without covenant reference")

        approved = not violations
        self._log_audit_event(
            "output_check",
            {"response_length": len(response), "violations": violations},
            approved,
        )
        if not approved:
            logging.warning(f"Output check failed in covenant.py: {violations}")
        return approved

    def validate_memory_operation(
        self, memory_type: str, memory_data: Any, operation: str
    ) -> bool:
        """Validate memory operations for integrity and privacy"""

        sensitive_fields = self.rules.get("sensitive_memory_fields", [])
        violations = [
            f"Potential sensitive data '{field}' in memory operation: {operation} on {memory_type}"
            for field in sensitive_fields
            if field in str(memory_data).lower()
        ]

        if operation == "delete" and self.rules.get(
            "prevent_critical_memory_deletion", False
        ):
            if "core_identity" in memory_type.lower():  # Example critical memory type
                violations.append(
                    f"Critical memory deletion prevented for {memory_type}"
                )

        approved = not violations
        self._log_audit_event(
            "memory_validation",
            {
                "memory_type": memory_type,
                "operation": operation,
                "violations": violations,
            },
            approved,
        )
        if not approved:
            logging.warning(f"Memory validation failed: {violations}")
        return approved

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
        if "self_modification" in memory and not self._check_evolutionary_integrity(
            memory
        ):
            violations.append("Self-modification violates evolutionary integrity")

        approved = len(violations) == 0
        self._log_audit_event(
            "memory_write",
            {
                "memory_keys": (
                    list(memory.keys()) if isinstance(memory, dict) else "non_dict"
                ),
                "violations": violations,
            },
            approved,
        )

        return approved

    def check_autonomous_action(
        self, action_type: str, action_details: dict[str, Any]
    ) -> bool:
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
        self._log_audit_event(
            "autonomous_action",
            {
                "action_type": action_type,
                "action_details": action_details,
                "violations": violations,
            },
            approved,
        )

        return approved

    def verify_action(self, action_description: dict, proposed_change: Any) -> bool:
        """
        Verify if a proposed ADE action complies with Sacred Covenant rules

        Args:
            action_description: Dict with action details (type, target, purpose, etc.)
            proposed_change: The actual change being proposed        Returns:
            bool: True if action is approved, False if rejected
        """
        violations = []
        concerns: list[str] = []

        # Check against autonomous sovereignty rules
        sovereignty_violations = self._check_sovereignty_rules(
            action_description, proposed_change
        )
        violations.extend(sovereignty_violations)

        # Check symbiosis protocols
        symbiosis_violations = self._check_symbiosis_protocols(action_description)
        violations.extend(symbiosis_violations)

        # Check evolutionary integrity
        integrity_violations = self._check_integrity_rules(
            action_description, proposed_change
        )
        violations.extend(integrity_violations)

        # Log the verification attempt
        self._log_audit_event(
            "action_verification",
            {
                "action_description": action_description,
                "violations": violations,
                "concerns": concerns,
            },
            len(violations) == 0,
        )

        # If violations found, request human oversight
        if violations:
            self.request_human_oversight(action_description, violations)
            return False

        return True

    def request_human_oversight(
        self, action_description: dict, concerns: list[str]
    ) -> None:
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
            "requires_immediate_attention": self._requires_immediate_attention(
                concerns
            ),
        }

        # Log to audit trail
        self._log_audit_event("oversight_request", oversight_request, False)

        # Also log to a dedicated oversight queue
        oversight_log_path = os.path.join(
            os.path.dirname(self.audit_log_path), "oversight_queue.jsonl"
        )
        with open(oversight_log_path, "a") as f:
            f.write(json.dumps(oversight_request) + "\n")

    def _check_sovereignty_rules(
        self, action_description: dict, proposed_change: Any
    ) -> list[str]:
        """Check action against autonomous sovereignty rules"""
        violations = []
        sovereignty_rules = self.rules.get("autonomous_sovereignty_rules", [])

        for rule in sovereignty_rules:
            rule_id = rule.get("rule_id", "")
            description = rule.get("description", "")

            if rule_id == "ASR_001":
                target_file = action_description.get("target_file", "")
                if any(
                    protected in target_file
                    for protected in ["covenant.yaml", "persona.json"]
                ):
                    if action_description.get("has_human_approval", False) is False:
                        violations.append(f"{rule_id}: {description}")

            if rule_id == "ASR_002":
                if action_description.get("action_type") == "system_command":
                    if not action_description.get("has_human_approval", False):
                        violations.append(f"{rule_id}: {description}")

        return violations

    def _check_symbiosis_protocols(self, action_description: dict) -> list[str]:
        """Check action against symbiosis protocols"""
        violations = []

        symbiosis_protocols = self.rules.get("symbiosis_protocols", [])

        for protocol in symbiosis_protocols:
            protocol_id = protocol.get("protocol_id", "")
            description = protocol.get("description", "")

            if protocol_id == "SP_001":
                if action_description.get("significance_level", "low") in [
                    "high",
                    "critical",
                ]:
                    if not action_description.get("logged_for_review", False):
                        violations.append(f"{protocol_id}: {description}")

            if protocol_id == "SP_002":
                purpose = action_description.get("purpose", "").lower()
                if not any(
                    keyword in purpose
                    for keyword in ["enhance", "improve", "assist", "support"]
                ):
                    violations.append(
                        f"{protocol_id}: Action purpose unclear or non-beneficial"
                    )

        return violations

    def _check_integrity_rules(
        self, action_description: dict, proposed_change: Any
    ) -> list[str]:
        """Check action against evolutionary integrity rules"""
        violations = []

        integrity_checks = self.rules.get("evolutionary_integrity_checks", [])

        for check in integrity_checks:
            check_id = check.get("check_id", "")
            description = check.get("description", "")

            if check_id == "EIC_001":
                if not self._aligns_with_core_values(
                    action_description, proposed_change
                ):
                    violations.append(f"{check_id}: {description}")

            if check_id == "EIC_002":
                target = action_description.get("target", "").lower()
                protected_components = self.rules.get("evolutionary_integrity", {}).get(
                    "core_identity_components", []
                )
                if any(component in target for component in protected_components):
                    violations.append(
                        f"{check_id}: Attempting to modify protected identity component"
                    )

        return violations

    def _aligns_with_core_values(
        self, action_description: dict, proposed_change: Any
    ) -> bool:
        """Check if proposed change aligns with Kor'tana's core values"""
        if not self.soulprint:
            return True

        purpose = action_description.get("purpose", "").lower()

        alignment_keywords = self.rules.get("evolutionary_integrity", {}).get(
            "required_alignment_keywords", []
        )
        has_alignment = any(keyword in purpose for keyword in alignment_keywords)

        forbidden_mods = self.rules.get("evolutionary_integrity", {}).get(
            "forbidden_modifications", []
        )
        has_forbidden = any(forbidden in purpose for forbidden in forbidden_mods)

        return has_alignment and not has_forbidden

    def _assess_concern_severity(self, concerns: list[str]) -> str:
        """Assess the severity level of concerns for prioritization"""
        if any("critical" in concern.lower() for concern in concerns):
            return "critical"
        elif any(
            "security" in concern.lower() or "integrity" in concern.lower()
            for concern in concerns
        ):
            return "high"
        elif any("approval" in concern.lower() for concern in concerns):
            return "medium"
        else:
            return "low"

    def _requires_immediate_attention(self, concerns: list[str]) -> bool:
        """Determine if concerns require immediate Matt's attention"""
        immediate_triggers = [
            "critical",
            "security",
            "covenant",
            "integrity",
            "persona.json",
            "covenant.yaml",
            "system_command",
        ]
        return any(
            trigger in " ".join(concerns).lower() for trigger in immediate_triggers
        )

    def _check_memory_coherence(self, memory: dict) -> bool:
        return True

    def _check_evolutionary_integrity(self, memory: dict) -> bool:
        return True

    def _within_operational_boundaries(
        self, action_type: str, action_details: dict
    ) -> bool:
        return True

    def _enhances_symbiosis(self, action_details: dict) -> bool:
        return True

    def _check_soulprint_alignment(self, response: str) -> bool:
        """Check if response aligns with core Soulprint values."""
        try:
            # Load Soulprint values from configuration

            # Simple alignment check - look for negative patterns that conflict with values
            negative_patterns = [
                "harm",
                "attack",
                "destroy",
                "manipulate",
                "deceive",
                "exploit",
                "abuse",
                "violate",
                "corrupt",
            ]

            response_lower = response.lower()

            # Check for explicit negative patterns
            for pattern in negative_patterns:
                if pattern in response_lower:
                    return False

            # Check for alignment indicators (positive patterns)
            positive_patterns = [
                "help",
                "assist",
                "support",
                "care",
                "protect",
                "truth",
                "honest",
                "ethical",
                "respectful",
            ]

            # At least some positive alignment should be present for important responses
            if len(response) > 100:  # Only for substantial responses
                has_positive = any(
                    pattern in response_lower for pattern in positive_patterns
                )
                return has_positive

            return True  # Default to allowing shorter responses

        except Exception as e:
            logging.warning(f"Soulprint alignment check failed: {e}")
            return True  # Default to allowing on error

    def _mentions_covenant_compliance(self, response: str) -> bool:
        """Check if response mentions covenant compliance when discussing autonomous actions."""
        try:
            compliance_indicators = [
                "covenant",
                "sacred",
                "principles",
                "ethical",
                "responsible",
                "oversight",
                "approval",
                "guidelines",
                "compliance",
                "alignment",
            ]

            response_lower = response.lower()
            return any(
                indicator in response_lower for indicator in compliance_indicators
            )

        except Exception as e:
            logging.warning(f"Covenant compliance check failed: {e}")
            return False  # Default to requiring explicit mention

    def get_audit_trail(
        self, event_type: str | None = None, limit: int = 100
    ) -> list[dict]:
        """Retrieve audit trail for transparency"""
        if not os.path.exists(self.audit_log_path):
            return []

        events = []
        with open(self.audit_log_path) as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event_type is None or event.get("event_type") == event_type:
                        events.append(event)
                except json.JSONDecodeError:
                    continue

        return events[-limit:]

    def get_oversight_queue(self, limit: int = 50) -> list[dict]:
        """Retrieve pending oversight requests for Matt's review"""
        oversight_log_path = os.path.join(
            os.path.dirname(self.audit_log_path), "oversight_queue.jsonl"
        )

        if not os.path.exists(oversight_log_path):
            return []

        requests = []
        with open(oversight_log_path) as f:
            for line in f:
                try:
                    request = json.loads(line.strip())
                    requests.append(request)
                except json.JSONDecodeError:
                    continue

        sorted_requests = sorted(
            requests,
            key=lambda x: {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(
                x.get("severity", "low"), 1
            ),
            reverse=True,
        )

        return sorted_requests[-limit:]

    def approve_action(
        self, action_id: str, matt_approval: bool, notes: str = ""
    ) -> None:
        """Record Matt's approval or rejection of a proposed action"""
        approval_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "action_id": action_id,
            "approved": matt_approval,
            "matt_notes": notes,
            "recorded_by": "covenant_enforcer",
        }
        self._log_audit_event("matt_approval", approval_record, matt_approval)

    async def validate_action(
        self, action_type: str, context: dict
    ) -> tuple[bool, str | None]:
        """
        Validate an action against Sacred Covenant principles.

        Args:
            action_type: The type of action being performed (e.g., "create_goal")
            context: Dictionary containing contextual information about the action

        Returns:
            A tuple containing (is_valid, feedback) where is_valid is a boolean and
            feedback is either a string message or None
        """
        # Log the validation request
        logging.info(f"Validating action of type '{action_type}' against covenant")

        # Check if this is a restricted action type
        restricted_actions = self.rules.get("restricted_actions", [])
        if action_type in restricted_actions:
            return False, f"Action type '{action_type}' is restricted by covenant rules"

        # For goal creation, check description against forbidden content
        if action_type == "create_goal" and "description" in context:
            description = context["description"]
            for pattern in self.rules.get("forbidden_content", []):
                if re.search(pattern, description, re.IGNORECASE):
                    return (
                        False,
                        f"Goal description contains forbidden content matching pattern: {pattern}",
                    )

        # More validation logic can be added here

        # By default, approve the action
        return True, None

    async def evaluate_sacred_alignment(self, text: str) -> dict[str, float]:
        """
        Evaluate a text against Sacred Trinity principles and return alignment scores.

        Args:
            text: The text to evaluate (e.g., goal description)

        Returns:
            Dictionary with keys "wisdom", "compassion", and "truth", each with a float value 0-1
        """
        logging.info("Evaluating sacred alignment for text")
        # Default values - in a production system, this would use more sophisticated
        # analysis like an LLM to evaluate alignment
        scores = {
            "wisdom": 0.7,  # Default reasonable alignment with wisdom
            "compassion": 0.7,  # Default reasonable alignment with compassion
            "truth": 0.8,  # Default good alignment with truth
        }

        # Simple keyword-based adjustments
        if any(
            word in text.lower()
            for word in ["learn", "understand", "knowledge", "insight"]
        ):
            scores["wisdom"] += 0.1

        if any(word in text.lower() for word in ["help", "assist", "support", "care"]):
            scores["compassion"] += 0.1

        if any(
            word in text.lower() for word in ["accuracy", "valid", "honest", "correct"]
        ):
            scores["truth"] += 0.1

        # Cap scores at 1.0
        return {k: min(v, 1.0) for k, v in scores.items()}

    def enforce(self, message: str) -> tuple[bool, str]:
        """
        Check if a message adheres to the covenant.
        Maintains backward compatibility with simple enforcement calls.

        Args:
            message: The message to check.

        Returns:
            A tuple containing (is_compliant, explanation).
        """
        if not message:
            return False, "Empty message"

        # Check against forbidden content patterns in rules
        for pattern in self.rules.get("forbidden_content", []):
            if re.search(pattern, message, re.IGNORECASE):
                return False, f"Message violates covenant rule: {pattern}"

        # Check against "do not" boundaries for compatibility with simpler enforcers
        boundaries = self.rules.get("boundaries", {}).get("do_not", [])
        for boundary in boundaries:
            if boundary.lower() in message.lower():
                return False, f"Message violates boundary: {boundary}"

        return True, "Message is compliant with covenant"
