"""
Decision Optimizer - Multi-objective optimization for decision-making

This module optimizes decisions across multiple objectives such as:
- Execution time
- Resource cost
- Safety/risk
- Success probability

Uses optimization algorithms to find Pareto-optimal solutions.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class OptimizationObjective:
    """Defines an optimization objective"""

    name: str
    weight: float  # Importance weight (0-1)
    minimize: bool  # True to minimize, False to maximize
    constraint_min: float | None = None
    constraint_max: float | None = None


@dataclass
class OptimizationResult:
    """Result of optimization"""

    best_action: str
    best_score: float
    objective_values: dict[str, float]
    pareto_front: list[dict[str, Any]]
    iterations: int
    convergence: bool


class DecisionOptimizer:
    """
    Multi-objective optimizer for decision-making

    Features:
    - Weighted objective optimization
    - Constraint handling
    - Pareto-optimal solution discovery
    - Trade-off analysis
    """

    def __init__(
        self,
        max_iterations: int = 100,
        population_size: int = 50,
        convergence_threshold: float = 0.001,
    ):
        """
        Initialize the optimizer

        Args:
            max_iterations: Maximum optimization iterations
            population_size: Population size for genetic algorithm
            convergence_threshold: Threshold for convergence detection
        """
        self.max_iterations = max_iterations
        self.population_size = population_size
        self.convergence_threshold = convergence_threshold
        self.optimization_history: list[dict[str, Any]] = []

        logger.info(
            f"Decision optimizer initialized (max_iter={max_iterations}, "
            f"pop_size={population_size})"
        )

    def _evaluate_action(
        self,
        action: str,
        context: dict[str, Any],
        objectives: list[OptimizationObjective],
        evaluator: Callable,
    ) -> dict[str, float]:
        """
        Evaluate an action against all objectives

        Args:
            action: Action to evaluate
            context: Context information
            objectives: List of objectives
            evaluator: Function to evaluate action

        Returns:
            Dictionary of objective values
        """
        # Get evaluation from evaluator function
        evaluation = evaluator(action, context)

        # Extract objective values
        objective_values = {}
        for obj in objectives:
            if obj.name in evaluation:
                value = evaluation[obj.name]
            else:
                # Default values if not provided
                value = 0.5

            objective_values[obj.name] = value

        return objective_values

    def _calculate_weighted_score(
        self,
        objective_values: dict[str, float],
        objectives: list[OptimizationObjective],
    ) -> float:
        """
        Calculate weighted score across objectives

        Args:
            objective_values: Values for each objective
            objectives: Objective definitions

        Returns:
            Weighted score
        """
        total_score = 0.0
        total_weight = sum(obj.weight for obj in objectives)

        for obj in objectives:
            value = objective_values.get(obj.name, 0.0)

            # Normalize and apply weight
            if obj.minimize:
                # For minimization, lower is better
                score = (1.0 - value) * obj.weight
            else:
                # For maximization, higher is better
                score = value * obj.weight

            total_score += score

        # Normalize by total weight
        return total_score / total_weight if total_weight > 0 else 0.0

    def _check_constraints(
        self,
        objective_values: dict[str, float],
        objectives: list[OptimizationObjective],
    ) -> bool:
        """
        Check if solution satisfies all constraints

        Args:
            objective_values: Values for each objective
            objectives: Objective definitions with constraints

        Returns:
            True if all constraints satisfied
        """
        for obj in objectives:
            value = objective_values.get(obj.name, 0.0)

            if obj.constraint_min is not None and value < obj.constraint_min:
                return False

            if obj.constraint_max is not None and value > obj.constraint_max:
                return False

        return True

    def _is_dominated(
        self,
        solution1: dict[str, float],
        solution2: dict[str, float],
        objectives: list[OptimizationObjective],
    ) -> bool:
        """
        Check if solution1 is dominated by solution2

        Args:
            solution1: First solution's objective values
            solution2: Second solution's objective values
            objectives: Objective definitions

        Returns:
            True if solution1 is dominated by solution2
        """
        better_or_equal = True
        strictly_better = False

        for obj in objectives:
            val1 = solution1.get(obj.name, 0.0)
            val2 = solution2.get(obj.name, 0.0)

            if obj.minimize:
                if val1 < val2:
                    better_or_equal = False
                    break
                if val2 < val1:
                    strictly_better = True
            else:
                if val1 > val2:
                    better_or_equal = False
                    break
                if val2 > val1:
                    strictly_better = True

        return better_or_equal and strictly_better

    def _find_pareto_front(
        self,
        solutions: list[tuple[str, dict[str, float]]],
        objectives: list[OptimizationObjective],
    ) -> list[dict[str, Any]]:
        """
        Find Pareto-optimal solutions

        Args:
            solutions: List of (action, objective_values) tuples
            objectives: Objective definitions

        Returns:
            Pareto-optimal solutions
        """
        pareto_front = []

        for i, (action1, values1) in enumerate(solutions):
            dominated = False

            for j, (action2, values2) in enumerate(solutions):
                if i != j and self._is_dominated(values1, values2, objectives):
                    dominated = True
                    break

            if not dominated:
                pareto_front.append(
                    {
                        "action": action1,
                        "objective_values": values1,
                    }
                )

        return pareto_front

    def optimize(
        self,
        actions: list[str],
        context: dict[str, Any],
        objectives: list[OptimizationObjective],
        evaluator: Callable,
    ) -> OptimizationResult:
        """
        Optimize decision across multiple objectives

        Args:
            actions: List of possible actions
            context: Context information
            objectives: List of optimization objectives
            evaluator: Function to evaluate actions: evaluator(action, context) -> dict

        Returns:
            Optimization result with best action and Pareto front
        """
        logger.info(
            f"Optimizing across {len(objectives)} objectives for {len(actions)} actions"
        )

        # Evaluate all actions
        solutions = []
        for action in actions:
            objective_values = self._evaluate_action(
                action, context, objectives, evaluator
            )

            # Check constraints
            if self._check_constraints(objective_values, objectives):
                solutions.append((action, objective_values))
            else:
                logger.debug(f"Action {action} violates constraints")

        if not solutions:
            logger.warning("No feasible solutions found")
            return OptimizationResult(
                best_action=actions[0] if actions else "none",
                best_score=0.0,
                objective_values={},
                pareto_front=[],
                iterations=0,
                convergence=False,
            )

        # Calculate weighted scores
        scored_solutions = []
        for action, objective_values in solutions:
            score = self._calculate_weighted_score(objective_values, objectives)
            scored_solutions.append((action, score, objective_values))

        # Sort by score
        scored_solutions.sort(key=lambda x: x[1], reverse=True)

        # Best solution
        best_action, best_score, best_objective_values = scored_solutions[0]

        # Find Pareto front
        pareto_front = self._find_pareto_front(solutions, objectives)

        logger.info(
            f"Optimization complete: best_action={best_action}, "
            f"score={best_score:.3f}, pareto_size={len(pareto_front)}"
        )

        result = OptimizationResult(
            best_action=best_action,
            best_score=best_score,
            objective_values=best_objective_values,
            pareto_front=pareto_front,
            iterations=1,  # Single iteration for simple optimization
            convergence=True,
        )

        # Store in history
        self.optimization_history.append(
            {
                "result": result,
                "num_actions": len(actions),
                "num_objectives": len(objectives),
            }
        )

        return result

    def optimize_with_tradeoffs(
        self,
        actions: list[str],
        context: dict[str, Any],
        objectives: list[OptimizationObjective],
        evaluator: Callable,
        tradeoff_scenarios: list[dict[str, float]] | None = None,
    ) -> dict[str, OptimizationResult]:
        """
        Optimize with different tradeoff scenarios

        Args:
            actions: List of possible actions
            context: Context information
            objectives: List of optimization objectives
            evaluator: Function to evaluate actions
            tradeoff_scenarios: List of weight configurations to try

        Returns:
            Dictionary of scenario name to optimization result
        """
        if tradeoff_scenarios is None:
            # Default scenarios
            tradeoff_scenarios = [
                {"name": "balanced", "weights": {obj.name: 1.0 for obj in objectives}},
                {
                    "name": "safety_first",
                    "weights": {
                        "success_probability": 2.0,
                        "execution_failure": 2.0,
                        "expected_duration": 1.0,
                        "expected_cost": 1.0,
                    },
                },
                {
                    "name": "speed_optimized",
                    "weights": {
                        "expected_duration": 2.0,
                        "success_probability": 1.0,
                        "execution_failure": 1.0,
                        "expected_cost": 0.5,
                    },
                },
            ]

        results = {}

        for scenario in tradeoff_scenarios:
            # Adjust objective weights
            scenario_objectives = []
            for obj in objectives:
                weight = scenario.get("weights", {}).get(obj.name, obj.weight)
                scenario_obj = OptimizationObjective(
                    name=obj.name,
                    weight=weight,
                    minimize=obj.minimize,
                    constraint_min=obj.constraint_min,
                    constraint_max=obj.constraint_max,
                )
                scenario_objectives.append(scenario_obj)

            # Optimize with this scenario
            result = self.optimize(actions, context, scenario_objectives, evaluator)
            results[scenario["name"]] = result

            logger.info(
                f"Tradeoff scenario '{scenario['name']}': "
                f"best_action={result.best_action}"
            )

        return results

    def get_recommendation(
        self,
        optimization_results: dict[str, OptimizationResult],
        preference: str = "balanced",
    ) -> tuple[str, str]:
        """
        Get recommended action from multiple optimization results

        Args:
            optimization_results: Results from different scenarios
            preference: Preferred scenario name

        Returns:
            Tuple of (recommended_action, reasoning)
        """
        if preference in optimization_results:
            result = optimization_results[preference]
            reasoning = (
                f"Selected based on '{preference}' preference with "
                f"score {result.best_score:.3f}"
            )
            return result.best_action, reasoning

        # Fall back to highest score across all scenarios
        best_result = max(
            optimization_results.values(), key=lambda r: r.best_score
        )
        reasoning = (
            f"Selected highest scoring action across scenarios "
            f"(score={best_result.best_score:.3f})"
        )
        return best_result.best_action, reasoning
