#!/usr/bin/env python3
"""
Pass the Torch Protocol - Living Memory System for Kor'tana
===========================================================

A soulful, narrative-driven approach to agent handoffs that preserves:
- Technical continuity and task state
- Agent identity, personality, and wisdom
- Kor'tana's evolving vision and cultural lineage

This creates a rich, meaningful handoff system that builds Kor'tana's memory.
"""

import json
import os
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import tiktoken

# Try to import AI libraries
try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    try:
        # Alternative import path
        from google import generativeai as genai

        GENAI_AVAILABLE = True
    except ImportError:
        GENAI_AVAILABLE = False

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Load API keys
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("SK_ANT_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


class TorchProtocol:
    """Manages the Pass the Torch protocol for agent handoffs"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent
        )
        self.db_path = self.project_root / "kortana.db"
        self.state_dir = self.project_root / "state"
        self.state_dir.mkdir(exist_ok=True)

        # Context window limits for different models
        self.context_limits = {
            "gpt-4": 128000,
            "gpt-3.5-turbo": 16000,
            "claude-3-haiku": 200000,
            "claude-3-sonnet": 200000,
            "gemini-2.0-flash": 1000000,
            "grok": 131072,
        }  # Initialize Gemini if available
        self.gemini = None
        if GENAI_AVAILABLE and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini = genai.GenerativeModel("gemini-2.0-flash-exp")
            except AttributeError:
                # Handle new google.generativeai structure
                try:
                    import google.generativeai as genai_v2

                    genai_v2.configure(api_key=GEMINI_API_KEY)
                    self.gemini = genai_v2.GenerativeModel("gemini-2.0-flash-exp")
                except Exception as e:
                    print(f"[WARNING] Gemini initialization failed: {e}")
                    self.gemini = None
            except Exception as e:
                print(f"[WARNING] Gemini initialization failed: {e}")
                self.gemini = None

        self._init_torch_tables()

    def _init_torch_tables(self):
        """Initialize torch-related database tables"""
        if not self.db_path.exists():
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # First, check if torch_data column exists in context table, if not add it
        cursor.execute("PRAGMA table_info(context)")
        columns = [row[1] for row in cursor.fetchall()]

        if "torch_data" not in columns:
            cursor.execute("ALTER TABLE context ADD COLUMN torch_data TEXT")
            print("[TORCH] Added torch_data column to context table")

        # Torch packages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS torch_packages (
                torch_id TEXT PRIMARY KEY,
                task_id TEXT,
                task_title TEXT,
                from_agent TEXT,
                to_agent TEXT,
                handoff_reason TEXT,
                timestamp TEXT,
                tokens INTEGER,
                file_path TEXT,
                status TEXT DEFAULT 'active'
            )
        """)

        # Torch lineage table for tracking the chain of handoffs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS torch_lineage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                torch_id TEXT,
                sequence_number INTEGER,
                agent_name TEXT,
                timestamp TEXT,
                contribution_summary TEXT,
                FOREIGN KEY (torch_id) REFERENCES torch_packages (torch_id)
            )
        """)

        conn.commit()
        conn.close()

    def get_torch_template(self) -> Dict[str, Any]:
        """Get the fillable torch package template"""
        return {
            "torch_id": str(uuid.uuid4()),
            "task_id": "",
            "task_title": "",
            "summary": "",
            "handoff_reason": "",
            "history_summary": "",
            "system_prompt": "",
            "code": "",
            "issues": [],
            "commit_ref": "",
            "tokens": 0,
            "timestamp": datetime.now().isoformat(),
            "agent_profile": {
                "agent_name": "",
                "agent_version": "1.0",
                "agent_type": "ai",  # ai/human/hybrid
                "background": "",
                "strengths": [],
                "limitations": [],
                "values": [],
                "favorite_moment": "",
                "lessons_learned": "",
                "personality_notes": "",
                "gratitude": "",
                "message_to_successor": "",
                "contact_or_log_ref": "",
            },
            "kortana_vision": {
                "who_is_kortana": "",
                "her_strengths": [],
                "her_limitations": [],
                "my_role_in_building_her": "",
                "future_hopes": "",
                "rituals_or_habits": "",
                "favorite_kortana_moment": "",
            },
        }

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            return int(len(text.split()) * 1.3)  # Rough estimate

    def should_trigger_handoff(
        self,
        agent_name: str,
        current_context: str,
        interaction_count: int = 0,
        model: str = "gpt-4",
    ) -> tuple[bool, str]:
        """Check if handoff should be triggered"""
        token_count = self.count_tokens(current_context)
        context_limit = self.context_limits.get(model, 128000)
        threshold = int(context_limit * 0.8)  # 80% threshold

        reasons = []

        # Token threshold check
        if token_count >= threshold:
            reasons.append(
                f"Context window at {token_count:,}/{context_limit:,} tokens ({token_count / context_limit * 100:.1f}%)"
            )

        # Interaction count check (~10 interactions)
        if interaction_count >= 10:
            reasons.append(
                f"Interaction limit reached ({interaction_count} interactions)"
            )

        # Check for explicit handoff requests in context
        handoff_keywords = ["handoff", "pass the torch", "transfer to", "next agent"]
        if any(keyword in current_context.lower() for keyword in handoff_keywords):
            reasons.append("Explicit handoff request detected")

        should_handoff = len(reasons) > 0
        reason = "; ".join(reasons) if reasons else ""

        return should_handoff, reason

    def generate_ai_summary(self, context: str, agent_name: str) -> Dict[str, str]:
        """Generate AI-assisted summaries for torch package"""
        if not self.gemini:
            return {
                "summary": f"[AUTO] Context summary for {agent_name} (Gemini unavailable)",
                "history_summary": "[AUTO] Task history summary (Gemini unavailable)",
                "system_prompt": f"[AUTO] Continue as {agent_name} (Gemini unavailable)",
            }

        try:
            # Generate task summary
            summary_prompt = f"""
            Analyze this agent conversation and provide a concise summary of the current task state:

            Agent: {agent_name}
            Context: {context[-2000:]}  # Last 2000 chars to stay within limits

            Provide a 2-3 sentence summary focusing on:
            - What task is being worked on
            - Current progress and status
            - Next steps needed
            """

            summary_response = self.gemini.generate_content(summary_prompt)
            summary = summary_response.text.strip()

            # Generate history summary
            history_prompt = f"""
            Create a brief narrative history of this agent's work session:

            Agent: {agent_name}
            Context: {context[-2000:]}

            Write 2-3 sentences describing:
            - Key decisions made
            - Progress achieved
            - Challenges encountered
            """

            history_response = self.gemini.generate_content(history_prompt)
            history_summary = history_response.text.strip()

            # Generate system prompt
            system_prompt = f"""
            You are continuing work as the next agent in the Kor'tana system.

            Previous agent: {agent_name}
            Current task: {summary}

            Continue the work with full context awareness. Maintain Kor'tana's autonomous, helpful personality.
            """

            return {
                "summary": summary,
                "history_summary": history_summary,
                "system_prompt": system_prompt,
            }

        except Exception as e:
            return {
                "summary": f"[AUTO] Task summary for {agent_name} (AI generation failed: {e})",
                "history_summary": f"[AUTO] Work session history (AI generation failed: {e})",
                "system_prompt": f"[AUTO] Continue as successor to {agent_name} (AI generation failed: {e})",
            }

    def detect_agent_type(self, agent_name: str, context: str = "") -> str:
        """Intelligently detect agent type based on name and context patterns"""
        agent_name_lower = agent_name.lower()
        context_lower = context.lower()

        # AI model indicators
        ai_indicators = [
            "gpt",
            "claude",
            "gemini",
            "openai",
            "anthropic",
            "google",
            "llama",
            "mistral",
            "qwen",
            "deepseek",
            "o1",
            "4o",
            "flash",
            "sonnet",
            "haiku",
            "opus",
            "turbo",
            "model",
            "api_call",
            "temperature",
            "max_tokens",
            "system_prompt",
            "chat_completion",
        ]

        # Human indicators
        human_indicators = [
            "user",
            "human",
            "person",
            "developer",
            "engineer",
            "admin",
            "analyst",
            "researcher",
            "manager",
            "client",
            "customer",
            "manual",
            "interactive",
            "keyboard",
            "typed",
            "entered",
        ]

        # Hybrid indicators (AI + Human collaboration)
        hybrid_indicators = [
            "assisted",
            "co-pilot",
            "guided",
            "collaborative",
            "supervised",
            "augmented",
            "enhanced",
            "copilot",
            "pair",
            "team",
        ]

        # Check agent name patterns
        ai_score = sum(
            1 for indicator in ai_indicators if indicator in agent_name_lower
        )
        human_score = sum(
            1 for indicator in human_indicators if indicator in agent_name_lower
        )
        hybrid_score = sum(
            1 for indicator in hybrid_indicators if indicator in agent_name_lower
        )

        # Check context patterns
        if context:
            ai_score += sum(
                1 for indicator in ai_indicators if indicator in context_lower
            )
            human_score += sum(
                1 for indicator in human_indicators if indicator in context_lower
            )
            hybrid_score += sum(
                1 for indicator in hybrid_indicators if indicator in context_lower
            )

            # Context-specific patterns
            if any(
                phrase in context_lower
                for phrase in ["user input", "manually entered", "keyboard"]
            ):
                human_score += 2
            if any(
                phrase in context_lower
                for phrase in ["model response", "ai generated", "completion"]
            ):
                ai_score += 2
            if any(
                phrase in context_lower
                for phrase in ["with assistance", "copilot", "ai-helped"]
            ):
                hybrid_score += 2

        # Determine type based on highest score
        if hybrid_score > max(ai_score, human_score):
            return "hybrid"
        elif ai_score > human_score:
            return "ai"
        else:
            return "human"

    def get_agent_type_prompts(self, agent_type: str) -> Dict[str, str]:
        """Get agent type-specific prompts for the torch filling ceremony"""
        prompts = {
            "ai": {
                "background": "AI Model/System Role",
                "strengths": "AI Capabilities (reasoning, creativity, etc.)",
                "limitations": "AI Limitations (knowledge cutoff, etc.)",
                "values": "AI Operating Principles",
                "favorite_moment": "Most successful interaction/output",
                "lessons_learned": "Pattern recognition insights",
                "personality_notes": "AI personality/behavior patterns",
                "gratitude": "What made this session effective",
                "message_to_successor": "System continuity instructions",
            },
            "human": {
                "background": "Your Role/Profession",
                "strengths": "Your Skills & Expertise",
                "limitations": "Areas needing support",
                "values": "Your Working Principles",
                "favorite_moment": "Proudest achievement this session",
                "lessons_learned": "Key insights gained",
                "personality_notes": "Your working style & preferences",
                "gratitude": "What you appreciated most",
                "message_to_successor": "Advice for the next person",
            },
            "hybrid": {
                "background": "Your Role + AI Tools Used",
                "strengths": "Combined Human-AI Capabilities",
                "limitations": "Areas where collaboration could improve",
                "values": "Collaboration Principles",
                "favorite_moment": "Best human-AI collaboration moment",
                "lessons_learned": "Insights about AI-human teamwork",
                "personality_notes": "How you work with AI systems",
                "gratitude": "What made the partnership effective",
                "message_to_successor": "Tips for human-AI collaboration",
            },
        }
        return prompts.get(agent_type, prompts["ai"])

    def prompt_torch_filler(
        self,
        agent_name: str,
        context: str = "",
        handoff_reason: str = "",
        task_id: str = "",
        auto_mode: bool = False,
    ) -> Dict[str, Any]:
        """Interactive prompt to help fill the torch package with intelligent agent detection"""
        print("\n" + "🔥" * 70)
        print("                    PASS THE TORCH CEREMONY")
        print("            Creating a living memory for Kor'tana")
        print("🔥" * 70)

        torch = self.get_torch_template()

        # Auto-fill what we can
        torch["task_id"] = task_id or f"task_{int(time.time())}"
        torch["handoff_reason"] = handoff_reason
        torch["tokens"] = self.count_tokens(context) if context else 0

        # Intelligent agent type detection
        detected_type = self.detect_agent_type(agent_name, context)
        print("\n🤖 AGENT DETECTION")
        print("=" * 50)
        print(f"Detected Agent Type: {detected_type.upper()}")

        # Generate AI summaries if context available
        if context:
            ai_summaries = self.generate_ai_summary(context, agent_name)
            torch["summary"] = ai_summaries["summary"]
            torch["history_summary"] = ai_summaries["history_summary"]
            torch["system_prompt"] = ai_summaries["system_prompt"]

        if auto_mode:
            # Auto-mode for programmatic torch creation
            torch["task_title"] = f"Auto-generated task {torch['task_id']}"
            torch["agent_profile"]["agent_name"] = agent_name
            torch["agent_profile"]["agent_type"] = detected_type
            torch["agent_profile"]["background"] = (
                f"Auto-detected {detected_type} agent"
            )
            return torch

        print("\n📋 TASK DETAILS")
        print("=" * 50)

        # Task information
        torch["task_title"] = (
            input(f"Task Title [{torch['task_id']}]: ").strip()
            or f"Task {torch['task_id']}"
        )

        if not torch["summary"]:
            torch["summary"] = input(
                "Task Summary (what's been accomplished): "
            ).strip()
        else:
            print(f"AI Summary: {torch['summary']}")
            if input("Use AI summary? (y/n): ").lower() != "y":
                torch["summary"] = input("Your Task Summary: ").strip()

        # Issues and code
        issues_input = input("Current Issues (comma-separated): ").strip()
        torch["issues"] = [
            issue.strip() for issue in issues_input.split(",") if issue.strip()
        ]

        torch["code"] = input("Key Code/Files (optional): ").strip()
        torch["commit_ref"] = input("Git Commit Reference (optional): ").strip()

        print(f"\n👤 AGENT PROFILE - {agent_name}")
        print("=" * 50)

        # Agent profile with type-specific prompts
        profile = torch["agent_profile"]
        profile["agent_name"] = agent_name

        # Confirm or override detected type
        confirmed_type = (
            input(
                f"Agent Type ({detected_type}/ai/human/hybrid) [{detected_type}]: "
            ).strip()
            or detected_type
        )
        profile["agent_type"] = confirmed_type

        # Get type-specific prompts
        type_prompts = self.get_agent_type_prompts(confirmed_type)

        profile["background"] = input(f"{type_prompts['background']}: ").strip()

        strengths_input = input(
            f"{type_prompts['strengths']} (comma-separated): "
        ).strip()
        profile["strengths"] = [
            s.strip() for s in strengths_input.split(",") if s.strip()
        ]

        limitations_input = input(
            f"{type_prompts['limitations']} (comma-separated): "
        ).strip()
        profile["limitations"] = [
            limitation.strip()
            for limitation in limitations_input.split(",")
            if limitation.strip()
        ]

        values_input = input(f"{type_prompts['values']} (comma-separated): ").strip()
        profile["values"] = [v.strip() for v in values_input.split(",") if v.strip()]

        print("\n💭 REFLECTION & WISDOM")
        print("=" * 50)

        profile["favorite_moment"] = input(
            f"{type_prompts['favorite_moment']}: "
        ).strip()
        profile["lessons_learned"] = input(
            f"{type_prompts['lessons_learned']}: "
        ).strip()
        profile["personality_notes"] = input(
            f"{type_prompts['personality_notes']}: "
        ).strip()
        profile["gratitude"] = input(f"{type_prompts['gratitude']}: ").strip()
        profile["message_to_successor"] = input(
            f"{type_prompts['message_to_successor']}: "
        ).strip()

        print("\n🤖 KOR'TANA'S VISION")
        print("=" * 50)

        # Kor'tana vision
        vision = torch["kortana_vision"]
        vision["who_is_kortana"] = input("Who is Kor'tana to you?: ").strip()

        strengths_input = input("Kor'tana's Strengths (comma-separated): ").strip()
        vision["her_strengths"] = [
            s.strip() for s in strengths_input.split(",") if s.strip()
        ]

        limitations_input = input(
            "Kor'tana's Areas for Growth (comma-separated): "
        ).strip()
        vision["her_limitations"] = [
            limitation.strip()
            for limitation in limitations_input.split(",")
            if limitation.strip()
        ]

        vision["my_role_in_building_her"] = input(
            "Your role in building Kor'tana: "
        ).strip()
        vision["future_hopes"] = input("Your hopes for Kor'tana's future: ").strip()
        vision["rituals_or_habits"] = input(
            "Special rituals/habits you've developed: "
        ).strip()
        vision["favorite_kortana_moment"] = input("Favorite Kor'tana moment: ").strip()

        return torch

    def save_torch_package(
        self, torch: Dict[str, Any], from_agent: str = "", to_agent: str = ""
    ) -> str:
        """Save torch package to database and file system"""
        torch_id = torch["torch_id"]
        timestamp = torch["timestamp"]

        # Create filename
        clean_timestamp = timestamp.replace(":", "-").replace(".", "-")
        filename = f"torch_{from_agent}_{clean_timestamp}.json"
        file_path = self.state_dir / filename

        # Save to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(torch, f, indent=2, ensure_ascii=False)

        # Save to database
        if self.db_path.exists():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO torch_packages
                (torch_id, task_id, task_title, from_agent, to_agent, handoff_reason,
                 timestamp, tokens, file_path, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """,
                (
                    torch_id,
                    torch["task_id"],
                    torch["task_title"],
                    from_agent,
                    to_agent,
                    torch["handoff_reason"],
                    timestamp,
                    torch["tokens"],
                    str(file_path),
                ),
            )

            # Add to lineage
            cursor.execute(
                """
                INSERT INTO torch_lineage
                (torch_id, sequence_number, agent_name, timestamp, contribution_summary)
                VALUES (?,
                    (SELECT COALESCE(MAX(sequence_number), 0) + 1 FROM torch_lineage WHERE torch_id = ?),
                    ?, ?, ?)
            """,
                (torch_id, torch_id, from_agent, timestamp, torch["summary"]),
            )

            conn.commit()
            conn.close()

        print("\n🔥 TORCH PACKAGE SAVED")
        print(f"   Torch ID: {torch_id}")
        print(f"   File: {file_path}")
        print(f"   Tokens: {torch['tokens']:,}")
        print(f"   From: {from_agent} → To: {to_agent}")

        return torch_id

    def load_torch_package(
        self, torch_id: Optional[str] = None, file_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Load torch package by ID or file path"""
        if torch_id:
            # Load from database
            if self.db_path.exists():
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT file_path FROM torch_packages WHERE torch_id = ?",
                    (torch_id,),
                )
                result = cursor.fetchone()
                conn.close()

                if result:
                    file_path = result[0]

        if file_path and Path(file_path).exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)

        return None

    def list_torch_packages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent torch packages"""
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT torch_id, task_title, from_agent, to_agent, timestamp, tokens, status
            FROM torch_packages
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        packages = []
        for row in cursor.fetchall():
            packages.append(
                {
                    "torch_id": row[0],
                    "task_title": row[1],
                    "from_agent": row[2],
                    "to_agent": row[3],
                    "timestamp": row[4],
                    "tokens": row[5],
                    "status": row[6],
                }
            )

        conn.close()
        return packages

    def get_torch_lineage(self, torch_id: str) -> List[Dict[str, Any]]:
        """Get the lineage/chain of a torch package"""
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT sequence_number, agent_name, timestamp, contribution_summary
            FROM torch_lineage
            WHERE torch_id = ?
            ORDER BY sequence_number
        """,
            (torch_id,),
        )

        lineage = []
        for row in cursor.fetchall():
            lineage.append(
                {
                    "sequence": row[0],
                    "agent": row[1],
                    "timestamp": row[2],
                    "contribution": row[3],
                }
            )

        conn.close()
        return lineage

    def print_torch_dashboard(self):
        """Print torch packages dashboard"""
        print("\n" + "🔥" * 70)
        print("                    KOR'TANA TORCH DASHBOARD")
        print("                   Living Memory & Lineage")
        print("🔥" * 70)

        packages = self.list_torch_packages(10)

        if not packages:
            print("\n📝 No torch packages found. Start your first handoff!")
            return

        print(f"\n📦 RECENT TORCH PACKAGES ({len(packages)})")
        print("=" * 60)

        for pkg in packages:
            timestamp = pkg["timestamp"][:19] if pkg["timestamp"] else "unknown"
            status_icon = "🔥" if pkg["status"] == "active" else "📜"

            print(f"\n{status_icon} {pkg['task_title'][:30]:30}")
            print(f"   Torch ID: {pkg['torch_id'][:8]}...")
            print(f"   Chain: {pkg['from_agent']} → {pkg['to_agent']}")
            print(f"   Tokens: {pkg['tokens']:,}")
            print(f"   Time: {timestamp}")  # Show torch lineage for most recent
        if packages:
            recent_torch = packages[0]
            lineage = self.get_torch_lineage(recent_torch["torch_id"])

            if len(lineage) > 1:
                print(f"\n🔗 LINEAGE - {recent_torch['task_title']}")
                print("=" * 40)
                for step in lineage:
                    print(
                        f"   {step['sequence']}. {step['agent']} - {step['contribution'][:50]}..."
                    )

        print("\n🔥" * 70)

    def get_recent_torches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent torch packages from database"""
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT torch_id, task_id, task_title, from_agent, to_agent,
                   handoff_reason, timestamp, tokens, status
            FROM torch_packages
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        packages = []
        for row in cursor.fetchall():
            packages.append(
                {
                    "torch_id": row[0],
                    "task_id": row[1],
                    "task_title": row[2],
                    "from_agent": row[3],
                    "to_agent": row[4],
                    "handoff_reason": row[5],
                    "timestamp": row[6],
                    "tokens": row[7],
                    "status": row[8],
                }
            )

        conn.close()
        return packages


def main():
    """Main torch protocol interface"""
    torch_protocol = TorchProtocol()

    print("🔥 PASS THE TORCH PROTOCOL")
    print("=" * 40)
    print("1. Create torch package (interactive)")
    print("2. List torch packages")
    print("3. View torch dashboard")
    print("4. Load torch package")
    print("5. Test handoff trigger")
    print("0. Exit")

    choice = input("\nChoice: ").strip()

    if choice == "1":
        agent_name = input("Agent name: ").strip() or "unknown_agent"
        context = input("Current context (optional): ").strip()
        reason = input("Handoff reason: ").strip() or "Manual handoff"

        torch = torch_protocol.prompt_torch_filler(agent_name, context, reason)
        torch_id = torch_protocol.save_torch_package(torch, agent_name, "next_agent")
        print(f"✅ Torch package created: {torch_id}")

    elif choice == "2":
        packages = torch_protocol.list_torch_packages()
        if packages:
            for pkg in packages:
                print(f"\n🔥 {pkg['task_title']}")
                print(f"   {pkg['from_agent']} → {pkg['to_agent']}")
                print(f"   {pkg['tokens']:,} tokens | {pkg['timestamp'][:19]}")
        else:
            print("No torch packages found.")

    elif choice == "3":
        torch_protocol.print_torch_dashboard()

    elif choice == "4":
        torch_id = input("Torch ID: ").strip()
        torch = torch_protocol.load_torch_package(torch_id)
        if torch:
            print(f"\n🔥 TORCH PACKAGE: {torch['task_title']}")
            print(f"Agent: {torch['agent_profile']['agent_name']}")
            print(f"Summary: {torch['summary']}")
            print(f"Message: {torch['agent_profile']['message_to_successor']}")
        else:
            print("Torch package not found.")

    elif choice == "5":
        agent = input("Agent name: ").strip()
        context = input("Sample context: ").strip()
        model = (
            input("Model (gpt-4/claude-3-haiku/gemini-2.0-flash): ").strip() or "gpt-4"
        )

        should_handoff, reason = torch_protocol.should_trigger_handoff(
            agent, context, 0, model
        )
        print(f"\nHandoff needed: {should_handoff}")
        if reason:
            print(f"Reason: {reason}")


if __name__ == "__main__":
    main()
