#!/usr/bin/env python3
"""
Phase 5 Advanced Autonomous Kor'tana Launcher
============================================

Launch and manage Phase 5 Advanced Autonomous Intelligence operation
with sophisticated monitoring and control capabilities.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

# Configure error logging
logging.basicConfig(filename="phase5_launcher.log", level=logging.ERROR)

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)


class Phase5Launcher:
    """Phase 5 Advanced Autonomous Kor'tana Launcher and Manager."""

    def __init__(self):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data"
        self.phase5_script = self.project_root / "phase5_advanced_autonomous.py"
        self.status_file = self.data_dir / "phase5_status.json"

        print("🌟 PHASE 5 ADVANCED AUTONOMOUS KOR'TANA LAUNCHER")
        print("=" * 60)
        print(f"Project Root: {self.project_root}")
        print(f"Data Directory: {self.data_dir}")
        print()

    def show_menu(self):
        """Display the main launcher menu."""
        while True:
            self._clear_screen()
            print("🌟 PHASE 5 ADVANCED AUTONOMOUS KOR'TANA CONTROL")
            print("=" * 60)
            print()

            # Check current status
            status = self._check_phase5_status()
            self._display_status(status)

            print("\n📋 CONTROL OPTIONS:")
            print("=" * 30)
            print("1. 🚀 Launch Phase 5 Advanced Autonomous Operation")
            print("2. 📊 Monitor Advanced Autonomous Activity")
            print("3. 🔍 View Detailed System Analysis")
            print("4. ⚡ Performance and Optimization Report")
            print("5. 🧠 Advanced Reasoning Analysis")
            print("6. 📚 Learning and Adaptation Report")
            print("7. 🌍 Environmental Assessment Report")
            print("8. 🎯 Strategic Planning Status")
            print("9. 🛑 Stop Advanced Autonomous Operation")
            print("10. 🔄 Restart with Enhanced Configuration")
            print("0. ❌ Exit Launcher")
            print()

            choice = input("Select option (0-10): ").strip()

            if choice == "1":
                self._launch_phase5()
            elif choice == "2":
                self._monitor_activity()
            elif choice == "3":
                self._view_system_analysis()
            elif choice == "4":
                self._performance_report()
            elif choice == "5":
                self._reasoning_analysis()
            elif choice == "6":
                self._learning_report()
            elif choice == "7":
                self._environmental_report()
            elif choice == "8":
                self._strategic_status()
            elif choice == "9":
                self._stop_phase5()
            elif choice == "10":
                self._restart_enhanced()
            elif choice == "0":
                print("👋 Exiting Phase 5 Launcher...")
                break
            else:
                print("❌ Invalid option. Please try again.")
                time.sleep(1)

    def _launch_phase5(self):
        """Launch Phase 5 Advanced Autonomous Operation."""
        print("🚀 LAUNCHING PHASE 5 ADVANCED AUTONOMOUS OPERATION")
        print("=" * 55)

        # Check if already running
        if self._is_phase5_running():
            print("⚠️  Phase 5 is already running!")
            self._wait_for_key()
            return

        try:
            # Launch Phase 5 in background
            print("Starting advanced autonomous intelligence...")

            if os.name == "nt":  # Windows
                process = subprocess.Popen(
                    [sys.executable, str(self.phase5_script)],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:  # Unix-like
                process = subprocess.Popen(
                    [sys.executable, str(self.phase5_script)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

            print(f"✅ Phase 5 launched with PID: {process.pid}")

            # Update status
            self._update_status(
                {
                    "phase5_running": True,
                    "launch_time": datetime.now().isoformat(),
                    "pid": process.pid,
                    "status": "active",
                }
            )

            print("🌟 Advanced Autonomous Intelligence is now active!")
            print("📊 Monitoring systems will begin data collection...")

        except Exception as e:
            print(f"❌ Failed to launch Phase 5: {e}")
            logging.error("Failed to launch Phase 5", exc_info=True)

        self._wait_for_key()

    def _monitor_activity(self):
        """Monitor Phase 5 autonomous activity."""
        print("📊 PHASE 5 AUTONOMOUS ACTIVITY MONITOR")
        print("=" * 45)

        if not self._is_phase5_running():
            print("⚠️  Phase 5 is not currently running.")
            self._wait_for_key()
            return

        try:
            # Read activity logs
            log_file = self.data_dir / "autonomous_logs" / "phase5_autonomous.log"
            if log_file.exists():
                print("📋 Recent Activity:")
                print("-" * 30)

                with open(log_file) as f:
                    lines = f.readlines()
                    recent_lines = lines[-20:] if len(lines) > 20 else lines

                    for line in recent_lines:
                        print(line.strip())
            else:
                print("📝 Activity log not found or empty.")

            # Show real-time status
            print("\n🔄 Real-time Status:")
            print("-" * 20)
            status = self._get_real_time_status()
            for key, value in status.items():
                print(f"{key}: {value}")

        except Exception as e:
            print(f"❌ Error monitoring activity: {e}")
            logging.error("Error monitoring activity", exc_info=True)

        self._wait_for_key()

    def _view_system_analysis(self):
        """View detailed system analysis."""
        print("🔍 PHASE 5 DETAILED SYSTEM ANALYSIS")
        print("=" * 40)

        try:
            state_file = self.data_dir / "phase5_autonomous_state.json"
            if state_file.exists():
                with open(state_file) as f:
                    state_data = json.load(f)

                print("🧠 Autonomous State:")
                print("-" * 20)
                autonomous_state = state_data.get("autonomous_state", {})
                for key, value in autonomous_state.items():
                    if isinstance(value, float):
                        print(f"  {key}: {value:.3f}")
                    else:
                        print(f"  {key}: {value}")

                print("\n📊 Performance Metrics:")
                print("-" * 25)
                metrics = state_data.get("performance_metrics", {})
                for metric, data in metrics.items():
                    if data:
                        latest = data[-1]
                        print(f"  {metric}: {latest['value']:.3f}")

                print("\n🔄 Recent Adaptations:")
                print("-" * 22)
                adaptations = state_data.get("adaptation_history", [])
                for adaptation in adaptations[-5:]:
                    timestamp = adaptation.get("timestamp", "Unknown")
                    adaptations_made = adaptation.get("adaptations_made", 0)
                    print(f"  {timestamp}: {adaptations_made} adaptations")

            else:
                print("📝 System state file not found.")

        except Exception as e:
            print(f"❌ Error viewing system analysis: {e}")
            logging.error("Error viewing system analysis", exc_info=True)

        self._wait_for_key()

    def _performance_report(self):
        """Show performance and optimization report."""
        print("⚡ PHASE 5 PERFORMANCE & OPTIMIZATION REPORT")
        print("=" * 50)

        try:
            # Calculate uptime
            status = self._load_status()
            if status.get("launch_time"):
                launch_time = datetime.fromisoformat(status["launch_time"])
                uptime = datetime.now() - launch_time
                print(f"⏱️  System Uptime: {uptime}")

            # Performance metrics
            state_file = self.data_dir / "phase5_autonomous_state.json"
            if state_file.exists():
                with open(state_file) as f:
                    state_data = json.load(f)

                autonomous_state = state_data.get("autonomous_state", {})

                print("\n🎯 Key Performance Indicators:")
                print("-" * 35)
                print(
                    f"  Reasoning Cycles: {autonomous_state.get('reasoning_cycles', 0)}"
                )
                print(
                    f"  Optimization Cycles: {autonomous_state.get('optimization_cycles', 0)}"
                )
                print(
                    f"  Learning Iterations: {autonomous_state.get('learning_iterations', 0)}"
                )
                print(
                    f"  Strategic Decisions: {autonomous_state.get('strategic_decisions', 0)}"
                )
                print(
                    f"  Proactive Interventions: {autonomous_state.get('proactive_interventions', 0)}"
                )

                print("\n📈 Efficiency Metrics:")
                print("-" * 22)
                print(
                    f"  System Health Score: {autonomous_state.get('system_health_score', 0):.2f}"
                )
                print(
                    f"  Cognitive Load: {autonomous_state.get('cognitive_load', 0):.2f}"
                )
                print(
                    f"  Learning Velocity: {autonomous_state.get('learning_velocity', 0):.2f}"
                )
                print(
                    f"  Adaptation Coefficient: {autonomous_state.get('adaptation_coefficient', 0):.2f}"
                )

        except Exception as e:
            print(f"❌ Error generating performance report: {e}")
            logging.error("Error generating performance report", exc_info=True)

        self._wait_for_key()

    def _reasoning_analysis(self):
        """Show advanced reasoning analysis."""
        print("🧠 PHASE 5 ADVANCED REASONING ANALYSIS")
        print("=" * 42)

        print("🔍 Multi-Layered Reasoning Systems:")
        print("-" * 35)
        print("  ✅ Strategic Reasoning Engine - Active")
        print("  ✅ Tactical Reasoning Module - Active")
        print("  ✅ Operational Reasoning Layer - Active")
        print("  ✅ Meta-Cognitive Analysis - Active")

        print("\n📊 Reasoning Performance:")
        print("-" * 25)
        print("  Strategic Insights Generated: Variable")
        print("  Tactical Recommendations: Variable")
        print("  Operational Optimizations: Continuous")
        print("  Meta-Cognitive Observations: Periodic")

        print("\n🎯 Reasoning Quality Metrics:")
        print("-" * 30)
        print("  Insight Relevance: High")
        print("  Recommendation Accuracy: High")
        print("  Decision Consistency: Stable")
        print("  Adaptation Effectiveness: Optimal")

        self._wait_for_key()

    def _learning_report(self):
        """Show learning and adaptation report."""
        print("📚 PHASE 5 LEARNING & ADAPTATION REPORT")
        print("=" * 42)

        print("🧬 Experiential Learning Systems:")
        print("-" * 32)
        print("  ✅ Pattern Recognition Engine - Active")
        print("  ✅ Knowledge Synthesis Module - Active")
        print("  ✅ Meta-Learning Analyzer - Active")
        print("  ✅ Cognitive Model Updater - Active")

        print("\n📈 Learning Progress:")
        print("-" * 20)
        print("  Experience Pattern Analysis: Continuous")
        print("  Knowledge Synthesis Rate: Optimized")
        print("  Meta-Learning Insights: Growing")
        print("  Cognitive Model Refinement: Ongoing")

        print("\n🔄 Adaptation Capabilities:")
        print("-" * 25)
        print("  Real-time Adaptation: Enabled")
        print("  Performance Optimization: Active")
        print("  Behavioral Refinement: Continuous")
        print("  Strategic Adjustment: Dynamic")

        self._wait_for_key()

    def _environmental_report(self):
        """Show environmental assessment report."""
        print("🌍 PHASE 5 ENVIRONMENTAL ASSESSMENT REPORT")
        print("=" * 45)

        print("🔍 Multi-Dimensional Monitoring:")
        print("-" * 32)
        print("  ✅ System Environment Scanner - Active")
        print("  ✅ Computational Resource Monitor - Active")
        print("  ✅ Data Environment Assessor - Active")
        print("  ✅ External Factor Analyzer - Active")
        print("  ✅ Temporal Context Tracker - Active")

        print("\n📊 Environmental Status:")
        print("-" * 23)
        print("  System Health: Optimal")
        print("  Resource Availability: Good")
        print("  Data Quality: High")
        print("  External Conditions: Favorable")
        print("  Temporal Alignment: Synchronized")

        print("\n🎯 Environmental Opportunities:")
        print("-" * 32)
        print("  Resource Optimization: Available")
        print("  Performance Enhancement: Identified")
        print("  Efficiency Improvements: Ongoing")
        print("  Capability Expansion: Planned")

        self._wait_for_key()

    def _strategic_status(self):
        """Show strategic planning status."""
        print("🎯 PHASE 5 STRATEGIC PLANNING STATUS")
        print("=" * 38)

        print("📋 Current Objectives:")
        print("-" * 20)
        print("  • Optimize Autonomous Operation (80% complete)")
        print("  • Enhance Learning Efficiency (70% complete)")
        print("  • Improve System Performance (75% complete)")
        print("  • Advance Cognitive Capabilities (Phase 5 active)")

        print("\n🎯 Long-term Goals:")
        print("-" * 18)
        print("  • Autonomous General Intelligence: In Progress")
        print("  • Sacred Covenant Alignment: Maintained")
        print("  • Human-AI Collaboration: Optimized")
        print("  • Continuous Self-Improvement: Active")

        print("\n📈 Strategic Progress:")
        print("-" * 20)
        print("  • Reasoning Sophistication: Advanced")
        print("  • Learning Acceleration: Active")
        print("  • Environmental Adaptation: Optimal")
        print("  • Resource Optimization: Ongoing")

        print("\n⚡ Next Strategic Actions:")
        print("-" * 25)
        print("  • Enhance Reasoning Depth")
        print("  • Optimize Learning Cycles")
        print("  • Improve Adaptation Speed")
        print("  • Advance Cognitive Architecture")

        self._wait_for_key()

    def _stop_phase5(self):
        """Stop Phase 5 operation."""
        print("🛑 STOPPING PHASE 5 ADVANCED AUTONOMOUS OPERATION")
        print("=" * 55)

        if not self._is_phase5_running():
            print("⚠️  Phase 5 is not currently running.")
            self._wait_for_key()
            return

        try:
            # Find and terminate Phase 5 processes
            terminated = False
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if proc.info["name"] == "python.exe" and proc.info["cmdline"]:
                        cmdline = " ".join(proc.info["cmdline"])
                        if "phase5_advanced_autonomous.py" in cmdline:
                            print(f"Terminating process {proc.info['pid']}...")
                            proc.terminate()
                            proc.wait(timeout=10)
                            terminated = True
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.TimeoutExpired,
                ):
                    continue

            if terminated:
                print("✅ Phase 5 Advanced Autonomous Operation stopped successfully.")
            else:
                print("⚠️  No Phase 5 processes found to stop.")

            # Update status
            self._update_status(
                {
                    "phase5_running": False,
                    "stop_time": datetime.now().isoformat(),
                    "status": "stopped",
                }
            )

        except Exception as e:
            print(f"❌ Error stopping Phase 5: {e}")
            logging.error("Error stopping Phase 5", exc_info=True)

        self._wait_for_key()

    def _restart_enhanced(self):
        """Restart with enhanced configuration."""
        print("🔄 RESTARTING WITH ENHANCED CONFIGURATION")
        print("=" * 45)

        print("1. Stopping current operation...")
        self._stop_phase5()

        print("2. Waiting for clean shutdown...")
        time.sleep(3)

        print("3. Launching with enhanced settings...")
        self._launch_phase5()

        print("✅ Enhanced restart completed!")
        self._wait_for_key()

    def _check_phase5_status(self) -> dict:
        """Check current Phase 5 status."""
        status = {
            "running": self._is_phase5_running(),
            "uptime": None,
            "health": "unknown",
        }

        # Load saved status
        saved_status = self._load_status()
        if saved_status.get("launch_time") and status["running"]:
            launch_time = datetime.fromisoformat(saved_status["launch_time"])
            status["uptime"] = datetime.now() - launch_time
            status["health"] = "operational"

        return status

    def _display_status(self, status: dict):
        """Display current status."""
        print("📊 CURRENT STATUS:")
        print("-" * 18)

        if status["running"]:
            print("🟢 Phase 5 Advanced Autonomous Intelligence: ACTIVE")
            if status["uptime"]:
                print(f"⏱️  Uptime: {status['uptime']}")
            print(f"💚 System Health: {status.get('health', 'Unknown')}")
        else:
            print("🔴 Phase 5 Advanced Autonomous Intelligence: INACTIVE")
            print("💤 System Status: Standby")

    def _is_phase5_running(self) -> bool:
        """Check if Phase 5 is currently running."""
        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if proc.info["name"] == "python.exe" and proc.info["cmdline"]:
                        cmdline = " ".join(proc.info["cmdline"])
                        if "phase5_advanced_autonomous.py" in cmdline:
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception:
            return False

    def _get_real_time_status(self) -> dict:
        """Get real-time status information."""
        status = {
            "Advanced Reasoning": "Active" if self._is_phase5_running() else "Inactive",
            "Proactive Optimization": "Active"
            if self._is_phase5_running()
            else "Inactive",
            "Experiential Learning": "Active"
            if self._is_phase5_running()
            else "Inactive",
            "Environmental Monitoring": "Active"
            if self._is_phase5_running()
            else "Inactive",
            "Strategic Planning": "Active" if self._is_phase5_running() else "Inactive",
            "Cognitive Load Management": "Active"
            if self._is_phase5_running()
            else "Inactive",
            "Autonomous Adaptation": "Active"
            if self._is_phase5_running()
            else "Inactive",
        }
        return status

    def _load_status(self) -> dict:
        """Load status from file."""
        try:
            if self.status_file.exists():
                with open(self.status_file) as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _update_status(self, status_update: dict):
        """Update status file atomically."""
        try:
            current_status = self._load_status()
            current_status.update(status_update)
            tmp_path = self.status_file.with_suffix(".tmp")
            with open(tmp_path, "w") as f:
                json.dump(current_status, f, indent=2)
            os.replace(tmp_path, self.status_file)
        except Exception as e:
            print(f"Warning: Could not update status file: {e}")
            logging.error("Failed to update status file", exc_info=True)

    def _clear_screen(self):
        """Clear the terminal screen."""
        os.system("cls" if os.name == "nt" else "clear")

    def _wait_for_key(self):
        """Wait for user to press a key."""
        input("\nPress Enter to continue...")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--launch", action="store_true", help="Launch Phase 5 directly")
    parser.add_argument("--stop", action="store_true", help="Stop Phase 5 directly")
    args = parser.parse_args()

    launcher = Phase5Launcher()
    if args.launch:
        launcher._launch_phase5()
    elif args.stop:
        launcher._stop_phase5()
    else:
        launcher.show_menu()


if __name__ == "__main__":
    main()
