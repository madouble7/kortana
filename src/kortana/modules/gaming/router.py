"""
Gaming API Router for Kor'tana
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .rpg_assistant import RPGAssistant
from .storytelling_engine import StoryGenre, StorytellingEngine

router = APIRouter(prefix="/api/gaming", tags=["gaming"])

storytelling_engine = StorytellingEngine()
rpg_assistant = RPGAssistant()


# Storytelling endpoints
class StartStoryRequest(BaseModel):
    genre: StoryGenre
    setting: str


class ContinueStoryRequest(BaseModel):
    player_action: str


class AddCharacterRequest(BaseModel):
    name: str
    description: str


@router.post("/story/start")
async def start_story(request: StartStoryRequest):
    """Start a new interactive story"""
    try:
        story = storytelling_engine.start_story(request.genre, request.setting)
        return story
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/story/continue")
async def continue_story(request: ContinueStoryRequest):
    """Continue the current story"""
    try:
        result = storytelling_engine.continue_story(request.player_action)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/story/character")
async def add_character(request: AddCharacterRequest):
    """Add a character to the story"""
    try:
        character = storytelling_engine.add_character(request.name, request.description)
        return character
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/story/summary")
async def get_story_summary():
    """Get summary of current story"""
    try:
        summary = storytelling_engine.get_story_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# RPG endpoints
class CreateCampaignRequest(BaseModel):
    name: str
    system: str = "D&D 5e"


class AddPlayerRequest(BaseModel):
    player_name: str
    character_name: str
    character_class: str


class RollDiceRequest(BaseModel):
    dice_notation: str


@router.post("/rpg/campaign")
async def create_campaign(request: CreateCampaignRequest):
    """Create a new RPG campaign"""
    try:
        campaign = rpg_assistant.create_campaign(request.name, request.system)
        return campaign
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rpg/player")
async def add_player(request: AddPlayerRequest):
    """Add a player to the campaign"""
    try:
        player = rpg_assistant.add_player(
            request.player_name, request.character_name, request.character_class
        )
        return player
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rpg/roll")
async def roll_dice(request: RollDiceRequest):
    """Roll dice using standard notation"""
    try:
        result = rpg_assistant.roll_dice(request.dice_notation)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rpg/npc")
async def generate_npc(npc_type: str = "generic"):
    """Generate a random NPC"""
    try:
        npc = rpg_assistant.generate_npc(npc_type)
        return npc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rpg/campaign")
async def get_campaign_info():
    """Get active campaign information"""
    try:
        campaign = rpg_assistant.get_campaign_info()
        return campaign
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
