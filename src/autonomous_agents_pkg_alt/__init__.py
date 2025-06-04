"""Alternative autonomous agents package for Kortana.

This package contains alternative implementations of autonomous agents
for monitoring, planning, testing, and coding tasks.
"""
# src/autonomous_agents/__init__.py
# This file marks this directory as a Python package.

from .coding_agent import CodingAgent
from .monitoring_agent import MonitoringAgent
from .planning_agent import PlanningAgent
from .testing_agent import TestingAgent

# Optionally, add to __all__ for explicit exports
__all__ = [
    "MonitoringAgent",
    "PlanningAgent",
    "TestingAgent",
    "CodingAgent",
]
