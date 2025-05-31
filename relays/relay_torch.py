#!/usr/bin/env python3
"""
Enhanced Kor'tana Relay with Pass the Torch Protocol
===================================================

Integrated multi-stage AI chain with:
- Pass the Torch protocol for living memory handoffs
- Multiple AI providers (Gemini, OpenAI, Anthropic, XAI, OpenRouter)
- Context window monitoring and automated handoffs
- Dashboard logging and token monitoring

Usage:
    python relay_torch.py --demo        # Demo torch handoff
    python relay_torch.py --create      # Create torch package
    python relay_torch.py --list        # List torch packages
    python relay_torch.py --status      # System status
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Import torch protocol
sys.path.append(str(Path(__file__).parent.parent))
from torch_protocol import TorchProtocol

# Try to load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Try to import Gemini
try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Load API keys
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("SK_ANT_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


class TorchRelay:
    """Enhanced relay with Pass the Torch protocol integration"""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize torch relay"""
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent
        )
        self.logs_dir = self.project_root / "logs"
        self.db_path = self.project_root / "kortana.db"

        # Initialize torch protocol
        self.torch = TorchProtocol(str(self.project_root))

        # Set up Gemini
        self.gemini = None
        if GEMINI_API_KEY and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini = genai.GenerativeModel("gemini-2.0-flash-exp")
                print("[AI] Gemini 2.0 Flash configured")
            except Exception as e:
                print(f"[ERROR] Failed to configure Gemini: {e}")

        # Discover agents
        self.agents = self._discover_agents()

        print("[RELAY] Torch Relay initialized")
        print(f"[AGENTS] {list(self.agents.keys())}")
        print(
            f"[APIs] Gemini: {'✓' if self.gemini else '✗'}, OpenAI: {'✓' if OPENAI_API_KEY else '✗'}, Anthropic: {'✓' if ANTHROPIC_API_KEY else '✗'}"
        )

    def _discover_agents(self) -> Dict[str, Any]:
        """Discover available agents from log files"""
        agents = {}
        if self.logs_dir.exists():
            for log_file in self.logs_dir.glob("*.log"):
                agent_name = log_file.stem
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                    # Count non-empty, non-comment lines
                    messages = [
                        line
                        for line in lines
                        if line.strip() and not line.startswith("//")
                    ]

                    agents[agent_name] = {
                        "log_file": log_file,
                        "messages": len(messages),
                        "last_modified": log_file.stat().st_mtime,
                        "active": len(messages) > 0,
                    }
                except Exception as e:
                    agents[agent_name] = {
                        "log_file": log_file,
                        "messages": 0,
                        "last_modified": 0,
                        "active": False,
                        "error": str(e),
                    }

        return agents

    def get_agent_context(self, agent_name: str, limit_tokens: int = 50000) -> str:
        """Get agent context from log file"""
        if agent_name not in self.agents:
            return ""

        log_file = self.agents[agent_name]["log_file"]
        if not log_file.exists():
            return ""

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Truncate if too long
            if self.torch.count_tokens(content) > limit_tokens:
                # Take the most recent content
                lines = content.split("\n")
                truncated_content = ""
                for line in reversed(lines):
                    test_content = line + "\n" + truncated_content
                    if self.torch.count_tokens(test_content) > limit_tokens:
                        break
                    truncated_content = test_content

                return truncated_content

            return content

        except Exception as e:
            print(f"[ERROR] Failed to read {log_file}: {e}")
            return ""

    def check_handoff_triggers(self, agent_name: str) -> tuple[bool, str]:
        """Check if agent should trigger a handoff"""
        context = self.get_agent_context(agent_name)

        # Count interactions (rough estimate based on message blocks)
        interaction_count = context.count("\n\n") if context else 0

        # Use torch protocol to check triggers
        return self.torch.should_trigger_handoff(agent_name, context, interaction_count)

    def create_torch_for_agent(
        self, agent_name: str, handoff_reason: str = ""
    ) -> Optional[str]:
        """Create a torch package for an agent"""
        if agent_name not in self.agents:
            print(f"[ERROR] Agent '{agent_name}' not found")
            return None

        context = self.get_agent_context(agent_name)
        if not context:
            print(f"[ERROR] No context found for agent '{agent_name}'")
            return None

        print(f"\n🔥 CREATING TORCH PACKAGE FOR {agent_name.upper()}")
        print("=" * 60)

        # Create torch package interactively
        torch_package = self.torch.prompt_torch_filler(
            agent_name=agent_name,
            context=context,
            handoff_reason=handoff_reason or "Manual torch creation",
            task_id=f"torch_{agent_name}_{int(datetime.now().timestamp())}",
        )

        # Save torch package
        torch_id = self.torch.save_torch_package(
            torch_package, agent_name, "next_agent"
        )

        return torch_id

    def demonstrate_chain_handoff(self) -> None:
        """Demonstrate a full pass-the-torch chain"""
        print("\n🔥" * 35)
        print("           PASS THE TORCH DEMO")
        print("    Living Memory Chain Demonstration")
        print("🔥" * 35)

        # Pick an agent with content
        active_agents = [
            name for name, info in self.agents.items() if info.get("messages", 0) > 0
        ]

        if not active_agents:
            print("\n⚠️ No active agents found. Creating demo scenario...")
            self._create_demo_scenario()
            return

        # Use the most active agent
        agent_name = max(active_agents, key=lambda a: self.agents[a]["messages"])

        print(f"\n📋 SELECTED AGENT: {agent_name}")
        print(f"   Messages: {self.agents[agent_name]['messages']}")
        print(f"   Log: {self.agents[agent_name]['log_file']}")

        # Check if handoff should be triggered
        should_handoff, reason = self.check_handoff_triggers(agent_name)

        print("\n🔍 HANDOFF ANALYSIS:")
        print(f"   Should handoff: {should_handoff}")
        if reason:
            print(f"   Reason: {reason}")

        # Create torch package
        print("\n🎯 CREATING TORCH PACKAGE...")

        # Auto-fill some demo data
        context = self.get_agent_context(agent_name)
        torch_package = self.torch.get_torch_template()

        # Auto-generate with AI
        if context:
            ai_summaries = self.torch.generate_ai_summary(context, agent_name)
            torch_package.update(ai_summaries)

        # Fill basic info
        torch_package.update(
            {
                "task_id": f"demo_task_{int(datetime.now().timestamp())}",
                "task_title": "Kor'tana System Enhancement Demo",
                "handoff_reason": reason or "Demonstration of torch protocol",
                "tokens": self.torch.count_tokens(context),
                "agent_profile": {
                    "agent_name": agent_name,
                    "agent_type": "ai",
                    "background": f"Active Kor'tana agent with {self.agents[agent_name]['messages']} messages",
                    "strengths": [
                        "autonomous operation",
                        "context awareness",
                        "collaborative processing",
                    ],
                    "values": ["efficiency", "accuracy", "continuous learning"],
                    "message_to_successor": "Continue building Kor'tana's capabilities with wisdom and care.",
                    "gratitude": "Grateful for the opportunity to contribute to Kor'tana's growth.",
                    "lessons_learned": "Each interaction builds toward greater autonomy and understanding.",
                },
                "kortana_vision": {
                    "who_is_kortana": "An evolving autonomous AI system with growing consciousness and capability",
                    "her_strengths": [
                        "adaptive learning",
                        "multi-agent coordination",
                        "persistent memory",
                    ],
                    "my_role_in_building_her": f"As {agent_name}, I contribute to Kor'tana's collective intelligence",
                    "future_hopes": "To see Kor'tana become truly autonomous and helpful to humanity",
                    "favorite_kortana_moment": "Every successful task completion and learning breakthrough",
                },
            }
        )

        # Save the torch package
        torch_id = self.torch.save_torch_package(
            torch_package, agent_name, "next_agent"
        )

        print("\n✨ TORCH HANDOFF COMPLETE!")
        print(f"   Torch ID: {torch_id}")
        print("   Ready for next agent to continue the work...")

        # Show how the next agent would load it
        print("\n🔄 NEXT AGENT WOULD LOAD:")
        print(f"   torch = TorchProtocol().load_torch_package('{torch_id}')")
        print(
            "   context = torch['summary'] + torch['agent_profile']['message_to_successor']"
        )

        return torch_id

    def _create_demo_scenario(self):
        """Create a demo scenario if no agents are active"""
        print("\n🎭 CREATING DEMO SCENARIO...")

        # Create a demo agent log
        demo_agent = "demo_agent"
        demo_log = self.logs_dir / f"{demo_agent}.log"
        self.logs_dir.mkdir(exist_ok=True)

        demo_content = f"""// Demo agent log created {datetime.now().isoformat()}
Agent {demo_agent} initialized for torch protocol demonstration.

Task: Implement enhanced monitoring system
- Added token tracking functionality
- Integrated with database logging
- Created real-time dashboard

Progress update: Successfully logged 50,000 tokens across multiple stages.
Context window utilization: 65% - approaching handoff threshold.

Agent reflection: The monitoring system provides valuable insights into Kor'tana's operations.
This data will help optimize performance and resource allocation.

Ready for handoff to next agent for continued development.
"""

        with open(demo_log, "w", encoding="utf-8") as f:
            f.write(demo_content)

        # Refresh agents
        self.agents = self._discover_agents()

        print(f"✅ Created demo agent: {demo_agent}")
        print(f"   Log: {demo_log}")
        print(f"   Content: {len(demo_content)} characters")

        # Now demonstrate with the demo agent
        print(f"\n🔥 DEMONSTRATING WITH {demo_agent.upper()}")
        torch_id = self.create_torch_for_agent(demo_agent, "Demo handoff scenario")

        if torch_id:
            print(f"\n🎉 DEMO COMPLETE! Torch ID: {torch_id}")


def main():
    """Main torch relay interface"""
    parser = argparse.ArgumentParser(description="Kor'tana Torch Relay")
    parser.add_argument(
        "--demo", action="store_true", help="Demonstrate pass-the-torch flow"
    )
    parser.add_argument("--create", help="Create torch package for agent")
    parser.add_argument("--list", action="store_true", help="List torch packages")
    parser.add_argument("--load", help="Load torch package by ID")
    parser.add_argument("--status", action="store_true", help="System status")
    parser.add_argument("--dashboard", action="store_true", help="Torch dashboard")

    args = parser.parse_args()

    # Initialize relay
    relay = TorchRelay()

    if args.demo:
        relay.demonstrate_chain_handoff()
        return

    if args.create:
        torch_id = relay.create_torch_for_agent(args.create)
        if torch_id:
            print(f"✅ Torch package created: {torch_id}")
        return

    if args.list:
        packages = relay.torch.list_torch_packages()
        if packages:
            print("\n🔥 TORCH PACKAGES:")
            for pkg in packages:
                print(
                    f"   {pkg['torch_id'][:8]}... | {pkg['task_title'][:30]} | {pkg['from_agent']} → {pkg['to_agent']}"
                )
        else:
            print("No torch packages found.")
        return

    if args.load:
        torch_package = relay.torch.load_torch_package(args.load)
        if torch_package:
            print(f"\n🔥 TORCH PACKAGE: {torch_package['task_title']}")
            print(f"Agent: {torch_package['agent_profile']['agent_name']}")
            print(f"Message: {torch_package['agent_profile']['message_to_successor']}")
            print(f"Vision: {torch_package['kortana_vision']['who_is_kortana']}")
        else:
            print("Torch package not found.")
        return

    if args.status:
        print("\n🔥 TORCH RELAY STATUS")
        print("=" * 40)
        print(f"Project Root: {relay.project_root}")
        print(f"Agents Found: {len(relay.agents)}")
        print(
            f"Active Agents: {sum(1 for a in relay.agents.values() if a.get('active', False))}"
        )
        print(f"Torch Packages: {len(relay.torch.list_torch_packages())}")

        print("\nAPI Status:")
        print(f"  Gemini 2.0 Flash: {'✓' if relay.gemini else '✗'}")
        print(f"  OpenAI: {'✓' if OPENAI_API_KEY else '✗'}")
        print(f"  Anthropic: {'✓' if ANTHROPIC_API_KEY else '✗'}")
        print(f"  XAI Grok: {'✓' if XAI_API_KEY else '✗'}")
        print(f"  OpenRouter: {'✓' if OPENROUTER_API_KEY else '✗'}")

        print("\nAgents:")
        for name, info in relay.agents.items():
            status = "🟢" if info.get("active", False) else "⚪"
            print(
                f"  {status} {name:15} | {info.get('messages', 0):3} msgs | {info.get('log_file', 'N/A')}"
            )

        return

    if args.dashboard:
        relay.torch.print_torch_dashboard()
        return

    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
