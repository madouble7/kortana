import os
from langchain.agents import initialize_agent, Tool
from langchain_openai import OpenAI  # updated import for compatibility

grok_llm = OpenAI(model="grok-3-mini", api_key=os.getenv("XAI_API_KEY"))

tools = [
    Tool(name="search", func=lambda q: "TODO: integrate docs search", description="Search docs"),
    # add FileSystem, Git tools here...
]

dev_agent = initialize_agent(tools, grok_llm, agent_type="zero-shot-react-description", verbose=True)

def execute_dev_task(desc: str) -> str:
    prompt = f"You are Kor'tana's dev agent. Task: {desc}. Break it down, implement, test."
    return dev_agent.run(prompt) 