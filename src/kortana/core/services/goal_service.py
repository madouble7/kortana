from src.kortana.core.goal_framework import Goal
from src.kortana.modules.memory_core.services import MemoryCoreService

class GoalService:
    def __init__(self, memory_service: MemoryCoreService):
        self.memory_service = memory_service

    async def create_goal(self, goal: Goal):
        # Save goal to memory system
        await self.memory_service.save_goal(goal)
        return goal

    async def get_goal(self, goal_id):
        # Load goal from memory system
        goal_data = await self.memory_service.load_goal(goal_id)
        if goal_data:
            return Goal(**goal_data)
        return None

    async def update_goal(self, goal: Goal):
        # Update goal in memory system
        await self.memory_service.save_goal(goal)
        return goal

    async def delete_goal(self, goal_id):
        # Delete goal from memory system
        await self.memory_service.delete_goal(goal_id)
        return True
