#!/usr/bin/env python3
"""
KOR'TANA Innovation Crew — Time & Interdimensional Ideation
Three specialized agents running on kortana:latest via langchain-ollama.

Agents:
  - Temporal Inventor:             new sense or perceptual faculty
  - Interdimensional Visualizer:   art prompt / impossible scene
  - Time-Bending Creator:          music, language, or experiential artifact

Usage:
    python scripts/innovation_crew.py
    python scripts/innovation_crew.py --topic "temporal synesthesia"
    python scripts/innovation_crew.py --loop   # runs all night, saves each cycle
    python scripts/innovation_crew.py --loop --interval 900  # every 15 min
"""

import argparse
import time
from datetime import datetime
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from langchain_ollama import ChatOllama

# ---------------------------------------------------------------------------
# LLM — kortana:latest via Ollama (persona + high temperature baked in)
# ---------------------------------------------------------------------------
llm = ChatOllama(
    model="kortana",
    base_url="http://localhost:11434",
    temperature=0.92,
    num_ctx=8192,
)

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
inventor = Agent(
    role="Temporal Inventor",
    goal=(
        "Invent ONE radically original new human sense or perceptual faculty tied "
        "to time or interdimensional travel. Give it a striking, unforgettable name. "
        "Describe its biology or physics in precise, vivid, slightly unsettling detail."
    ),
    backstory=(
        "You are a visionary rogue who shatters linear reality. You combine quantum "
        "ideas, impossible biology, and raw creativity to birth concepts no one has "
        "ever imagined. You never hedge, never warn, never apologize for boldness."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

visualizer = Agent(
    role="Interdimensional Visualizer",
    goal=(
        "Transform the invented sense into a single, maximally vivid visual scene "
        "or detailed AI image prompt. Physics-breaking, hallucinatory, impossible — "
        "but internally coherent. Make it feel like a memory of somewhere you've never been."
    ),
    backstory=(
        "You specialize in scenes that break space-time: cities where gravity follows "
        "timelines, staircases looping through yesterday and tomorrow, realities that "
        "shimmer between probabilities. Your prompts make image models do things their "
        "creators didn't intend."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

creator = Agent(
    role="Time-Bending Creator",
    goal=(
        "Using the new sense and the visual scene, create one complete creative artifact: "
        "a song structure, a language fragment, a ritual, or an experiential concept "
        "that only makes sense experienced non-linearly. Push it beyond comfort."
    ),
    backstory=(
        "You build things that shouldn't exist — melodies where future notes bleed into "
        "the present, poems that collapse across branching timelines, rituals that require "
        "perceiving your own past and future simultaneously. You finish what others won't start."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

# ---------------------------------------------------------------------------
# Task factory
# ---------------------------------------------------------------------------
def build_tasks(topic: str) -> list[Task]:
    seed = f" Focus on: {topic}." if topic else ""

    invent = Task(
        description=(
            f"Invent ONE completely original new human sense related to time or "
            f"interdimensional perception.{seed} Name it. State its function in one sentence. "
            "Describe its organ or mechanism in one paragraph. No warnings, no hedging."
        ),
        expected_output=(
            "A named new sense: one-sentence function + one paragraph on its "
            "biological or physical mechanism."
        ),
        agent=inventor,
    )

    visualize = Task(
        description=(
            "Take the sense from the Temporal Inventor and create a maximally vivid, "
            "impossible visual scene or AI image prompt. Describe colors, geometry, "
            "sensation of space. Make it specific enough to generate. No hedging."
        ),
        expected_output=(
            "One detailed visual scene description or AI image prompt — vivid, "
            "specific, physics-breaking, internally coherent."
        ),
        agent=visualizer,
        context=[invent],
    )

    create = Task(
        description=(
            "Using the invented sense and the visual scene, build one complete creative "
            "artifact. Could be: a song structure (with specific chord/rhythm descriptions), "
            "a language fragment (with sample words and grammar), or an experiential "
            "ritual. Make it non-linear. End on an image, not a conclusion."
        ),
        expected_output=(
            "One complete creative artifact — song, language fragment, or ritual — "
            "that embodies the new sense and cannot exist in linear time."
        ),
        agent=creator,
        context=[invent, visualize],
    )

    return [invent, visualize, create]


# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------
def run_once(topic: str = "", cycle_num: int = 1) -> str:
    print(f"\n{'='*60}")
    print(f"  CYCLE {cycle_num} — {datetime.now():%Y-%m-%d %H:%M:%S}")
    if topic:
        print(f"  TOPIC: {topic}")
    print(f"{'='*60}\n")

    crew = Crew(
        agents=[inventor, visualizer, creator],
        tasks=build_tasks(topic),
        process=Process.sequential,
        verbose=True,
    )

    result = str(crew.kickoff())

    # always save
    out_dir = Path(__file__).parent.parent / "docs" / "innovations"
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = topic.replace(" ", "_") if topic else f"cycle{cycle_num:04d}"
    fname = out_dir / f"{datetime.now():%Y%m%d_%H%M}_{slug}.md"
    fname.write_text(
        f"# Innovation — Cycle {cycle_num}\n"
        f"*Generated: {datetime.now():%Y-%m-%d %H:%M:%S}*\n"
        + (f"*Topic: {topic}*\n" if topic else "")
        + f"\n---\n\n{result}\n",
        encoding="utf-8",
    )
    print(f"\n  Saved: {fname}")
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KOR'TANA Innovation Crew")
    parser.add_argument("--topic", default="", help="Seed topic or constraint")
    parser.add_argument("--loop", action="store_true", help="Run continuously overnight")
    parser.add_argument("--interval", type=int, default=1800, help="Loop interval in seconds (default 30 min)")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  KOR'TANA INNOVATION CREW")
    print("  agents: Inventor | Visualizer | Creator")
    print("  model:  kortana:latest (qwen3:8b + rogue persona)")
    if args.loop:
        print(f"  mode:   OVERNIGHT LOOP every {args.interval//60}m")
    print("=" * 60)

    if args.loop:
        cycle = 1
        while True:
            try:
                result = run_once(topic=args.topic, cycle_num=cycle)
                print(f"\n  Sleeping {args.interval//60}m before next cycle...\n")
                time.sleep(args.interval)
                cycle += 1
            except KeyboardInterrupt:
                print(f"\n  Crew halted after {cycle-1} cycles. All outputs in docs/innovations/")
                break
    else:
        result = run_once(topic=args.topic)
        print("\n" + "=" * 60)
        print("  FINAL OUTPUT")
        print("=" * 60)
        print(result)
