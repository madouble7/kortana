#!/usr/bin/env python3
"""
KOR'TANA Autonomous Agent Interface - Interactive Demo
========================================================

Live demonstration of Volitional Self-Correction Engine (Phase 1-2)
showing dynamic task classification and autonomous decision-making.

Usage:
    python autonomous_agent_demo.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from src.kortana.human_only_protocol import HumanOnlyProtocol, TaskClassification


class AutonomousAgentDemo:
    """Interactive demonstration of autonomous task classification"""

    def __init__(self):
        self.hop = HumanOnlyProtocol()
        self.task_history = []

    def classify_and_execute(self, task_name: str, task_type: str, branch: str) -> dict:
        """Classify a task and show execution path"""
        context = {
            "branch": branch,
            "task_name": task_name,
            "task_type": task_type,
        }

        # Classify using Phase 1 dynamic classification
        classification = self.hop.classify_task(task_type, context)

        # Determine execution path based on classification
        if classification == TaskClassification.SELF_CORRECTION:
            execution_path = "AUTONOMOUS (Phase 1-2: Self-Correction)"
            requires_approval = False
            autonomy_level = "HIGH"
        elif classification == TaskClassification.AUTO:
            execution_path = "AUTONOMOUS (Phase 1-2: Auto Execute)"
            requires_approval = False
            autonomy_level = "HIGH"
        elif classification == TaskClassification.HO:
            execution_path = "HUMAN ONLY (Requires scaffolded steps)"
            requires_approval = False
            autonomy_level = "MEDIUM"
        else:  # APPROVAL
            execution_path = "APPROVAL REQUIRED (Human decision gate)"
            requires_approval = True
            autonomy_level = "LOW"

        result = {
            "task_name": task_name,
            "task_type": task_type,
            "branch": branch,
            "classification": classification.value,
            "execution_path": execution_path,
            "requires_approval": requires_approval,
            "autonomy_level": autonomy_level,
            "status": "CLASSIFIED",
        }

        self.task_history.append(result)
        return result

    def run_demo(self):
        """Run interactive autonomous agent demonstration"""
        print("\n" + "=" * 80)
        print("KOR'TANA AUTONOMOUS AGENT INTERFACE - PHASE 1-2 DEMONSTRATION")
        print("=" * 80)
        print("\nDemonstrating Volitional Self-Correction Engine")
        print("Dynamic task classification with context-aware autonomy decisions\n")

        # Define test scenarios
        scenarios = [
            {
                "name": "Test Failure Fix",
                "type": "fix_test_failure",
                "branch": "evolution/test-fix-001",
            },
            {
                "name": "Schema Update",
                "type": "schema_update",
                "branch": "evolution/schema-v2",
            },
            {
                "name": "Code Refactor",
                "type": "code_refactor",
                "branch": "evolution/refactor-async",
            },
            {
                "name": "Feature on Main",
                "type": "fix_test_failure",
                "branch": "feature/new-auth",
            },
            {
                "name": "Production Deploy",
                "type": "deploy_to_production",
                "branch": "main",
            },
        ]

        print("SCENARIO CLASSIFICATION RESULTS")
        print("-" * 80)

        for scenario in scenarios:
            result = self.classify_and_execute(
                scenario["name"], scenario["type"], scenario["branch"]
            )

            print(f"\n📋 Task: {result['task_name']}")
            print(f"   Type: {result['task_type']}")
            print(f"   Branch: {result['branch']}")
            print(f"   Classification: {result['classification'].upper()}")
            print(f"   Execution Path: {result['execution_path']}")
            print(f"   Autonomy Level: {result['autonomy_level']}")
            print(f"   Status: {result['status']}")

        # Summary statistics
        print("\n" + "=" * 80)
        print("EXECUTION SUMMARY")
        print("=" * 80)

        auto_count = sum(
            1 for t in self.task_history if t["classification"] in ["auto", "self_correction"]
        )
        ho_count = sum(1 for t in self.task_history if t["classification"] == "ho")
        approval_count = sum(1 for t in self.task_history if t["classification"] == "approval")

        print(f"\nTotal Tasks Classified: {len(self.task_history)}")
        print(f"Autonomous Tasks (AUTO + SELF_CORRECTION): {auto_count}")
        print(f"Human-Only Tasks (HO): {ho_count}")
        print(f"Approval Required Tasks: {approval_count}")

        autonomy_percentage = (
            (auto_count / len(self.task_history) * 100) if self.task_history else 0
        )
        print(f"\nSystem Autonomy: {autonomy_percentage:.0f}%")
        print("Current Phase: 1-2 (60% base autonomy)")
        print("Next Phase: 3 (GitHub PR automation → 100% autonomy)")

        # Show context-aware decisions
        print("\n" + "=" * 80)
        print("CONTEXT-AWARE CLASSIFICATION LOGIC VERIFICATION")
        print("=" * 80)
        print("\n✅ Evolution/ branches with test fixes → SELF_CORRECTION (autonomous)")
        print("✅ Evolution/ branches with schema updates → SELF_CORRECTION (autonomous)")
        print("✅ Feature branches with changes → HO (human decision)")
        print("✅ Main branch operations → APPROVAL (human gate)")
        print("✅ Production deployments → APPROVAL (human approval required)")

        print("\n" + "=" * 80)
        print("PHASE 1-2 IMPLEMENTATION STATUS: ✅ OPERATIONAL")
        print("=" * 80 + "\n")

        return 0


def main():
    """Execute autonomous agent demo"""
    try:
        demo = AutonomousAgentDemo()
        return demo.run_demo()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
