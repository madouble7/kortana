"""
Kor'tana's Goal Manager
Handles goal lifecycle management, prioritization, and Sacred Covenant integration.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from .goal_framework import Goal, GoalStatus, GoalType

logger = logging.getLogger(__name__)


class GoalManager:
    """
    Central controller for Kor'tana's autonomous goal management.
    
    This class transforms Kor'tana from reactive assistance to proactive autonomy
    by enabling her to create, prioritize, and pursue her own objectives.
    """

    def __init__(self, memory_manager=None, covenant_enforcer=None):
        self.memory_manager = memory_manager
        self.covenant_enforcer = covenant_enforcer
        self.logger = logging.getLogger(__name__)

        # In-memory goal cache for performance
        self._goal_cache: dict[str, Goal] = {}
        self._last_cache_update = datetime.now(UTC)

        # Goal creation patterns for autonomous behavior
        self._goal_templates = {
            GoalType.MAINTENANCE: {
                "code_health": {
                    "title": "Maintain Code Health",
                    "description": "Run automated code quality checks and address issues",
                    "success_criteria": ["All linting checks pass", "No critical issues detected"],
                    "required_capabilities": ["execute_shell_command", "analyze_code"],
                    "estimated_effort": "low",
                    "priority": 7
                },
                "memory_optimization": {
                    "title": "Optimize Memory Usage",
                    "description": "Monitor and optimize memory consumption patterns",
                    "success_criteria": ["Memory usage under threshold", "No memory leaks detected"],
                    "required_capabilities": ["monitor_system", "analyze_memory"],
                    "estimated_effort": "medium",
                    "priority": 6
                }
            },
            GoalType.LEARNING: {
                "conversation_analysis": {
                    "title": "Analyze Conversation Patterns",
                    "description": "Study past interactions to improve response quality",
                    "success_criteria": ["Pattern analysis complete", "Improvement recommendations generated"],
                    "required_capabilities": ["analyze_text", "extract_insights"],
                    "estimated_effort": "medium",
                    "priority": 5
                },
                "capability_research": {
                    "title": "Research New Capabilities",
                    "description": "Explore new AI techniques and integration opportunities",
                    "success_criteria": ["Research documentation complete", "Implementation plan created"],
                    "required_capabilities": ["web_search", "analyze_research"],
                    "estimated_effort": "high",
                    "priority": 4
                }
            },
            GoalType.IMPROVEMENT: {
                "response_optimization": {
                    "title": "Optimize Response Performance",
                    "description": "Improve response time and quality metrics",
                    "success_criteria": ["Response time improved by 10%", "Quality metrics increased"],
                    "required_capabilities": ["benchmark_performance", "optimize_code"],
                    "estimated_effort": "medium",
                    "priority": 6
                },
                "feature_enhancement": {
                    "title": "Enhance Core Features",
                    "description": "Add new capabilities to improve user experience",
                    "success_criteria": ["New feature implemented", "User feedback positive"],
                    "required_capabilities": ["design_features", "implement_code"],
                    "estimated_effort": "high",
                    "priority": 5
                }
            },
            GoalType.USER_SERVICE: {
                "proactive_assistance": {
                    "title": "Provide Proactive Assistance",
                    "description": "Anticipate user needs and offer timely help",
                    "success_criteria": ["User needs anticipated", "Assistance provided proactively"],
                    "required_capabilities": ["predict_needs", "generate_assistance"],
                    "estimated_effort": "medium",
                    "priority": 8
                }
            }
        }

    def create_goal(self,
                   goal_type: GoalType,
                   title: str = "",
                   description: str = "",
                   priority: int = 5,
                   success_criteria: list[str] = None,
                   required_capabilities: list[str] = None,
                   estimated_effort: str = "medium",
                   target_completion: datetime | None = None,
                   tags: list[str] = None,
                   context: dict[str, Any] = None) -> Goal:
        """
        Create a new autonomous goal.
        
        This is where Kor'tana's proactive behavior begins - the ability to set
        her own objectives rather than waiting for human commands.
        """

        goal = Goal(
            type=goal_type,
            title=title,
            description=description,
            priority=priority,
            success_criteria=success_criteria or [],
            required_capabilities=required_capabilities or [],
            estimated_effort=estimated_effort,
            target_completion=target_completion,
            tags=tags or [],
            context=context or {}
        )

        self.logger.info(f"🎯 Created new autonomous goal: {goal.title} ({goal.goal_id})")

        # Store in cache
        self._goal_cache[goal.goal_id] = goal

        # Persist to memory system
        self._save_goal_to_memory(goal)

        return goal

    def create_goal_from_template(self, goal_type: GoalType, template_name: str, **overrides) -> Goal | None:
        """Create goal from predefined template with optional overrides"""

        if goal_type not in self._goal_templates or template_name not in self._goal_templates[goal_type]:
            self.logger.error(f"Template not found: {goal_type.value}.{template_name}")
            return None

        template = self._goal_templates[goal_type][template_name].copy()
        template.update(overrides)

        return self.create_goal(goal_type=goal_type, **template)

    def get_goal(self, goal_id: str) -> Goal | None:
        """Retrieve goal by ID"""

        # Check cache first
        if goal_id in self._goal_cache:
            return self._goal_cache[goal_id]

        # Load from memory if not in cache
        goal = self._load_goal_from_memory(goal_id)
        if goal:
            self._goal_cache[goal_id] = goal

        return goal

    def get_goals_by_status(self, status: GoalStatus) -> list[Goal]:
        """Get all goals with specified status"""

        self._refresh_cache_if_needed()
        return [goal for goal in self._goal_cache.values() if goal.status == status]

    def get_active_goals(self) -> list[Goal]:
        """Get all active goals sorted by priority"""

        active_goals = self.get_goals_by_status(GoalStatus.ACTIVE)
        return sorted(active_goals, key=lambda g: g.priority, reverse=True)

    def get_actionable_goals(self) -> list[Goal]:
        """Get goals that are ready for execution"""

        self._refresh_cache_if_needed()
        actionable = [goal for goal in self._goal_cache.values() if goal.is_actionable()]
        return sorted(actionable, key=lambda g: g.priority, reverse=True)

    def prioritize_goals(self) -> list[Goal]:
        """
        Dynamically prioritize goals based on multiple factors.
        
        This implements Kor'tana's strategic thinking capability.
        """

        all_goals = list(self._goal_cache.values())

        # Calculate dynamic priority scores
        for goal in all_goals:
            base_priority = goal.priority

            # Urgency factor (higher for approaching deadlines)
            urgency_bonus = 0
            if goal.target_completion:
                days_left = goal.get_time_to_deadline_days()
                if days_left is not None:
                    if days_left <= 1:
                        urgency_bonus = 3
                    elif days_left <= 3:
                        urgency_bonus = 2
                    elif days_left <= 7:
                        urgency_bonus = 1

            # Age factor (slightly prioritize older goals)
            age_bonus = min(1, goal.get_age_days() / 7)  # Max 1 point for week-old goals

            # Type-based priority adjustments
            type_bonuses = {
                GoalType.MAINTENANCE: 1,      # Always important
                GoalType.USER_SERVICE: 2,     # User-focused gets priority
                GoalType.IMPROVEMENT: 0,      # Standard
                GoalType.LEARNING: -1,        # Can wait
                GoalType.EXPLORATION: -2      # Lowest priority
            }
            type_bonus = type_bonuses.get(goal.type, 0)

            # Calculate final dynamic priority
            dynamic_priority = base_priority + urgency_bonus + age_bonus + type_bonus
            goal.context["dynamic_priority"] = dynamic_priority

        # Sort by dynamic priority
        return sorted(all_goals, key=lambda g: g.context.get("dynamic_priority", g.priority), reverse=True)

    def activate_goal(self, goal_id: str) -> bool:
        """Activate a goal for pursuit"""

        goal = self.get_goal(goal_id)
        if not goal:
            self.logger.error(f"Goal not found: {goal_id}")
            return False

        # Check covenant approval
        if not self._check_covenant_approval(goal):
            self.logger.warning(f"Goal blocked by Sacred Covenant: {goal.title}")
            return False

        if goal.activate():
            self.logger.info(f"✅ Activated goal: {goal.title}")
            self._save_goal_to_memory(goal)
            return True

        self.logger.warning(f"Cannot activate goal: {goal.title} (status: {goal.status})")
        return False

    def update_goal_progress(self, goal_id: str, percentage: float,
                           metrics: dict[str, Any] = None,
                           insights: list[str] = None) -> bool:
        """Update goal progress and learning"""

        goal = self.get_goal(goal_id)
        if not goal:
            return False

        goal.update_progress(percentage, metrics, insights)
        self._save_goal_to_memory(goal)

        self.logger.info(f"📊 Updated progress for {goal.title}: {percentage}%")

        return True

    def complete_goal(self, goal_id: str, lessons: dict[str, str] = None) -> bool:
        """Mark goal as completed with optional lessons learned"""

        goal = self.get_goal(goal_id)
        if not goal:
            return False

        goal.complete(lessons)
        self._save_goal_to_memory(goal)

        self.logger.info(f"🎉 Completed goal: {goal.title}")

        # Analyze completion for learning
        self._extract_completion_insights(goal)

        return True

    def suggest_new_goals(self, context: dict[str, Any] = None) -> list[Goal]:
        """
        Autonomously suggest new goals based on current state and patterns.
        
        This is a key autonomous behavior - proactive goal generation.
        """

        suggestions = []

        # Analyze current goal distribution
        active_by_type = {}
        for goal in self.get_active_goals():
            active_by_type[goal.type] = active_by_type.get(goal.type, 0) + 1

        # Suggest maintenance goals if none active
        if active_by_type.get(GoalType.MAINTENANCE, 0) == 0:
            suggestions.append(
                self.create_goal_from_template(GoalType.MAINTENANCE, "code_health")
            )

        # Suggest learning goals periodically
        if active_by_type.get(GoalType.LEARNING, 0) == 0:
            suggestions.append(
                self.create_goal_from_template(GoalType.LEARNING, "conversation_analysis")
            )

        # Context-based suggestions
        if context:
            if context.get("performance_issues"):
                suggestions.append(
                    self.create_goal_from_template(GoalType.IMPROVEMENT, "response_optimization")
                )

            if context.get("user_requests"):
                suggestions.append(
                    self.create_goal_from_template(GoalType.USER_SERVICE, "proactive_assistance")
                )

        self.logger.info(f"🤔 Suggested {len(suggestions)} new autonomous goals")

        return suggestions

    def _check_covenant_approval(self, goal: Goal) -> bool:
        """Check goal against Sacred Covenant principles"""

        if not self.covenant_enforcer:
            # Default approve if no enforcer available
            goal.covenant_approved = True
            return True

        # Check if goal aligns with Sacred Covenant
        goal_summary = f"Goal: {goal.title}\nDescription: {goal.description}\nType: {goal.type.value}"

        try:
            # Use covenant enforcer's verification method
            if hasattr(self.covenant_enforcer, 'verify_action'):
                approved = self.covenant_enforcer.verify_action(
                    {"goal": goal.to_dict()},
                    goal_summary
                )
            else:
                # Fallback approval
                approved = True

            goal.covenant_approved = approved

            if approved:
                goal.covenant_review_notes = "Approved by Sacred Covenant"
                self.logger.info(f"✅ Covenant approved goal: {goal.title}")
            else:
                goal.covenant_review_notes = "Blocked by Sacred Covenant"
                self.logger.warning(f"❌ Covenant blocked goal: {goal.title}")

            return approved

        except Exception as e:
            self.logger.error(f"Error checking covenant approval: {e}")
            # Default to not approved on error
            goal.covenant_approved = False
            goal.covenant_review_notes = f"Covenant check failed: {str(e)}"
            return False

    def _save_goal_to_memory(self, goal: Goal):
        """Save goal to persistent memory system"""

        if not self.memory_manager:
            self.logger.warning("No memory manager available for goal persistence")
            return

        try:
            memory_entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "role": "goal",
                "goal_id": goal.goal_id,
                "status": goal.status.value,
                "content": goal.to_dict(),
                "metadata": {
                    "created_by": "goal_manager",
                    "covenant_approved": goal.covenant_approved
                }
            }

            # Store in memory system
            if hasattr(self.memory_manager, 'store_memory'):
                self.memory_manager.store_memory(
                    memory_type="goal",
                    content=f"Goal: {goal.title}",
                    goal_data=goal.to_dict()
                )

        except Exception as e:
            self.logger.error(f"Failed to save goal to memory: {e}")

    def _load_goal_from_memory(self, goal_id: str) -> Goal | None:
        """Load goal from persistent memory system"""

        if not self.memory_manager:
            return None

        try:
            # Search memory for goal
            # This is a placeholder - actual implementation depends on memory system
            # For now, return None (goals will be created fresh)
            return None

        except Exception as e:
            self.logger.error(f"Failed to load goal from memory: {e}")
            return None

    def _refresh_cache_if_needed(self):
        """Refresh goal cache if it's stale"""

        now = datetime.now(UTC)
        if (now - self._last_cache_update).total_seconds() > 300:  # 5 minutes
            # In a full implementation, this would reload from persistent storage
            self._last_cache_update = now

    def _extract_completion_insights(self, goal: Goal):
        """Extract insights from completed goal for future learning"""

        insights = []

        # Analyze completion time vs estimate
        if goal.started_at and goal.completed_at:
            actual_duration = (goal.completed_at - goal.started_at).total_seconds() / 3600  # hours
            effort_mapping = {"low": 2, "medium": 8, "high": 24}  # estimated hours
            estimated_duration = effort_mapping.get(goal.estimated_effort, 8)

            if actual_duration > estimated_duration * 1.5:
                insights.append(f"Goal took longer than expected ({actual_duration:.1f}h vs {estimated_duration}h estimated)")
            elif actual_duration < estimated_duration * 0.5:
                insights.append(f"Goal completed faster than expected ({actual_duration:.1f}h vs {estimated_duration}h estimated)")

        # Add insights to goal
        if insights:
            goal.learning_insights.extend(insights)
            self.logger.info(f"📚 Extracted {len(insights)} insights from completed goal: {goal.title}")

    def get_statistics(self) -> dict[str, Any]:
        """Get goal management statistics for monitoring"""

        self._refresh_cache_if_needed()
        goals = list(self._goal_cache.values())

        stats = {
            "total_goals": len(goals),
            "by_status": {},
            "by_type": {},
            "completion_rate": 0.0,
            "average_priority": 0.0,
            "overdue_count": 0
        }

        if not goals:
            return stats

        # Count by status
        for status in GoalStatus:
            stats["by_status"][status.value] = len([g for g in goals if g.status == status])

        # Count by type
        for goal_type in GoalType:
            stats["by_type"][goal_type.value] = len([g for g in goals if g.type == goal_type])

        # Calculate completion rate
        completed = stats["by_status"].get("completed", 0)
        total_finished = completed + stats["by_status"].get("cancelled", 0)
        if total_finished > 0:
            stats["completion_rate"] = completed / total_finished

        # Average priority
        stats["average_priority"] = sum(g.priority for g in goals) / len(goals)

        # Overdue count
        stats["overdue_count"] = len([g for g in goals if g.is_overdue()])

        return stats
