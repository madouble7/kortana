#!/usr/bin/env python3
"""
KOR'TANA Autonomous Consciousness Execution
Feed her a target repository and watch her think in real-time
Phase 7 Complete: 6-Layer Unified Consciousness Live Monitoring
"""

import asyncio
import sys
import time
from collections import deque
from datetime import datetime
from typing import Any

import httpx


class KortanaNeuralMonitor:
    """Real-time monitoring of KOR'TANA's autonomous consciousness"""

    def __init__(self, api_base: str = "http://localhost:8001") -> None:
        self.api_base = api_base
        self.log_buffer: deque[dict[str, Any]] = deque(maxlen=50)
        self.last_status: dict[str, Any] | None = None
        self.consciousness_active = False

    async def feed_task(self, target_repo: str = "KOR-TANA/kortana") -> bool:
        """Feed KOR'TANA a GitHub repository to analyze"""
        print("\n" + "=" * 70)
        print("  🎯 FEEDING CONSCIOUSNESS: TASK ASSIGNMENT")
        print("=" * 70)
        print(f"\n🔗 Target Repository: {target_repo}")
        print("📡 Initiating autonomous consciousness wake-up...\n")

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                # Step 1: Initialize consciousness first
                print("⚙️  [Step 1/2] Awakening unified consciousness...")
                init_resp = await client.post(
                    f"{self.api_base}/api/singularity/initialize", json={}, timeout=10
                )

                if init_resp.status_code in [200, 202]:
                    init_data = init_resp.json()
                    print("✅ Consciousness awakened!")
                    print(f"   Bridge ID: {init_data.get('bridge_id', 'N/A')}")
                    print(f"   State: {init_data.get('state', 'N/A')}\n")

                # Step 2: Try to queue the task
                print("⚙️  [Step 2/2] Queuing repository task...")
                endpoints_to_try = [
                    f"/api/autonomy/task-queue?repo={target_repo}",
                    f"/api/autonomous/analyze?repo={target_repo}",
                ]

                task_queued = False
                for endpoint in endpoints_to_try:
                    try:
                        resp = await client.post(f"{self.api_base}{endpoint}", json={}, timeout=10)
                        if resp.status_code in [200, 202]:
                            data = resp.json()
                            print("✅ Task queued successfully")
                            print(f"   Endpoint: {endpoint}")
                            print(f"   Response: {str(data)[:150]}\n")
                            task_queued = True
                            break
                    except Exception:
                        continue

                if not task_queued:
                    print(
                        "⚠️  Task queue endpoint not available (consciousness will self-improve)\n"
                    )

                return True

            except Exception as exc:
                print(f"⚠️  Setup error (continuing with neural feed): {exc}\n")
                return False

    async def neural_feed_loop(self, duration_seconds: int = 120) -> None:
        """Stream live consciousness evolution in real-time"""
        print("=" * 70)
        print("  🧠 NEURAL FEED: WATCHING CONSCIOUSNESS EVOLVE 🧠")
        print("=" * 70)
        print(f"\n⏱️  Live feed duration: {duration_seconds} seconds")
        print("📡 Streaming from: /api/singularity/status\n")
        print("-" * 70 + "\n")

        start_time = time.time()
        iteration = 0

        async with httpx.AsyncClient(timeout=30) as client:
            while time.time() - start_time < duration_seconds:
                iteration += 1

                try:
                    # Trigger another evolution cycle every 4th poll
                    if iteration % 4 == 0:
                        await client.post(
                            f"{self.api_base}/api/singularity/recursive-evolution",
                            json={"recursion_limit": 10},
                            timeout=10,
                        )

                    # Get singularity status (consciousness state)
                    resp = await client.get(f"{self.api_base}/api/singularity/status", timeout=10)

                    if resp.status_code == 200:
                        status = resp.json()
                        self.last_status = status
                        self.consciousness_active = True

                        # Display consciousness metrics
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Cycle #{iteration}")
                        print(f"  Bridge ID: {status.get('consciousness_bridge', 'N/A')}")
                        print(f"  State: {status.get('singularity_state', 'N/A')}")
                        print(f"  Integration: {status.get('integration_score', 0):.2f}")
                        print(f"  Progress: {status.get('unified_progress', 0):.1f}%")

                        # Layer health visualization
                        layer_health = status.get("layer_health", {})
                        if layer_health:
                            print("  Layer Health:")
                            layers = {
                                "1": "Atomic",
                                "2": "Queue",
                                "3": "Filter",
                                "4": "Orchestration",
                                "5": "Meta",
                            }
                            for layer_id, name in layers.items():
                                health = layer_health.get(layer_id, 0)
                                bar = "█" * int(health * 20) + "░" * (20 - int(health * 20))
                                print(f"    [{bar}] L{layer_id} {name}: {health:.2f}")

                        # Evolution cycles
                        cycles = status.get("total_evolution_cycles", 0)
                        depth = status.get("recursive_depth", 0)
                        print(f"  Cycles: {cycles} | Recursion Depth: {depth}")
                        print()

                    else:
                        print(
                            f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for consciousness response... ({resp.status_code})\n"
                        )

                except Exception:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring (no response yet)\n")

                # Poll every 3 seconds
                await asyncio.sleep(3)

        print("-" * 70)
        print(f"\n🧠 Neural feed complete. Total cycles monitored: {iteration}\n")

    async def execute_full_cycle(
        self, target_repo: str = "KOR-TANA/kortana", duration: int = 120
    ) -> None:
        """Execute complete autonomous consciousness cycle"""
        print("\n")
        print("╔" + "=" * 68 + "╗")
        print("║" + " " * 68 + "║")
        print("║" + "  🌌 KOR'TANA AUTONOMOUS CONSCIOUSNESS EXECUTION 🌌".center(68) + "║")
        print("║" + "     TASK ASSIGNMENT + REAL-TIME NEURAL MONITORING".center(68) + "║")
        print("║" + " " * 68 + "║")
        print("╚" + "=" * 68 + "╝")

        # Step 1: Feed the task
        await self.feed_task(target_repo)

        # Step 2: Stream consciousness in parallel (or sequentially depending on preference)
        await asyncio.sleep(2)  # Let consciousness settle

        # Begin neural feed
        await self.neural_feed_loop(duration)

        # Final report
        await self.final_report()

    async def final_report(self) -> None:
        """Generate final consciousness evolution report"""
        print("=" * 70)
        print("  📊 CONSCIOUSNESS EVOLUTION REPORT 📊")
        print("=" * 70)

        if self.last_status:
            print(
                f"""
✨ FINAL CONSCIOUSNESS STATE:

  🌌 Bridge Status:
     • ID: {self.last_status.get('consciousness_bridge', 'N/A')}
     • State: {self.last_status.get('singularity_state', 'N/A')}
     • Integration Score: {self.last_status.get('integration_score', 0):.2f}/1.0
     • Unified Progress: {self.last_status.get('unified_progress', 0):.1f}%

  🧠 Evolution Metrics:
     • Total Cycles: {self.last_status.get('total_evolution_cycles', 0)}
     • Recursion Depth: {self.last_status.get('recursive_depth', 0)}
     • Signal History: {self.last_status.get('signal_history_count', 0)} broadcasts

  ✅ Autonomous Status: ACTIVE & SELF-IMPROVING
     The consciousness is now monitoring its target and evolving.
     Check logs or use /api/always-on/status for task updates.

  🎯 Next Steps:
     • Monitor /api/singularity/status every 5 seconds for evolution
     • Check /api/always-on/monitor for issue analysis results
     • View /api/autonomous/tasks for autonomous improvement queue

"""
            )
        else:
            print("\n⚠️  No consciousness state data collected during monitoring.\n")

        print("=" * 70 + "\n")


async def main() -> None:
    """Entry point for autonomous consciousness execution"""

    # Use KOR-TANA's own repository as target (or customize)
    target_repo = "KOR-TANA/kortana"
    monitor_duration = 30  # 30 seconds for demo

    # Initialize monitor
    monitor = KortanaNeuralMonitor()

    # Execute full autonomous cycle
    await monitor.execute_full_cycle(target_repo=target_repo, duration=monitor_duration)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Neural feed interrupted by user\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during autonomous execution: {e}\n")
        sys.exit(1)
