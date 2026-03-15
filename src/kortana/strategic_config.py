"""Strategic configuration system for Kortana's Sacred Trinity architecture.

This module defines the strategic configuration layer that governs
model selection, task categorization, and sacred principle alignment.
"""

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskCategory(Enum):
    CREATIVE_WRITING = "creative_writing"
    TECHNICAL_ANALYSIS = "technical_analysis"
    PROBLEM_SOLVING = "problem_solving"
    COMMUNICATION = "communication"
    RESEARCH = "research"
    CODE_GENERATION = "code_generation"
    ETHICAL_REASONING = "ethical_reasoning"
    ORACLE = "oracle"  # General high-level reasoning
    SWIFT_RESPONDER = "swift_responder"  # Quick, low-latency responses
    MEMORY_WEAVER = "memory_weaver"  # Processing large contexts, summarization
    DEV_AGENT = "dev_agent"  # Code tasks, technical instructions
    BUDGET_WORKHORSE = "budget_workhorse"  # Cost-optimized tasks
    MULTIMODAL_SEER = "multimodal_seer"  # Image/audio processing
    DEVELOPMENT = "development"  # Alias for DEV_AGENT
    REASONING = "reasoning"  # Alias for ORACLE
    CREATIVE = "creative"  # Alias for CREATIVE_WRITING


@dataclass
class PerformanceMetric:
    """Represents performance data for a single task execution."""

    model_used: str
    task_category: TaskCategory
    # E.g., 1.0 for success, 0.0 for failure (can be nuanced)
    success_rate: float
    quality_score: float  # E.g., 0.0 to 1.0 or based on specific rubrics
    cost_effectiveness: float  # E.g., normalized cost per task
    time_efficiency: float  # E.g., normalized latency or tokens/sec
    human_validation: float | None = None  # Human feedback score
    sacred_alignment_achieved: dict[str, float] | None = (
        None  # How well principles were embodied in this response
    )
    timestamp: float = time.time()
    metadata: dict | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the performance metric to a dictionary representation.

        Returns:
            Dictionary containing all performance metric data
        """
        data = asdict(self)
        try:
            data["task_category"] = self.task_category.value
        except AttributeError:
            data["task_category"] = str(self.task_category)
        return data


@dataclass
class SacredPrinciple(Enum):
    """Represents core Sacred Trinity principles."""

    WISDOM = "wisdom"
    COMPASSION = "compassion"
    TRUTH = "truth"
    EFFICIENCY = "efficiency"


@dataclass
class SacredPrincipleConfig:
    """Configuration for a sacred principle."""

    weight: float
    validation_score: float
    active: bool


class UltimateLivingSacredConfig:
    """Ultimate living configuration system representing Kor'tana's strategic consciousness.

    This class manages Sacred Trinity optimization, task intelligence, and
    performance tracking for the entire Kortana system.
    """

    def __init__(
        self, performance_history_path: str = "data/performance_history.jsonl"
    ):
        self.performance_history_path = performance_history_path
        self.performance_history: list[PerformanceMetric] = (
            self._load_performance_history()
        )

        # Sacred Trinity - Initially based on conceptual understanding,
        # optimized by performance
        self.sacred_trinity: dict[str, SacredPrincipleConfig] = {
            "wisdom": SacredPrincipleConfig(
                weight=0.95, validation_score=0.90, active=True
            ),
            "compassion": SacredPrincipleConfig(
                weight=0.92, validation_score=0.93, active=True
            ),
            "truth": SacredPrincipleConfig(
                weight=0.93, validation_score=0.91, active=True
            ),
        }

        # Initial strategic scores
        self.initial_sacred_alignment_scores: dict[str, dict[str, float]] = {
            "gpt-4.1-nano": {"wisdom": 0.8, "truth": 0.8, "compassion": 0.6},
            "x-ai/grok-3-mini-beta": {"wisdom": 0.7, "compassion": 0.75, "truth": 0.8},
            "gemini-2.5-flash": {"wisdom": 0.7, "compassion": 0.75, "truth": 0.8},
            "deepseek-chat-v3-openrouter": {
                "wisdom": 0.7,
                "compassion": 0.6,
                "truth": 0.7,
            },
            "noromaid-20b-openrouter": {"wisdom": 0.6, "compassion": 0.9, "truth": 0.7},
            "meta-llama/llama-4-scout-openrouter": {
                "wisdom": 0.7,
                "compassion": 0.7,
                "truth": 0.9,
            },
            "meta-llama/llama-4-maverick-openrouter": {
                "wisdom": 0.8,
                "compassion": 0.6,
                "truth": 0.85,
            },
            "qwen3-235b-openrouter": {"wisdom": 0.6, "compassion": 0.7, "truth": 0.8},
            "gpt-4o-mini-openai": {"wisdom": 0.75, "compassion": 0.7, "truth": 0.75},
            "claude-3-haiku-openrouter": {
                "wisdom": 0.7,
                "compassion": 0.8,
                "truth": 0.75,
            },
            "gemini-2.0-flash-lite": {"wisdom": 0.65, "compassion": 0.7, "truth": 0.68},
        }

        self.initial_archetype_fits: dict[str, dict[str, float]] = {
            "gpt-4.1-nano": {
                "oracle": 0.7,
                "swift_responder": 0.8,
                "memory_weaver": 0.7,
                "dev_agent": 0.8,
                "budget_workhorse": 0.7,
                "multimodal_seer": 0.6,
            }
            # ... (truncated for brevity in setup)
        }

        self.performance_thresholds: dict[str, float] = {
            "minimum_success_rate": 0.85,
            "quality_threshold": 0.80,
            "cost_effectiveness_target": 0.75,
            "human_validation_minimum": 0.85,
        }

        self.adaptive_settings: dict[str, float] = {
            "learning_rate": 0.0015,
            "adaptation_threshold": 0.87,
            "healing_interval": 240,
            "performance_window": 50,
        }

    def _load_performance_history(self) -> list[PerformanceMetric]:
        history = []
        if os.path.exists(self.performance_history_path):
            with open(self.performance_history_path) as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        data["task_category"] = TaskCategory(data["task_category"])
                        history.append(PerformanceMetric(**data))
                    except Exception as e:
                        logger.error(f"Error loading history: {e}")
        return history

    def _save_performance_history(self):
        os.makedirs(os.path.dirname(self.performance_history_path), exist_ok=True)
        with open(self.performance_history_path, "w") as f:
            for metric in self.performance_history:
                f.write(json.dumps(metric.to_dict()) + "\n")

    def update_performance_data(self, performance_metric: PerformanceMetric):
        self.performance_history.append(performance_metric)
        self._save_performance_history()

    def get_task_guidance(self, task_category: TaskCategory) -> dict[str, Any]:
        prioritized_principles = []
        # Logic here...
        return {
            "prioritize_principles": prioritized_principles,
            "quality_threshold": 0.8,
        }
