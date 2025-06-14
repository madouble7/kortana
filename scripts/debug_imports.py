#!/usr/bin/env python3
"""
Debug import issues for the learning loop
"""

import sys
import traceback
from pathlib import Path

print("=== Import Debug Script ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {Path.cwd()}")
print("Python path:")
for p in sys.path:
    print(f"  {p}")

print("\n=== Testing Core Imports ===")

try:
    print("Testing: from src.kortana.core.models import Goal, GoalStatus, PlanStep")
    from src.kortana.core.models import Goal, GoalStatus, PlanStep

    print("✅ Core models imported successfully")
    print(f"Goal: {Goal}")
    print(f"GoalStatus: {GoalStatus}")
    print(f"PlanStep: {PlanStep}")
except Exception as e:
    print(f"❌ Core models import failed: {e}")
    traceback.print_exc()

try:
    print(
        "\nTesting: from src.kortana.core.autonomous_tasks import run_performance_analysis_task"
    )
    from src.kortana.core.autonomous_tasks import run_performance_analysis_task

    print("✅ Autonomous tasks imported successfully")
    print(f"Function: {run_performance_analysis_task}")
except Exception as e:
    print(f"❌ Autonomous tasks import failed: {e}")
    traceback.print_exc()

try:
    print("\nTesting: from src.kortana.services.database import get_db_sync")
    from src.kortana.services.database import get_db_sync

    print("✅ Database service imported successfully")
    print(f"Function: {get_db_sync}")
except Exception as e:
    print(f"❌ Database service import failed: {e}")
    traceback.print_exc()

print("\n=== Import Debug Complete ===")
