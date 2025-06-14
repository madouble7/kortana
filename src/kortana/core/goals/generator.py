"""
Goal Generator for Kor'tana's Goal Framework.

This component is responsible for taking potential goal descriptions
identified by the EnvironmentalScanner and generating structured Goal objects.
"""

import logging
import re

from ...services.llm_service import llm_service
from .goal import Goal, GoalType
from .manager import GoalManager

logger = logging.getLogger(__name__)


class GoalGenerator:
    """
    Generates structured Goal objects from potential goal descriptions.
    """

    def __init__(self, goal_manager: GoalManager) -> None:
        """
        Initialize the GoalGenerator.

        Args:
            goal_manager: The GoalManager instance to create goals.
        """
        self.goal_manager = goal_manager

    async def generate_goals(self, descriptions: list[str]) -> list[Goal]:
        """
        Generate structured Goal objects from a list of potential descriptions.

        Args:
            descriptions: A list of strings, each a potential goal description.

        Returns:
            A list of generated Goal objects.
        """
        created_goals = []
        logger.info(
            f"Attempting to generate goals from {len(descriptions)} descriptions."
        )

        for description in descriptions:
            logger.debug(f"Processing description: '{description}'")
            try:
                # First, try to extract details using the LLM
                goal_details = await self._extract_goal_details_with_llm(description)

                # If LLM extraction fails or returns incomplete data, fallback to rule-based
                if (
                    not goal_details
                    or not goal_details.get("type")
                    or not goal_details.get("priority")
                ):
                    logger.warning(
                        f"LLM extraction failed or incomplete for '{description}'. Falling back to rule-based."
                    )
                    goal_details = self._extract_goal_details_rule_based(description)

                # Ensure goal_details has required keys after fallback
                if (
                    not goal_details
                    or not goal_details.get("type")
                    or not goal_details.get("priority")
                ):
                    logger.error(
                        f"Failed to extract sufficient goal details for '{description}' even with fallback."
                    )
                    continue  # Skip this description if details are still missing

                # Create the Goal object
                goal = await self.goal_manager.create_goal(
                    type=goal_details["type"],
                    description=description,
                    priority=goal_details["priority"],
                    success_criteria=goal_details.get(
                        "success_criteria", ["Goal successfully implemented"]
                    ),
                )
                created_goals.append(goal)
                logger.debug(f"Generated goal: {goal.id} - {description}")
            except Exception as e:
                logger.error(
                    f"Error generating goal from description '{description}': {str(e)}",
                    exc_info=True,
                )

        logger.info(f"Successfully generated {len(created_goals)} goals.")
        return created_goals

    async def _extract_goal_details_with_llm(self, description: str) -> dict:
        """
        Extract goal details using an LLM.

        Args:
            description: A potential goal description.

        Returns:
            A dictionary containing goal attributes.
        """
        prompt = f"""
        Based on the following goal description, extract the following information:
        1. Goal type (one of: DEVELOPMENT, LEARNING, OPTIMIZATION, MAINTENANCE, ASSISTANCE, INTEGRATION, AUTONOMOUS, COVENANT)
        2. Priority (1-5, where 5 is highest priority)
        3. Success criteria (list of concrete conditions that indicate the goal has been achieved)

        Goal description: "{description}"

        Return your response as structured data with type, priority, and success_criteria.
        """

        try:
            # Use llm_service directly
            # Assuming llm_service has a generate_response method that returns a dict-like object
            response = await llm_service.generate_response(prompt)

            # Parse the LLM's response to extract structured data
            # Access content using .get('content') as response is likely a dict
            response_text = (
                response.get("content", "")
                if isinstance(response, dict)
                else str(response)
            )

            # Extract goal type
            goal_type_str = None
            # Use next with a generator expression for simplification
            goal_type_str = next(
                (gt for gt in GoalType if gt.value.upper() in response_text.upper()),
                None,
            )

            if not goal_type_str:
                goal_type_str = self._guess_goal_type(description)

            # Extract priority (look for a number 1-5)
            priority = 3  # Default
            priority_match = re.search(
                r"priority[:\s]+(\d)", response_text, re.IGNORECASE
            )
            if priority_match:
                priority = min(5, max(1, int(priority_match.group(1))))

            # Extract success criteria
            success_criteria = ["Goal successfully implemented"]  # Default
            if "success_criteria" in response_text.lower():
                criteria_section = response_text.lower().split("success_criteria")[1]
                # Use named expression for simplification
                if criteria_items := re.findall(r'["\'](.*?)["\']', criteria_section):
                    success_criteria = criteria_items
                else:
                    # Try to find list items with numbers or bullet points
                    # Use named expression for simplification
                    if criteria_items := re.findall(
                        r"(?:[-*\d]\.?\s+)(.*?)(?:\n|$)", criteria_section
                    ):
                        success_criteria = [
                            c.strip() for c in criteria_items if c.strip()
                        ]

            return {
                "type": goal_type_str,
                "priority": priority,
                "success_criteria": success_criteria[
                    :3
                ],  # Limit to 3 criteria for simplicity
            }

        except Exception as e:  # Catch any exception during LLM call or parsing
            logger.warning(
                f"Failed to extract goal details with LLM: {str(e)}. Falling back to rule-based.",
                exc_info=True,
            )
            return self._extract_goal_details_rule_based(description)

    def _extract_goal_details_rule_based(self, description: str) -> dict:
        """
        Extract goal details using rule-based heuristics.

        Args:
            description: A potential goal description.

        Returns:
            A dictionary containing goal attributes.
        """
        # Determine goal type based on keywords in description
        goal_type = self._guess_goal_type(description)

        # Determine priority (simple heuristic)
        priority = 3  # Default to medium priority
        if any(
            word in description.lower()
            for word in ["urgent", "critical", "important", "high"]
        ):
            priority = 5  # High priority
        elif any(
            word in description.lower()
            for word in ["minor", "low", "eventually", "sometime"]
        ):
            priority = 1  # Low priority

        # Generate simple success criteria
        success_criteria = [f"Successfully {description.strip('.')}"]

        # Additional success criteria based on goal type
        if goal_type == GoalType.DEVELOPMENT:
            success_criteria.append("Code written, tested, and documented")
        elif goal_type == GoalType.OPTIMIZATION:
            success_criteria.append("Performance improved with benchmarks")
        elif goal_type == GoalType.MAINTENANCE:
            success_criteria.append("System stability maintained or improved")

        return {
            "type": goal_type,
            "priority": priority,
            "success_criteria": success_criteria,
        }

    def _guess_goal_type(self, description: str) -> GoalType:
        """
        Guess the goal type based on the description.

        Args:
            description: A goal description string.

        Returns:
            A GoalType enum value.
        """
        description = description.lower()

        # Simple keyword matching
        if any(
            word in description
            for word in ["implement", "develop", "create", "build", "code"]
        ):
            return GoalType.DEVELOPMENT
        elif any(
            word in description for word in ["learn", "study", "understand", "research"]
        ):
            return GoalType.LEARNING
        elif any(
            word in description
            for word in ["optimize", "improve", "enhance", "performance"]
        ):
            return GoalType.OPTIMIZATION
        elif any(
            word in description for word in ["maintain", "fix", "repair", "update"]
        ):
            return GoalType.MAINTENANCE
        elif any(word in description for word in ["assist", "help", "support", "user"]):
            return GoalType.ASSISTANCE
        elif any(
            word in description for word in ["integrate", "connection", "api", "system"]
        ):
            return GoalType.INTEGRATION
        elif any(word in description for word in ["automate", "autonomous", "self"]):
            return GoalType.AUTONOMOUS
        elif any(
            word in description for word in ["covenant", "sacred", "principle", "value"]
        ):
            return GoalType.COVENANT

        # Default to DEVELOPMENT if no clear match
        return GoalType.DEVELOPMENT
