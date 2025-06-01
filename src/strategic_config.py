import json
import os
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

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
    human_validation: Optional[float] = None  # Human feedback score
    sacred_alignment_achieved: Optional[Dict[str, float]] = (
        None  # How well principles were embodied in this response
    )
    timestamp: float = time.time()
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["task_category"] = self.task_category.value
        return data


@dataclass
class SacredPrinciple:
    """Represents a core Sacred Trinity principle."""

    weight: float
    validation_score: (
        float  # Confidence/how well we understand this principle's application
    )
    active: bool


class UltimateLivingSacredConfig:
    """
    Ultimate living configuration system representing Kor'tana's strategic consciousness.
    Manages Sacred Trinity optimization, task intelligence, and performance tracking.
    """

    def __init__(
        self, performance_history_path: str = "data/performance_history.jsonl"
    ):
        self.performance_history_path = performance_history_path
        self.performance_history: List[PerformanceMetric] = (
            self._load_performance_history()
        )

        # Sacred Trinity - Initially based on conceptual understanding,
        # optimized by performance
        self.sacred_trinity: Dict[str, SacredPrinciple] = {
            "wisdom": SacredPrinciple(weight=0.95, validation_score=0.90, active=True),
            "compassion": SacredPrinciple(
                weight=0.92, validation_score=0.93, active=True
            ),
            "truth": SacredPrinciple(weight=0.93, validation_score=0.91, active=True),
        }

        # Initial strategic scores - Will be augmented by real performance data over time
        # Stored internally initially due to file edit issues with
        # models_config.json
        self.initial_sacred_alignment_scores: Dict[str, Dict[str, float]] = {
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

        self.initial_archetype_fits: Dict[str, Dict[str, float]] = {
            # Scores from 0 to 1, higher is better fit
            # Archetypes: oracle, swift_responder, memory_weaver, dev_agent,
            # budget_workhorse, multimodal_seer
            "gpt-4.1-nano": {
                "oracle": 0.7,
                "swift_responder": 0.8,
                "memory_weaver": 0.7,
                "dev_agent": 0.8,
                "budget_workhorse": 0.7,
                "multimodal_seer": 0.6,
            },
            "x-ai/grok-3-mini-beta": {
                "oracle": 0.8,
                "swift_responder": 0.7,
                "memory_weaver": 0.6,
                "dev_agent": 0.9,
                "budget_workhorse": 0.75,
                "multimodal_seer": 0.7,
            },
            "gemini-2.5-flash": {
                "oracle": 0.6,
                "swift_responder": 0.9,
                "memory_weaver": 0.8,
                "dev_agent": 0.5,
                "budget_workhorse": 0.85,
                "multimodal_seer": 0.6,
            },
            "deepseek-chat-v3-openrouter": {
                "oracle": 0.6,
                "swift_responder": 0.7,
                "memory_weaver": 0.6,
                "dev_agent": 0.9,
                "budget_workhorse": 0.7,
                "multimodal_seer": 0.5,
            },
            "noromaid-20b-openrouter": {
                "oracle": 0.8,
                "swift_responder": 0.6,
                "memory_weaver": 0.7,
                "dev_agent": 0.4,
                "budget_workhorse": 0.6,
                "multimodal_seer": 0.5,
            },
            "meta-llama/llama-4-scout-openrouter": {
                "oracle": 0.7,
                "swift_responder": 0.8,
                "memory_weaver": 0.9,
                "dev_agent": 0.7,
                "budget_workhorse": 0.75,
                "multimodal_seer": 0.8,
            },
            "meta-llama/llama-4-maverick-openrouter": {
                "oracle": 0.75,
                "swift_responder": 0.7,
                "memory_weaver": 0.75,
                "dev_agent": 0.85,
                "budget_workhorse": 0.7,
                "multimodal_seer": 0.75,
            },
            "qwen3-235b-openrouter": {
                "oracle": 0.65,
                "swift_responder": 0.75,
                "memory_weaver": 0.7,
                "dev_agent": 0.7,
                "budget_workhorse": 0.65,
                "multimodal_seer": 0.7,
            },
            "gpt-4o-mini-openai": {
                "oracle": 0.7,
                "swift_responder": 0.85,
                "memory_weaver": 0.7,
                "dev_agent": 0.8,
                "budget_workhorse": 0.75,
                "multimodal_seer": 0.85,
            },
            "claude-3-haiku-openrouter": {
                "oracle": 0.75,
                "swift_responder": 0.8,
                "memory_weaver": 0.7,
                "dev_agent": 0.7,
                "budget_workhorse": 0.7,
                "multimodal_seer": 0.75,
            },
            "gemini-2.0-flash-lite": {
                "oracle": 0.6,
                "swift_responder": 0.9,
                "memory_weaver": 0.65,
                "dev_agent": 0.5,
                "budget_workhorse": 0.9,
                "multimodal_seer": 0.6,
            },
        }

        # Performance thresholds and adaptive settings (placeholders for now)
        self.performance_thresholds: Dict[str, float] = {
            "minimum_success_rate": 0.85,
            "quality_threshold": 0.80,
            "cost_effectiveness_target": 0.75,
            "human_validation_minimum": 0.85,
        }

        self.adaptive_settings: Dict[str, float] = {
            "learning_rate": 0.0015,
            "adaptation_threshold": 0.87,
            "healing_interval": 240,
            "performance_window": 50,
        }

    def _load_performance_history(self) -> List[PerformanceMetric]:
        """Loads performance history from a JSONL file."""
        history = []
        if os.path.exists(self.performance_history_path):
            with open(self.performance_history_path, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        # Convert task_category string back to Enum member
                        data["task_category"] = TaskCategory(data["task_category"])
                        # Convert SacredPrinciple dicts back to objects if they
                        # were saved as dicts
                        if data.get("sacred_alignment_achieved") and isinstance(
                            data["sacred_alignment_achieved"], dict
                        ):
                            # Assuming principles are just names mapped to
                            # scores
                            pass  # Keep as dict of scores
                        history.append(PerformanceMetric(**data))
                    except json.JSONDecodeError as e:
                        logger.error(
                            f"Error decoding performance history line: {line.strip()} - {e}"
                        )
                    except ValueError as e:
                        logger.error(
                            f"Error parsing performance history data: {line.strip()} - {e}"
                        )
        return history

    def _save_performance_history(self):
        """Saves performance history to a JSONL file."""
        os.makedirs(os.path.dirname(self.performance_history_path), exist_ok=True)
        with open(self.performance_history_path, "w") as f:
            for metric in self.performance_history:
                f.write(json.dumps(metric.to_dict()) + "\n")

    def update_performance_data(self, performance_metric: PerformanceMetric):
        """Adds new performance data and saves history."""
        self.performance_history.append(performance_metric)
        # Keep history window limited if needed
        # self.performance_history = self.performance_history[-self.adaptive_settings["performance_window"]:]
        self._save_performance_history()
        logger.info(
            f"Logged performance for model {performance_metric.model_used} on task category {performance_metric.task_category.value}"
        )

    def optimize_sacred_trinity(self):
        """Optimizes Sacred Trinity weights based on performance history."""
        logger.info("Optimizing Sacred Trinity weights...")
        # This is a complex optimization task.
        # A simple approach: increase weight for principles that correlate with high quality/success in recent history.
        # Requires performance_history to include sacred_alignment_achieved per task.
        # For now, this method is a placeholder.
        logger.warning("Sacred Trinity optimization logic is a placeholder.")
        # Example placeholder logic (needs real data & method):
        # if self.performance_history:
        #    avg_quality_by_sacred_principle = {} # Calculate average quality when principle was strongly embodied
        #    for principle in self.sacred_trinity.keys():
        #       # Filter history where this principle scored high in sacred_alignment_achieved
        #       # Calculate average quality_score for these entries
        #       # Update self.sacred_trinity[principle].weight based on this average
        pass

    def get_task_guidance(self, task_category: TaskCategory) -> Dict[str, Any]:
        """
        Provides strategic guidance for model selection based on task category
        and current Sacred Trinity optimization state.
        """
        logger.debug(f"Getting task guidance for category: {task_category.value}")
        guidance = {
            "prioritize_principles": [],
            "quality_threshold": self.performance_thresholds["quality_threshold"],
            "cost_threshold": self.performance_thresholds["cost_effectiveness_target"],
            "min_success_rate": self.performance_thresholds["minimum_success_rate"],
        }

        # Example: Prioritize principles based on fixed mapping and current
        # trinity weights
        principle_priority_map = {
            TaskCategory.CREATIVE_WRITING: ["compassion", "wisdom"],
            TaskCategory.ETHICAL_REASONING: ["truth", "compassion", "wisdom"],
            TaskCategory.CODE_GENERATION: ["wisdom", "truth"],
            TaskCategory.ORACLE: ["wisdom", "truth", "compassion"],
            # Speed is primary, principles less critical for selection
            TaskCategory.SWIFT_RESPONDER: [],
            TaskCategory.MEMORY_WEAVER: [
                "wisdom"
            ],  # Focus on accurate recall/summarization
            TaskCategory.DEV_AGENT: ["wisdom", "truth"],  # Logic, accuracy
            TaskCategory.BUDGET_WORKHORSE: [],  # Cost is primary
            TaskCategory.MULTIMODAL_SEER: [
                "truth",
                "wisdom",
            ],  # Accurate interpretation
            # Add more mappings as needed
        }

        prioritized_principles = principle_priority_map.get(task_category, [])

        # Sort prioritized principles by their current optimized weight
        prioritized_principles.sort(
            key=lambda p: self.sacred_trinity.get(
                p, SacredPrinciple(0, 0, False)
            ).weight,
            reverse=True,
        )

        guidance["prioritize_principles"] = prioritized_principles

        # TODO: Add logic to adjust thresholds based on historical performance
        # for this category

        return guidance

    def get_model_sacred_scores(self, model_id: str) -> Dict[str, float]:
        """Retrieves the initial sacred alignment scores for a model."""
        # In a truly living system, these might also be influenced by
        # performance data
        return self.initial_sacred_alignment_scores.get(model_id, {})

    def get_model_archetype_fits(self, model_id: str) -> Dict[str, float]:
        """Retrieves the initial archetype fit scores for a model."""
        # In a truly living system, these might also be influenced by
        # performance data
        return self.initial_archetype_fits.get(model_id, {})


# Example usage (for testing the class independently)
if __name__ == "__main__":
    config_system = UltimateLivingSacredConfig()
    print(config_system.sacred_trinity)

    # Simulate adding performance data
    sample_metric = PerformanceMetric(
        model_used="gpt-4o-mini-openai",
        task_category=TaskCategory.CODE_GENERATION,
        success_rate=0.95,
        quality_score=0.90,
        cost_effectiveness=0.80,
        time_efficiency=0.88,
        human_validation=0.92,
        sacred_alignment_achieved={"wisdom": 0.9, "truth": 0.85},
    )
    config_system.update_performance_data(sample_metric)

    print(f"\nPerformance History Size: {len(config_system.performance_history)}")

    # Get task guidance
    guidance_code = config_system.get_task_guidance(TaskCategory.CODE_GENERATION)
    print(f"\nCode Generation Guidance: {guidance_code}")

    guidance_creative = config_system.get_task_guidance(TaskCategory.CREATIVE_WRITING)
    print(f"\nCreative Writing Guidance: {guidance_creative}")

    # Example of getting initial scores
    model_id = "gpt-4o-mini-openai"
    sacred_scores = config_system.get_model_sacred_scores(model_id)
    archetype_fits = config_system.get_model_archetype_fits(model_id)
    print(f"\nInitial Sacred Scores for {model_id}: {sacred_scores}")
    print(f"Initial Archetype Fits for {model_id}: {archetype_fits}")
