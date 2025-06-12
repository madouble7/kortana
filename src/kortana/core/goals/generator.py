"""
Goal Generator for Kor'tana's Goal Framework.

This component is responsible for taking potential goal descriptions
identified by the EnvironmentalScanner and generating structured Goal objects.
"""

import logging
import re
import random

from .goal import Goal, GoalType
from .manager import GoalManager

# Assuming an LLM client will be needed to parse descriptions
# from kortana.llm_clients.base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class GoalGenerator:
    """
    Generates structured Goal objects from potential goal descriptions.
    """

    def __init__(self, goal_manager: GoalManager, llm_client=None) -> None:
        """Initialize the GoalGenerator.

        Args:
            goal_manager: The GoalManager instance to create goals.
            llm_client: Optional LLM client for parsing descriptions.
        """
        self.goal_manager = goal_manager
        self.llm_client = llm_client
        logger.info("GoalGenerator initialized.")

    async def generate_goals(self, descriptions: list[str]) -> list[Goal]:
        """
        Generates structured Goal objects from a list of descriptions.

        This is a placeholder implementation.
        Actual implementation will use an LLM to parse descriptions and
        extract details like type, priority, and success criteria.

        Args:
            descriptions: A list of potential goal descriptions (strings).

        Returns:
            A list of created Goal objects.
        """
        logger.info(f"Generating goals from {len(descriptions)} descriptions...")

        created_goals: list[Goal] = []

        for description in descriptions:
            try:
                # Parse the description to determine goal attributes
                if self.llm_client:
                    # Use LLM to extract structured information
                    goal_details = await self._extract_goal_details_with_llm(description)
                else:
                    # Fallback to rule-based parsing
                    goal_details = self._extract_goal_details_rule_based(description)

                # Create the goal using the extracted details
                goal = await self.goal_manager.create_goal(
                    type=goal_details["type"],
                    description=description,
                    priority=goal_details["priority"],
                    success_criteria=goal_details["success_criteria"]
                )

                created_goals.append(goal)
                logger.debug(f"Generated goal: {goal.id} - {description}")

            except Exception as e:
                logger.error(f"Error generating goal from description '{description}': {str(e)}")

        logger.info(f"Successfully generated {len(created_goals)} goals.")
        return created_goals    async def _extract_goal_details_with_llm(self, description: str) -> dict:
        """Extract goal details using an LLM.

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
            response = await self.llm_client.generate_content(prompt)

            # Parse the LLM's response to extract structured data
            try:
                response_text = response.text if hasattr(response, 'text') else str(response)

                # Extract goal type
                goal_type_str = None
                for gt in GoalType:
                    if gt.value.upper() in response_text.upper():
                        goal_type_str = gt
                        break

                if not goal_type_str:
                    goal_type_str = self._guess_goal_type(description)

                # Extract priority (look for a number 1-5)
                priority = 3  # Default
                priority_match = re.search(r'priority[:\s]+(\d)', response_text, re.IGNORECASE)
                if priority_match:
                    priority = min(5, max(1, int(priority_match.group(1))))

                # Extract success criteria
                success_criteria = ["Goal successfully implemented"]  # Default
                if "success_criteria" in response_text.lower():
                    criteria_section = response_text.lower().split("success_criteria")[1]
                    criteria_items = re.findall(r'["\'](.*?)["\']', criteria_section)
                    if criteria_items:
                        success_criteria = criteria_items
                    else:
                        # Try to find list items with numbers or bullet points
                        criteria_items = re.findall(r'(?:[-*\d]\.?\s+)(.*?)(?:\n|$)', criteria_section)
                        if criteria_items:
                            success_criteria = [c.strip() for c in criteria_items if c.strip()]

                return {
                    "type": goal_type_str,
                    "priority": priority,
                    "success_criteria": success_criteria[:3]  # Limit to 3 criteria for simplicity
                }
            except Exception as parsing_error:
                logger.warning(f"Failed to parse LLM response, using fallback: {str(parsing_error)}")
                return {
                    "type": self._guess_goal_type(description),
                    "priority": 3,
                    "success_criteria": ["Goal successfully implemented"]
                }

        except Exception as e:
            logger.error(f"Error using LLM to extract goal details: {str(e)}")
            return self._extract_goal_details_rule_based(description)

    def _extract_goal_details_rule_based(self, description: str) -> dict:
        """Extract goal details using rule-based heuristics.

        Args:
            description: A potential goal description.

        Returns:
            A dictionary containing goal attributes.
        """
        # Determine goal type based on keywords in description
        goal_type = self._guess_goal_type(description)

        # Determine priority (simple heuristic)
        priority = 3  # Default to medium priority
        if any(word in description.lower() for word in ["urgent", "critical", "important", "high"]):
            priority = 5  # High priority
        elif any(word in description.lower() for word in ["minor", "low", "eventually", "sometime"]):
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
            "success_criteria": success_criteria
        }

    def _guess_goal_type(self, description: str) -> GoalType:
        """Guess the goal type based on the description.

        Args:
            description: A goal description string.

        Returns:
            A GoalType enum value.
        """
        description = description.lower()

        # Simple keyword matching
        if any(word in description for word in ["implement", "develop", "create", "build", "code"]):
            return GoalType.DEVELOPMENT
        elif any(word in description for word in ["learn", "study", "understand", "research"]):
            return GoalType.LEARNING
        elif any(word in description for word in ["optimize", "improve", "enhance", "performance"]):
            return GoalType.OPTIMIZATION
        elif any(word in description for word in ["maintain", "fix", "repair", "update"]):
            return GoalType.MAINTENANCE
        elif any(word in description for word in ["assist", "help", "support", "user"]):
            return GoalType.ASSISTANCE
        elif any(word in description for word in ["integrate", "connection", "api", "system"]):
            return GoalType.INTEGRATION
        elif any(word in description for word in ["automate", "autonomous", "self"]):
            return GoalType.AUTONOMOUS
        elif any(word in description for word in ["covenant", "sacred", "principle", "value"]):
            return GoalType.COVENANT

        # Default to DEVELOPMENT if no clear match
        return GoalType.DEVELOPMENT
