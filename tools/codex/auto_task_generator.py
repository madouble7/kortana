#!/usr/bin/env python3
"""Automatic Codex Task Generator for Kor'tana.

This utility parses `TASKS.md` for tasks assigned to Kor'tana and uses
Google's Generative AI to produce Codex task prompt files and JSON task
configurations. Generated tasks are saved under `tools/codex/tasks/` and
prompts under `tools/codex/prompts/`.

Requirements:
    - google-generativeai
    - python-dotenv (for loading .env files)
    - GEMINI_API_KEY or GOOGLE_API_KEY in environment or .env

This script is intentionally lightweight. It generates one Codex task per
assignment found in `TASKS.md` that has not already been created.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import google.generativeai as genai  # type: ignore
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TASKS_MD = PROJECT_ROOT / "TASKS.md"
TASKS_DIR = PROJECT_ROOT / "tools" / "codex" / "tasks"
PROMPTS_DIR = PROJECT_ROOT / "tools" / "codex" / "prompts"


def slugify(text: str) -> str:
    """Create a filesystem-friendly slug from text."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return slug[:50]


def extract_kortana_tasks() -> list[str]:
    """Return task descriptions assigned to Kor'tana from TASKS.md."""
    content = TASKS_MD.read_text(encoding="utf-8")
    pattern = r"\*\*ASSIGN TO KOR'TANA:\*\*\s*\"(.*?)\""
    return re.findall(pattern, content, flags=re.DOTALL)


def generate_prompt(description: str) -> str:
    """Generate a Codex prompt for the given task description."""
    # Load API keys from a .env file if present
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY must be set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")
    system_prompt = (
        "You are a helpful assistant that writes concise prompts for a code\n"
        "generation tool named Codex. The prompt should guide Codex to fulfill\n"
        "the following task inside the Kor'tana project."\
    )
    resp = model.generate_content([system_prompt, description])
    prompt_text = resp.candidates[0].content if resp.candidates else ""
    return str(prompt_text).strip()


def write_task_files(slug: str, description: str, prompt: str) -> None:
    """Create prompt and task JSON files for the new task."""
    prompt_path = PROMPTS_DIR / f"{slug}.md"
    task_path = TASKS_DIR / f"{slug}.json"

    prompt_path.write_text(prompt, encoding="utf-8")

    task_config = {
        "task_name": slug,
        "description": description,
        "target_files": [],
        "output_file": "",
        "prompt_file": str(prompt_path.relative_to(PROJECT_ROOT)),
        "prompt_params": {},
        "validation_checks": [],
    }
    task_path.write_text(json.dumps(task_config, indent=4), encoding="utf-8")
    print(f"Created task: {task_path}")


def main() -> None:
    tasks = extract_kortana_tasks()
    for description in tasks:
        slug = slugify(description)
        task_file = TASKS_DIR / f"{slug}.json"
        if task_file.exists():
            print(f"Skipping existing task: {slug}")
            continue
        try:
            prompt = generate_prompt(description)
        except Exception as e:  # pylint: disable=broad-except
            print(f"Failed to generate prompt for '{slug}': {e}")
            continue
        write_task_files(slug, description, prompt)


if __name__ == "__main__":
    main()
