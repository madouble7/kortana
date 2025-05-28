from agents.memory_agent import MemoryAgent
import os

class AgentManager:
    def __init__(self):
        self.agents = {
            "memory": MemoryAgent(
                pinecone_api_key=os.getenv("PINECONE_API_KEY"),
                pinecone_env=os.getenv("PINECONE_ENV")
            ),
            # ... other agents
        }

    def run(self, name: str, **kwargs):
        agent = self.agents.get(name)
        if not agent:
            raise ValueError(f"No agent named {name}")
        plan = agent.plan(kwargs.get("text", ""))
        agent.execute(plan)
        return agent.verify(kwargs.get("verify_query", ""))