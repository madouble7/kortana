"""
KOR'TANA Autonomous System Monitor & Self-Awareness Engine

Continuously monitors autonomous system performance, identifies improvement
opportunities, and autonomously enhances the system's capabilities.

Features:
- Real-time task execution monitoring
- Performance metrics aggregation
- Autonomous improvement analysis
- Self-optimization recommendations
- Continuous learning from execution patterns
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Callable
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any

from src.kortana.database import get_db_session
from src.kortana.logger import get_logger
from src.kortana.services.autonomy_code_patcher import AutonomyCodePatcher
from src.kortana.services.gemini import gemini_service

logger = get_logger(__name__)


class AutonomousSystemMonitor:
    """Monitor and analyze KOR'TANA's autonomous operations."""

    def __init__(
        self,
        db_session_factory: Callable[[], Any] | None = None,
        patcher_cls: type[AutonomyCodePatcher] = AutonomyCodePatcher,
    ) -> None:
        self.metrics: dict[str, Any] = {
            "tasks_executed": 0,
            "tasks_successful": 0,
            "tasks_failed": 0,
            "github_issues_analyzed": 0,
            "prs_created": 0,
            "code_improvements": 0,
            "errors_encountered": [],
            "cycle_times": [],
            "last_check": None,
        }
        self.improvement_opportunities: list[dict[str, Any]] = []
        self.learning_log: list[dict[str, Any]] = []
        self._db_session_factory = db_session_factory or get_db_session
        self._patcher_cls = patcher_cls
        self._background_patch_tasks: set[asyncio.Task[None]] = set()

    async def monitor_cycle_execution(
        self, cycle_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Monitor a single autonomous cycle execution.

        Args:
            cycle_data: Data from completed cycle including timing, results, errors

        Returns:
            Analysis of cycle execution with recommendations
        """
        try:
            logger.info(
                "Monitoring cycle execution: %s",
                cycle_data.get("cycle_type", "unknown"),
            )

            cycle_type = cycle_data.get("cycle_type", "unknown")
            status = cycle_data.get("status", "unknown")
            duration = cycle_data.get("duration", 0)
            errors = cycle_data.get("errors", [])
            tasks_processed = cycle_data.get("tasks_processed", 0)

            self.metrics["tasks_executed"] += 1
            if status == "completed":
                self.metrics["tasks_successful"] += 1
            elif status == "failed":
                self.metrics["tasks_failed"] += 1

            if errors:
                self.metrics["errors_encountered"].extend(errors)

            self.metrics["cycle_times"].append(duration)
            self.metrics["last_check"] = datetime.utcnow().isoformat()

            analysis = {
                "cycle_type": cycle_type,
                "status": status,
                "duration_seconds": duration,
                "tasks_processed": tasks_processed,
                "success_rate": (
                    self.metrics["tasks_successful"] / self.metrics["tasks_executed"]
                    if self.metrics["tasks_executed"] > 0
                    else 0
                ),
                "average_cycle_time": (
                    sum(self.metrics["cycle_times"]) / len(self.metrics["cycle_times"])
                    if self.metrics["cycle_times"]
                    else 0
                ),
                "issues_identified": [],
                "optimizations_available": [],
            }

            if duration > 30:
                analysis["issues_identified"].append(
                    f"High cycle duration: {duration}s (target: <10s)"
                )

            if errors:
                analysis["issues_identified"].append(
                    f"Errors in cycle: {len(errors)} encountered"
                )

            if analysis["success_rate"] < 0.95:
                analysis["optimizations_available"].append("Improve error handling")

            if len(self.metrics["errors_encountered"]) > 10:
                analysis["optimizations_available"].append(
                    "Review recurring error patterns and implement fixes"
                )

            return analysis
        except Exception as exc:
            logger.error(f"Error monitoring cycle: {str(exc)}")
            return {"status": "error", "message": str(exc)}

    def _normalized_error_entries(self) -> list[dict[str, Any]]:
        """Normalize stored error payloads into a consistent structure."""
        normalized: list[dict[str, Any]] = []

        for raw_error in self.metrics["errors_encountered"]:
            if isinstance(raw_error, dict):
                payload = dict(raw_error)
            else:
                payload = {"message": str(raw_error)}

            error_type = str(
                payload.get("type")
                or payload.get("error_type")
                or payload.get("name")
                or "unknown"
            ).strip() or "unknown"
            error_message = str(
                payload.get("message")
                or payload.get("error_message")
                or payload.get("detail")
                or payload.get("exception")
                or error_type
            ).strip() or error_type
            target_file = self._normalize_patch_target_file(
                payload.get("target_file")
                or payload.get("file")
                or payload.get("file_path")
                or payload.get("path")
            )

            normalized.append(
                {
                    "error_type": error_type,
                    "error_message": error_message,
                    "target_file": target_file,
                    "raw": payload,
                }
            )

        return normalized

    @staticmethod
    def _normalize_patch_target_file(raw_target: Any) -> str | None:
        """Normalize file hints to repo-root-relative backend Python paths."""
        if not raw_target:
            return None

        target = str(raw_target).strip().replace("\\", "/")
        if not target.endswith(".py"):
            return None

        if "/backend/" in target:
            target = "backend/" + target.split("/backend/", 1)[1].lstrip("/")
        elif target.startswith("backend/"):
            pass
        elif target.startswith("src/") or target.startswith("tests/"):
            target = f"backend/{target}"
        else:
            return None

        normalized = PurePosixPath(target)
        if ".." in normalized.parts:
            return None

        return normalized.as_posix()

    async def identify_improvements(self) -> list[dict[str, Any]]:
        """
        Analyze autonomous system performance and identify improvement opportunities.

        Returns:
            List of recommended improvements
        """
        try:
            improvements: list[dict[str, Any]] = []

            if self.metrics["errors_encountered"]:
                error_summaries: dict[str, dict[str, Any]] = {}
                for error in self._normalized_error_entries():
                    error_type = error["error_type"]
                    summary = error_summaries.setdefault(
                        error_type,
                        {
                            "frequency": 0,
                            "sample_error_message": error["error_message"],
                            "target_file": error["target_file"],
                        },
                    )
                    summary["frequency"] += 1
                    if not summary["target_file"] and error["target_file"]:
                        summary["target_file"] = error["target_file"]
                    if (
                        summary["sample_error_message"] == error_type
                        and error["error_message"] != error_type
                    ):
                        summary["sample_error_message"] = error["error_message"]

                for error_type, summary in sorted(
                    error_summaries.items(),
                    key=lambda item: int(item[1]["frequency"]),
                    reverse=True,
                )[:3]:
                    count = int(summary["frequency"])
                    improvements.append(
                        {
                            "type": "error_reduction",
                            "target": error_type,
                            "frequency": count,
                            "impact": "high" if count > 5 else "medium",
                            "recommendation": f"Implement handling for {error_type}",
                            "sample_error_message": summary["sample_error_message"],
                            "target_file": summary["target_file"],
                            "patchable": summary["target_file"] is not None,
                        }
                    )

            if self.metrics["cycle_times"]:
                avg_time = sum(self.metrics["cycle_times"]) / len(
                    self.metrics["cycle_times"]
                )
                max_time = max(self.metrics["cycle_times"])

                if max_time > avg_time * 2:
                    improvements.append(
                        {
                            "type": "performance",
                            "target": "cycle_time",
                            "current": f"{max_time:.2f}s",
                            "baseline": f"{avg_time:.2f}s",
                            "recommendation": "Identify and optimize slow cycle phases",
                        }
                    )

            if self.metrics["tasks_executed"] > 0:
                success_rate = (
                    self.metrics["tasks_successful"] / self.metrics["tasks_executed"]
                )
                if success_rate < 0.9:
                    improvements.append(
                        {
                            "type": "reliability",
                            "target": "task_success",
                            "current": f"{success_rate * 100:.1f}%",
                            "goal": "95%+",
                            "recommendation": "Review and improve task error handling",
                        }
                    )

            self.improvement_opportunities = improvements
            return improvements

        except Exception as exc:
            logger.error(f"Error identifying improvements: {str(exc)}")
            return []

    def _select_patch_candidate(
        self, critical_issues: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Pick the first actionable high-frequency error with a concrete target."""
        for issue in critical_issues:
            if issue.get("type") != "error_reduction":
                continue

            target_file = issue.get("target_file")
            if not target_file:
                continue

            error_type = str(issue.get("target") or "unknown").strip() or "unknown"
            error_message = (
                str(issue.get("sample_error_message") or error_type).strip()
                or error_type
            )
            frequency = int(issue.get("frequency", 0))

            return {
                "error_type": error_type,
                "error_message": error_message,
                "target_file": target_file,
                "frequency": frequency,
            }

        return None

    def _queue_patch_candidate(self, candidate: dict[str, Any]) -> bool:
        """Run the patcher in the background without blocking the monitor loop."""
        task = asyncio.create_task(self._run_autonomy_patcher(candidate))
        self._background_patch_tasks.add(task)
        task.add_done_callback(self._finalize_background_patch_task)
        return True

    def _finalize_background_patch_task(self, task: asyncio.Task[None]) -> None:
        self._background_patch_tasks.discard(task)
        try:
            task.result()
        except Exception as exc:
            logger.error(f"Autonomy patch background task failed: {exc}")

    async def _run_autonomy_patcher(self, candidate: dict[str, Any]) -> None:
        async with self._db_session_factory() as db:
            patcher = self._patcher_cls(db)
            success = await patcher.attempt_auto_fix(
                error_type=candidate["error_type"],
                error_message=candidate["error_message"],
                target_file=candidate["target_file"],
                context={
                    "reason": (
                        "Detected as a high-impact recurring error during the "
                        "autonomous monitoring cycle."
                    ),
                    "frequency": candidate["frequency"],
                    "source": "autonomous_monitor",
                },
            )
            if success:
                logger.info(
                    "KOR'TANA AUTO-REPAIR: Queued fix succeeded for %s",
                    candidate["target_file"],
                )
            else:
                logger.warning(
                    "KOR'TANA AUTO-REPAIR: Queued fix was rejected for %s",
                    candidate["target_file"],
                )

    async def generate_self_awareness_report(self) -> dict[str, Any]:
        """
        Generate comprehensive self-awareness report of autonomous system.

        Returns:
            Detailed report of system state, performance, and recommendations
        """
        try:
            improvements = await self.identify_improvements()

            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "system_status": {
                    "total_cycles": self.metrics["tasks_executed"],
                    "successful": self.metrics["tasks_successful"],
                    "failed": self.metrics["tasks_failed"],
                    "success_rate": (
                        (
                            self.metrics["tasks_successful"]
                            / self.metrics["tasks_executed"]
                            * 100
                        )
                        if self.metrics["tasks_executed"] > 0
                        else 0
                    ),
                },
                "performance": {
                    "average_cycle_time_seconds": (
                        sum(self.metrics["cycle_times"])
                        / len(self.metrics["cycle_times"])
                        if self.metrics["cycle_times"]
                        else 0
                    ),
                    "errors_total": len(self.metrics["errors_encountered"]),
                    "last_check": self.metrics["last_check"],
                },
                "improvements": improvements,
                "autonomous_capabilities": {
                    "github_monitoring": "✅ Active (5-min cycles)",
                    "code_analysis": "✅ Active (Gemini AI)",
                    "pr_creation": "✅ Ready",
                    "self_improvement": "✅ Active",
                    "error_recovery": "✅ Implemented",
                },
            }

            return report

        except Exception as exc:
            logger.error(f"Error generating report: {str(exc)}")
            return {"status": "error", "message": str(exc)}

    async def learn_and_adapt(self, execution_data: dict[str, Any]) -> dict[str, Any]:
        """
        Learn from execution data and adapt autonomous system.

        Args:
            execution_data: Data from recent autonomous cycles

        Returns:
            Adaptation results and applied improvements
        """
        try:
            logger.info("🧠 Autonomous system learning phase started")

            patterns = await self._extract_patterns(execution_data)

            prompt = f"""
Based on the following autonomous system execution data, suggest specific improvements
to make the system more efficient and effective:

Execution Data:
{json.dumps(execution_data, indent=2, default=str)}

Patterns Identified:
{json.dumps(patterns, indent=2, default=str)}

Provide 3-5 concrete, implementable improvements to the autonomous system.
Focus on:
1. Performance optimization
2. Error reduction
3. Feature enhancement
4. Self-awareness improvement
"""

            recommendations = await gemini_service.analyze_text(prompt)

            learning_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "patterns": patterns,
                "recommendations": recommendations,
                "status": "processed",
            }

            self.learning_log.append(learning_entry)

            return {
                "status": "completed",
                "patterns_identified": patterns,
                "recommendations": recommendations,
                "learning_entries_total": len(self.learning_log),
            }

        except Exception as exc:
            logger.error(f"Error in learning phase: {str(exc)}")
            return {"status": "error", "message": str(exc)}

    async def _extract_patterns(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract patterns from execution data."""
        patterns: dict[str, list[Any]] = {
            "common_errors": [],
            "peak_activity_times": [],
            "performance_trends": [],
            "success_patterns": [],
        }

        if data.get("errors"):
            error_types: dict[str, int] = {}
            for error in data["errors"]:
                error_type = str(error).split(":")[0]
                error_types[error_type] = error_types.get(error_type, 0) + 1

            patterns["common_errors"] = sorted(
                error_types.items(), key=lambda item: item[1], reverse=True
            )[:3]

        return patterns

    async def initiate_self_optimization(self) -> dict[str, Any]:
        """
        Initiate autonomous self-optimization cycle.

        Returns:
            Status of optimization initiation
        """
        try:
            logger.info("🚀 Initiating autonomous self-optimization")

            awareness = await self.generate_self_awareness_report()
            critical_issues = [
                imp
                for imp in awareness.get("improvements", [])
                if imp.get("impact") == "high"
            ]
            patch_candidate_queued = False

            if critical_issues:
                logger.warning(f"Critical issues identified: {len(critical_issues)}")

                patch_candidate = self._select_patch_candidate(critical_issues)
                if patch_candidate:
                    logger.info(
                        "KOR'TANA AUTO-REPAIR: High-impact error detected: %s "
                        "(freq=%s, target=%s). Handing over to patcher.",
                        patch_candidate["error_type"],
                        patch_candidate["frequency"],
                        patch_candidate["target_file"],
                    )
                    patch_candidate_queued = self._queue_patch_candidate(
                        patch_candidate
                    )
                else:
                    logger.info(
                        "High-impact errors were found, but none had a concrete "
                        "backend Python target file for autonomous patching."
                    )
            else:
                logger.info("System operating within normal parameters")

            return {
                "status": "initiated",
                "awareness_report_generated": True,
                "critical_issues": len(critical_issues),
                "optimization_in_progress": True,
                "patch_candidate_queued": patch_candidate_queued,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as exc:
            logger.error(f"Error initiating optimization: {str(exc)}")
            return {"status": "error", "message": str(exc)}


_monitor: AutonomousSystemMonitor | None = None


def get_monitor() -> AutonomousSystemMonitor:
    """Get or create the global autonomous system monitor."""
    global _monitor
    if _monitor is None:
        _monitor = AutonomousSystemMonitor()
    return _monitor


async def monitor_autonomous_system() -> dict[str, Any]:
    """
    Main monitoring function to be called periodically.

    Returns:
        Monitoring results
    """
    monitor = get_monitor()
    report = await monitor.generate_self_awareness_report()
    improvements = await monitor.identify_improvements()

    if improvements:
        optimization = await monitor.initiate_self_optimization()
    else:
        optimization = {"status": "not_needed"}

    return {
        "monitor_timestamp": datetime.utcnow().isoformat(),
        "awareness_report": report,
        "improvements": improvements,
        "optimization_status": optimization,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="KOR'TANA Autonomous System Monitor")
    parser.add_argument("--optimize", action="store_true", help="Run self-optimization")
    args = parser.parse_args()

    monitor = get_monitor()
    if args.optimize:
        print("Starting KOR'TANA Autonomous Self-Optimization...")
        data = {"cycles": [], "error_rate": 0.05, "latency": 1500}
        result = await monitor.learn_and_adapt(data)
        print(f"Optimization Status: {result['status']}")
        print(f"Recommendations: {result['recommendations']}")
    else:
        report = await monitor.generate_self_awareness_report()
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
