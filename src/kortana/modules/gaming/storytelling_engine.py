"""
Storytelling Engine for Kor'tana
Generates interactive narratives and story elements
"""

from enum import Enum
from typing import Any, Optional


class StoryGenre(str, Enum):
    FANTASY = "fantasy"
    SCIFI = "scifi"
    MYSTERY = "mystery"
    HORROR = "horror"
    ADVENTURE = "adventure"


class StorytellingEngine:
    """Service for interactive storytelling"""

    def __init__(self):
        self.current_story: Optional[dict[str, Any]] = None
        self.story_history: list[dict[str, Any]] = []

    def start_story(self, genre: StoryGenre, setting: str) -> dict[str, Any]:
        """
        Start a new interactive story

        Args:
            genre: Story genre
            setting: Story setting description

        Returns:
            Initial story state
        """
        self.current_story = {
            "genre": genre,
            "setting": setting,
            "scenes": [],
            "characters": [],
            "current_scene": "You find yourself at the beginning of an epic tale...",
        }
        return self.current_story

    def continue_story(self, player_action: str) -> dict[str, Any]:
        """
        Continue the story based on player action

        Args:
            player_action: Player's chosen action

        Returns:
            Updated story state
        """
        if not self.current_story:
            return {"error": "No active story. Start a new story first."}

        # Simple continuation logic
        self.current_story["scenes"].append(
            {"action": player_action, "result": f"As you {player_action}..."}
        )

        return {
            "previous_action": player_action,
            "current_scene": f"Your action leads to new developments...",
            "choices": ["Investigate further", "Retreat", "Talk to someone"],
        }

    def add_character(self, name: str, description: str) -> dict[str, Any]:
        """
        Add a character to the story

        Args:
            name: Character name
            description: Character description

        Returns:
            Character information
        """
        if not self.current_story:
            return {"error": "No active story"}

        character = {"name": name, "description": description}
        self.current_story["characters"].append(character)
        return character

    def get_story_summary(self) -> dict[str, Any]:
        """
        Get summary of current story

        Returns:
            Story summary
        """
        if not self.current_story:
            return {"error": "No active story"}

        return {
            "genre": self.current_story["genre"],
            "setting": self.current_story["setting"],
            "scenes_count": len(self.current_story["scenes"]),
            "characters_count": len(self.current_story["characters"]),
        }
