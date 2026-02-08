"""
RPG Assistant for Kor'tana
Assists with tabletop RPG gameplay
"""

from typing import Any


class RPGAssistant:
    """Service for tabletop RPG assistance"""

    def __init__(self):
        self.campaigns: dict[str, dict[str, Any]] = {}
        self.active_campaign: str | None = None

    def create_campaign(self, name: str, system: str = "D&D 5e") -> dict[str, Any]:
        """
        Create a new RPG campaign

        Args:
            name: Campaign name
            system: RPG system (e.g., 'D&D 5e', 'Pathfinder')

        Returns:
            Campaign information
        """
        campaign_id = f"campaign_{len(self.campaigns) + 1}"
        self.campaigns[campaign_id] = {
            "id": campaign_id,
            "name": name,
            "system": system,
            "sessions": [],
            "players": [],
            "npcs": [],
        }
        self.active_campaign = campaign_id
        return self.campaigns[campaign_id]

    def add_player(
        self, player_name: str, character_name: str, character_class: str
    ) -> dict[str, Any]:
        """
        Add a player to the active campaign

        Args:
            player_name: Player's real name
            character_name: Character name
            character_class: Character class

        Returns:
            Player information
        """
        if not self.active_campaign:
            return {"error": "No active campaign"}

        player = {
            "player_name": player_name,
            "character_name": character_name,
            "character_class": character_class,
        }
        self.campaigns[self.active_campaign]["players"].append(player)
        return player

    def roll_dice(self, dice_notation: str) -> dict[str, Any]:
        """
        Roll dice using standard notation (e.g., '2d6', '1d20+5')

        Args:
            dice_notation: Dice notation

        Returns:
            Roll results
        """
        import random
        import re

        # Parse dice notation (e.g., 2d6+3 or 2d6-2)
        match = re.match(r"(\d+)d(\d+)([\+\-]\d+)?", dice_notation)
        if not match:
            return {"error": "Invalid dice notation"}

        num_dice = int(match.group(1))
        die_size = int(match.group(2))
        modifier_str = match.group(3)
        modifier = int(modifier_str) if modifier_str else 0

        rolls = [random.randint(1, die_size) for _ in range(num_dice)]
        total = sum(rolls) + modifier

        return {
            "notation": dice_notation,
            "rolls": rolls,
            "modifier": modifier,
            "total": total,
        }

    def generate_npc(self, npc_type: str = "generic") -> dict[str, Any]:
        """
        Generate a random NPC

        Args:
            npc_type: Type of NPC to generate

        Returns:
            NPC information
        """
        import random

        names = ["Aldric", "Brenna", "Cedric", "Diana", "Erik", "Fiona"]
        traits = ["brave", "cunning", "wise", "mysterious", "cheerful", "grumpy"]

        npc = {
            "name": random.choice(names),
            "type": npc_type,
            "trait": random.choice(traits),
        }

        if self.active_campaign:
            self.campaigns[self.active_campaign]["npcs"].append(npc)

        return npc

    def get_campaign_info(self) -> dict[str, Any]:
        """
        Get information about the active campaign

        Returns:
            Campaign information
        """
        if not self.active_campaign:
            return {"error": "No active campaign"}

        return self.campaigns[self.active_campaign]
