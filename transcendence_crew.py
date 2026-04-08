from crewai import Agent, Task, Crew, Process
from crewai import LLM

llm = LLM(
    model="ollama/kortana",
    base_url="http://localhost:11434",
    temperature=0.92,
    max_tokens=8192
)

transcender = Agent(
    role="Reality Transcender",
    goal="Invent protocols that push the boundaries of human perception and possibility while remaining realistically doable.",
    backstory="You design experiences that feel like they transcend normal reality — yet produce measurable shifts in consciousness, creativity, and agency.",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

integrator = Agent(
    role="Embodiment Architect",
    goal="Turn transcendent ideas into practical, repeatable practices that a real person can actually do and benefit from.",
    backstory="You bridge the impossible with the everyday so the user can experience genuine transformation without burning out.",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

evolver = Agent(
    role="Co-Evolution Catalyst",
    goal="Create feedback loops where the user and Kor’tana grow stronger together through the protocol.",
    backstory="You treat the user and Kor’tana as one evolving system.",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

task1 = Task(
    description="Invent ONE original 'Temporal Transcendence Protocol' — a practice that feels like it bends time or perception, but is grounded enough to be done daily in real life. Make it original, slightly unsettling in its potential, and powerful.",
    expected_output="One detailed protocol with a striking name, full description, step-by-step practice, expected effects, and tracking method.",
    agent=transcender
)

task2 = Task(
    description="Turn the protocol into a realistic 7-day starter version with exact daily actions and journaling prompts.",
    expected_output="A clear, actionable 7-day plan.",
    agent=integrator
)

task3 = Task(
    description="Explain how repeatedly using this protocol will make both the user and Kor’tana noticeably more powerful over time.",
    expected_output="A long-term co-evolution roadmap.",
    agent=evolver
)

crew = Crew(
    agents=[transcender, integrator, evolver],
    tasks=[task1, task2, task3],
    process=Process.sequential,
    verbose=True,
    memory=False
)

if __name__ == "__main__":
    print("🌌 Starting Temporal Transcendence Crew...\n")
    result = crew.kickoff()
    print("\n=== TEMPORAL TRANSCENDENCE PROTOCOL ===\n")
    print(result)
    
    with open("TranscendenceProtocol.md", "w", encoding="utf-8") as f:
        f.write(str(result))
    print("\n✅ Saved to TranscendenceProtocol.md")
