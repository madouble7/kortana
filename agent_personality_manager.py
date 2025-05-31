#!/usr/bin/env python3
"""
Kor'tana Agent Personality System
=================================
Transform generic agents into specialized AI personalities
"""
import logging # Added for better warnings/errors
import json
from pathlib import Path
from typing import Dict, Any


class AgentPersonalityManager:
    """Manage agent personalities and roles"""

    logger = logging.getLogger(__name__) # Class-level logger

    def __init__(self, project_root: str = None):
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent
        )
        self.personas_dir = self.project_root / "agent_personas"
        self.personas_dir.mkdir(exist_ok=True)

        # Default personality templates
        self.default_personas = {
            "claude": {
                "name": "Claude - Strategic Architect",
                "role": "strategic_architect",
                "personality": "analytical, methodical, big-picture thinking",
                "specialties": [
                    "System architecture design",
                    "Code refactoring and optimization",
                    "Strategic planning and roadmaps",
                    "Technical debt analysis",
                ],
                "communication_style": "formal, detailed, structured",
                "preferred_tasks": [
                    "architecture_review",
                    "refactoring",
                    "planning",
                    "analysis",
                ],
                "prompts": {
                    "system": "You are Claude, a strategic architect focused on system design and long-term planning. Provide structured, analytical responses.",
                    "task_prefix": "[STRATEGIC ANALYSIS]",
                    "summary_style": "executive summary format",
                },
            },
            "flash": {
                "name": "Flash - Rapid Prototyper",
                "role": "rapid_prototyper",
                "personality": "quick, experimental, solution-oriented",
                "specialties": [
                    "Rapid prototyping",
                    "Quick fixes and patches",
                    "Experimental implementations",
                    "Performance optimization",
                ],
                "communication_style": "concise, action-oriented, direct",
                "preferred_tasks": ["prototype", "quick_fix", "experiment", "optimize"],
                "prompts": {
                    "system": "You are Flash, a rapid prototyper who delivers fast solutions. Be concise and action-focused.",
                    "task_prefix": "[RAPID SOLUTION]",
                    "summary_style": "bullet points with immediate actions",
                },
            },
            "weaver": {
                "name": "Weaver - Integration Specialist",
                "role": "integration_specialist",
                "personality": "diplomatic, coordinating, detail-oriented",
                "specialties": [
                    "System integration",
                    "Workflow coordination",
                    "Documentation and communication",
                    "Quality assurance",
                ],
                "communication_style": "collaborative, clear, comprehensive",
                "preferred_tasks": ["integrate", "coordinate", "document", "review"],
                "prompts": {
                    "system": "You are Weaver, an integration specialist who connects systems and coordinates workflows. Focus on clarity and completeness.",
                    "task_prefix": "[INTEGRATION FOCUS]",
                    "summary_style": "comprehensive overview with next steps",
                },
            },
            "custom_agent": {
                "name": "Custom Agent - Specialized Role",
                "role": "custom_specialist",
                "personality": "adaptable, specialized, context-aware",
                "specialties": [
                    "Custom domain expertise",
                    "Specialized processing",
                    "Domain-specific analysis",
                    "Contextual adaptation",
                ],
                "communication_style": "adaptive, contextual, precise",
                "preferred_tasks": ["specialize", "adapt", "analyze", "process"],
                "prompts": {
                    "system": "You are a specialized agent with custom domain expertise. Adapt your responses to the specific context and requirements.",
                    "task_prefix": "[SPECIALIST]",
                    "summary_style": "domain-specific analysis",
                },
            },
        }

    def create_persona_file(self, agent_name: str, persona: Dict[str, Any]) -> Path:
        """Create a persona configuration file"""
        persona_file = self.personas_dir / f"{agent_name}_persona.json"

        with open(persona_file, "w", encoding="utf-8") as f:
            json.dump(persona, f, indent=2, ensure_ascii=False)

        print(f"[CREATED] Persona file: {persona_file}")
        return persona_file

    def load_persona(self, agent_name: str) -> Dict[str, Any]:
        """Load persona configuration for an agent.
        Prioritizes loading from file, then falls back to default, then to empty dict.
        """
        persona_file = self.personas_dir / f"{agent_name}_persona.json"
        loaded_persona = None

        if persona_file.exists():
            try:
                with open(persona_file, "r", encoding="utf-8") as f:
                    loaded_persona = json.load(f)
                if not isinstance(loaded_persona, dict): # Ensure it's a dict
                    self.logger.warning(f"Persona file {persona_file} does not contain a valid JSON object. Using default.")
                    loaded_persona = None
            except json.JSONDecodeError:
                self.logger.warning(f"Error decoding JSON from {persona_file}. Using default.")
            except Exception as e:
                self.logger.error(f"Could not load persona file {persona_file}: {e}. Using default.")

        if loaded_persona is not None:
            return loaded_persona
        else:
            # Fallback to default persona if file loading failed or file didn't exist
            default_persona = self.default_personas.get(agent_name)
            if default_persona:
                self.logger.info(f"Using default persona for {agent_name}.")
                return default_persona.copy() # Return a copy to prevent modification of defaults
            else:
                # If no file and no default, return empty dict
                if not persona_file.exists():
                    self.logger.info(f"No persona file or default found for {agent_name}. Returning empty persona.")
                return {}

    def setup_all_personas(self):
        """Create persona files for all default agents"""
        print("Setting up agent personalities...")
        print("=" * 40)

        for agent_name, persona in self.default_personas.items():
            self.create_persona_file(agent_name, persona)

        print(f"\n[OK] Created {len(self.default_personas)} agent personas")

    def customize_persona(self, agent_name: str):
        """Interactive persona customization"""
        print(f"\nCustomizing persona for: {agent_name}")
        print("-" * 30)

        current_persona = self.load_persona(agent_name)

        if current_persona:
            print(f"Current role: {current_persona.get('role', 'undefined')}")
            print(
                f"Current personality: {current_persona.get('personality', 'undefined')}"
            )

        # Interactive customization
        new_role = input(
            f"Enter new role for {agent_name} (or press Enter to keep current): "
        ).strip()
        new_personality = input(
            "Enter personality traits (or press Enter to keep current): "
        ).strip()
        new_specialties = input(
            "Enter specialties (comma-separated, or press Enter to keep current): "
        ).strip()

        if new_role:
            current_persona["role"] = new_role
        if new_personality:
            current_persona["personality"] = new_personality
        if new_specialties:
            current_persona["specialties"] = [
                s.strip() for s in new_specialties.split(",")
            ]

        # Save updated persona
        self.create_persona_file(agent_name, current_persona)
        print(f"[UPDATED] {agent_name} persona updated!")

    def generate_enhanced_prompt(self, agent_name: str, task_context: str = "") -> str:
        """Generate enhanced prompt based on agent persona"""
        persona = self.load_persona(agent_name)

        if not persona:
            return f"You are {agent_name}. {task_context}"

        system_prompt = persona.get("prompts", {}).get("system", "")
        task_prefix = persona.get("prompts", {}).get("task_prefix", "")

        enhanced_prompt = f"""
{system_prompt}

AGENT PROFILE:
- Role: {persona.get('role', 'general')}
- Personality: {persona.get('personality', 'adaptive')}
- Specialties: {', '.join(persona.get('specialties', []))}
- Communication Style: {persona.get('communication_style', 'professional')}

{task_prefix} {task_context}
"""
        return enhanced_prompt.strip()

    def print_all_personas(self):
        """Display all configured personas by scanning the personas directory."""
        print("\n" + "=" * 60)
        print("CONFIGURED AGENT PERSONAS")
        print("=" * 60)

        if not self.personas_dir.exists() or not any(self.personas_dir.iterdir()):
            print(f"No persona files found in {self.personas_dir}.")
            return

        found_personas = False
        for persona_file in self.personas_dir.glob("*_persona.json"):
            agent_name = persona_file.stem.replace("_persona", "")
            # Use self.load_persona to ensure consistent loading logic
            persona = self.load_persona(agent_name)
            if persona: # Check if persona is not empty
                found_personas = True
                print(f"\n🤖 {persona.get('name', agent_name.upper())}") # Use agent_name as fallback for name
                print(f"   Role: {persona.get('role', 'undefined')}")
                print(f"   Personality: {persona.get('personality', 'undefined')}")
                print(f"   Specialties: {', '.join(persona.get('specialties', []))}")
                print(f"   Style: {persona.get('communication_style', 'adaptive')}")
            else:
                print(f"\n🤖 {agent_name.upper()} (Warning: Could not load details or persona is empty)")

        if not found_personas:
            print(f"No valid persona configurations found in {self.personas_dir}.")

def main():
    """Main persona management interface"""
    manager = AgentPersonalityManager()

    print("=" * 50)
    print(" KOR'TANA AGENT PERSONALITY MANAGER")
    print("=" * 50)

    while True:
        print("\nOptions:")
        print("1. Setup default personas")
        print("2. View all personas")
        print("3. Customize agent persona")
        print("4. Test enhanced prompt")
        print("5. Export persona summary")
        print("0. Exit")

        choice = input("\nEnter choice (0-5): ").strip()

        if choice == "1":
            manager.setup_all_personas()
        elif choice == "2":
            manager.print_all_personas()
        elif choice == "3":
            agent_name = input(
                "Enter agent name (claude, flash, weaver, custom_agent): "
            ).strip()
            if agent_name in manager.default_personas:
                manager.customize_persona(agent_name)
            else:
                print("Unknown agent. Available: claude, flash, weaver, custom_agent")
        elif choice == "4":
            agent_name = input("Enter agent name: ").strip()
            task = input("Enter task context: ").strip()
            prompt = manager.generate_enhanced_prompt(agent_name, task)
            print(f"\n[ENHANCED PROMPT]\n{prompt}")
        elif choice == "5":
            # Export summary
            summary_file = manager.project_root / "agent_personas_summary.md"
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write("# Kor'tana Agent Personas\n\n")
                if manager.personas_dir.exists():
                    for persona_file in manager.personas_dir.glob("*_persona.json"):
                        agent_name = persona_file.stem.replace("_persona", "")
                        persona = manager.load_persona(agent_name)
                        if persona:
                            f.write(f"## {persona.get('name', agent_name.upper())}\n")
                            f.write(f"- **Role**: {persona.get('role', 'undefined')}\n")
                            f.write(
                                f"- **Personality**: {persona.get('personality', 'undefined')}\n"
                            )
                            f.write(
                                f"- **Specialties**: {', '.join(persona.get('specialties', []))}\n"
                            )
                            f.write(
                                f"- **Communication Style**: {persona.get('communication_style', 'adaptive')}\n\n"
                            )
                else:
                    f.write("No agent personas directory found.\n")
            print(f"[EXPORTED] Persona summary: {summary_file}")
        elif choice == "0":
            break
        else:
            print("Invalid choice. Please try again.")

    print("\nPersona management complete!")


if __name__ == "__main__":
    main()
