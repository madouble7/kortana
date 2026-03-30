"""
CapabilityBudget — action-class governance for the autonomy daemon.

Gates each category of mutation based on the current autonomy_index,
system state, control_mode, and operator settings so the daemon only
acts when it has the confidence and permission to do so.
"""

from __future__ import annotations

from enum import Enum

from src.kortana.logger import get_logger

logger = get_logger(__name__)


class ActionClass(str, Enum):
    """Ordered tiers of autonomy, from observation to actuation."""

    OBSERVE = "observe"
    PLAN = "plan"
    PATCH = "patch"
    COMMIT = "commit"
    PUSH = "push"
    PROPOSE_PR = "propose_pr"


# Minimum autonomy_index required to unlock each action class.
_MIN_INDEX: dict[ActionClass, int] = {
    ActionClass.OBSERVE: 0,
    ActionClass.PLAN: 20,
    ActionClass.PATCH: 50,
    ActionClass.COMMIT: 60,
    ActionClass.PUSH: 70,
    ActionClass.PROPOSE_PR: 70,
}

# Control modes that block execution above PLAN.
_OBSERVE_ONLY_MODES = {
    "observe_only",
    "paused_by_operator",
    "operator_override_halt",
    "safe_mode",
}

# Control modes that allow PLAN but block PATCH and above.
_PLAN_ONLY_MODES = {
    "plan_only",
    "approval_required",
}

# System states that restrict execution above PLAN regardless of index.
_RESTRICTED_STATES = {"critical"}

# System states that restrict PUSH / PROPOSE_PR.
_DEGRADED_STATES = {"degraded", "recovering"}


class CapabilityBudget:
    """Evaluates whether a proposed action class is currently permitted."""

    def is_permitted(
        self,
        action: ActionClass,
        *,
        autonomy_index: int,
        system_state: str,
        control_mode: str,
        live_execution_enabled: bool,
    ) -> bool:
        """
        Return True if *action* is safe to attempt given the current runtime context.

        Parameters
        ----------
        action:
            The action class being proposed.
        autonomy_index:
            Current self-assessed autonomy score (0-100).
        system_state:
            Current health label, e.g. "nominal", "degraded", "critical".
        control_mode:
            Current daemon control mode string.
        live_execution_enabled:
            Whether the daemon's live execution flag is set.
        """
        # Threshold gate — hard floor on autonomy index
        if autonomy_index < _MIN_INDEX[action]:
            logger.debug(
                "CapabilityBudget DENY %s: autonomy_index=%d < min=%d",
                action,
                autonomy_index,
                _MIN_INDEX[action],
            )
            return False

        # Observe-only modes block everything above OBSERVE
        if control_mode in _OBSERVE_ONLY_MODES and action not in (ActionClass.OBSERVE,):
            logger.debug(
                "CapabilityBudget DENY %s: control_mode=%s", action, control_mode
            )
            return False

        # Plan-only modes block PATCH and above
        if control_mode in _PLAN_ONLY_MODES and action not in (
            ActionClass.OBSERVE,
            ActionClass.PLAN,
        ):
            logger.debug(
                "CapabilityBudget DENY %s: plan-only control_mode=%s",
                action,
                control_mode,
            )
            return False

        # Critical system state blocks PATCH and above
        if system_state in _RESTRICTED_STATES and action not in (
            ActionClass.OBSERVE,
            ActionClass.PLAN,
        ):
            logger.debug("CapabilityBudget DENY %s: critical system_state", action)
            return False

        # Degraded state blocks PUSH / PROPOSE_PR
        if system_state in _DEGRADED_STATES and action in (
            ActionClass.PUSH,
            ActionClass.PROPOSE_PR,
        ):
            logger.debug("CapabilityBudget DENY %s: degraded system_state", action)
            return False

        # Live execution required for PUSH and PROPOSE_PR
        if (
            action in (ActionClass.PUSH, ActionClass.PROPOSE_PR)
            and not live_execution_enabled
        ):
            logger.debug(
                "CapabilityBudget DENY %s: live_execution_enabled=False", action
            )
            return False

        return True


_budget = CapabilityBudget()


def get_capability_budget() -> CapabilityBudget:
    return _budget
