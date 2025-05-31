import os

from agents.memory_agent import MemoryAgent


class AgentManager:
    def __init__(self):
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        pinecone_env = os.getenv("PINECONE_ENV")

        if not pinecone_api_key or not pinecone_env:
            raise ValueError(
                "PINECONE_API_KEY and PINECONE_ENV environment variables must be set"
            )

        self.agents = {
            "memory": MemoryAgent(
                pinecone_api_key=pinecone_api_key, pinecone_env=pinecone_env
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
