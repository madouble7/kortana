"""Development agent module for autonomous development tasks.

This module implements the development agent that handles coding tasks,
testing, and project implementation using XAI's Grok model.
"""

import os

from langchain.agents import Tool, initialize_agent
from langchain_openai.chat_models import ChatOpenAI  # Use ChatOpenAI for agents

# Use the XAIClient directly instead of LangChain's ChatOpenAI wrapper
from .llm_clients.xai_client import XAIClient

grok_llm = ChatOpenAI(
    model="grok-3-mini",  # Or the specific model name for XAI's API
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1",  # Point to the XAI API endpoint
    # temperature=0.7 # Optional: set default temperature
)
tools = [
    Tool(
        name="search",
        func=lambda q: "TODO: integrate docs search",
        description="Search docs",
    ),
    # add FileSystem, Git tools here...
]

# Initialize the XAIClient directly
xai_client = XAIClient(model_name="grok-3-mini")

# The LangChain agent initialization needs a LangChain-compatible LLM.
# We will keep the LangChain agent structure but potentially wrap the XAIClient
# or ensure XAIClient can be used directly if it has a compatible interface.
# For now, keep the LangChain ChatOpenAI wrapper pointing to XAI API.
dev_agent = initialize_agent(
    tools, grok_llm, agent_type="zero-shot-react-description", verbose=True
)


def execute_dev_task(desc: str) -> str:
    """Execute a development task using the dev agent.

    Args:
        desc: Description of the development task to execute

    Returns:
        Result of the development task execution
    """
    prompt = (
        f"You are Kor'tana's dev agent. Task: {desc}. Break it down, implement, test."
    )
    return dev_agent.run(prompt)
