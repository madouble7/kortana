"""
Test Kor'tana's Autonomous Development Engine
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from brain import ChatEngine
from ade_coordinator import ADECoordinator

async def test_autonomous_development():
    """Test autonomous development capabilities"""
    print("🔥 Testing Kor'tana's Autonomous Development Engine")
    
    # Initialize ChatEngine
    engine = ChatEngine()
    coordinator = ADECoordinator(engine)
    
    # Test goals
    test_goals = [
        "Analyze the current codebase structure and suggest improvements",
        "Create comprehensive documentation for the memory_manager module",
        "Enhance error handling in the llm_clients factory"
    ]
    
    print(f"📋 Test goals: {test_goals}")
    
    # Add goals to system
    for goal in test_goals:
        coordinator.add_development_goal(goal)
    
    # Run autonomous session
    print("🚀 Starting autonomous development session...")
    results = await coordinator.start_autonomous_session(test_goals)
    
    print("✅ Autonomous development session completed!")
    print(f"📊 Results: {results}")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_autonomous_development())
