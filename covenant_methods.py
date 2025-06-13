"""
Additional methods for CovenantEnforcer to support the goal framework
"""


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
        word in text.lower() for word in ["learn", "understand", "knowledge", "insight"]
    ):
        scores["wisdom"] += 0.1

    if any(word in text.lower() for word in ["help", "assist", "support", "care"]):
        scores["compassion"] += 0.1

    if any(word in text.lower() for word in ["accuracy", "valid", "honest", "correct"]):
        scores["truth"] += 0.1

    # Cap scores at 1.0
    return {k: min(v, 1.0) for k, v in scores.items()}
