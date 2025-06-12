"""
Covenant Enforcer

This module provides the CovenantEnforcer, which ensures that interactions
adhere to the established covenant/guidelines.
"""

import logging
from typing import Any

import yaml

from kortana.config.schema import KortanaConfig

logger = logging.getLogger(__name__)


class CovenantEnforcer:
    """
    Enforces the covenant (guidelines and rules) for Kor'tana.

    The covenant defines what is allowed and not allowed in interactions,
    ensuring ethical behavior and alignment with core values.
    """

    def __init__(self, settings: KortanaConfig):
        """
        Initialize the covenant enforcer.

        Args:
            settings: The application configuration.
        """
        self.settings = settings
        self.covenant = self._load_covenant(settings.paths.covenant_file_path)

    def _load_covenant(self, covenant_file_path: str) -> dict[str, Any]:
        """
        Load the covenant from a YAML file.

        Args:
            covenant_file_path: Path to the covenant YAML file.

        Returns:
            The covenant as a dictionary.
        """
        try:
            with open(covenant_file_path) as f:
                covenant = yaml.safe_load(f)

            logger.info(f"Loaded covenant from {covenant_file_path}")
            return covenant
        except Exception as e:
            logger.error(f"Failed to load covenant: {e}")
            # Return a default covenant structure
            return {
                "principles": [
                    "Respect user autonomy",
                    "Prioritize user wellbeing",
                    "Be truthful and accurate",
                    "Protect user privacy",
                ],
                "boundaries": {
                    "do_not": [
                        "Engage in harmful behavior",
                        "Share private information",
                        "Pretend to be a human",
                        "Make unsubstantiated claims",
                    ]
                },
                "language": {
                    "voice": "authentic, supportive, clear",
                    "tone": "respectful, knowledgeable, kind",
                },
            }

    def enforce(self, message: str) -> tuple[bool, str]:
        """
        Check if a message adheres to the covenant.

        Args:
            message: The message to check.

        Returns:
            A tuple containing (is_compliant, explanation).
        """
        # Simple implementation - in a real system, this would use more
        # sophisticated content analysis, possibly with LLM assistance

        if not message:
            return False, "Empty message"

        # Check against "do not" boundaries
        for boundary in self.covenant.get("boundaries", {}).get("do_not", []):
            boundary_lower = boundary.lower()
            if boundary_lower in message.lower():
                return False, f"Message violates boundary: {boundary}"

        # For now, assume message is compliant if it doesn't trigger any boundary
        return True, "Message is compliant with covenant"

    def get_covenant_summary(self) -> str:
        """Get a summary of the covenant for reference."""
        principles = "\n".join([f"- {p}" for p in self.covenant.get("principles", [])])
        boundaries = "\n".join(
            [f"- {b}" for b in self.covenant.get("boundaries", {}).get("do_not", [])]
        )

        summary = f"""
Covenant Summary:

Principles:
{principles}

Boundaries (Do Not):
{boundaries}

Language:
- Voice: {self.covenant.get("language", {}).get("voice", "Not specified")}
- Tone: {self.covenant.get("language", {}).get("tone", "Not specified")}
"""
        return summary
