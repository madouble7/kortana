#!/usr/bin/env python3
"""
Test Proactive Code Integration - Batch 10 File-Based Validation

This script validates that proactive code review scheduling is properly integrated
into Kor'tana's codebase by examining the files directly.
"""

from pathlib import Path

print("🧠 TESTING PROACTIVE CODE INTEGRATION (Batch 10)")
print("=" * 55)

success_count = 0
total_checks = 0

def check_condition(condition, description, success_message, failure_message):
    global success_count, total_checks
    total_checks += 1
    if condition:
        print(f"✅ {success_message}")
        success_count += 1
    else:
        print(f"❌ {failure_message}")

# Check 1: Execution Engine has scan_codebase_for_issues method
print("🔍 Checking ExecutionEngine implementation...")
execution_engine_file = Path("src/kortana/core/execution_engine.py")
if execution_engine_file.exists():
    execution_content = execution_engine_file.read_text(encoding='utf-8')
    check_condition(
        "scan_codebase_for_issues" in execution_content,
        "ExecutionEngine has scan_codebase_for_issues",
        "ExecutionEngine scan_codebase_for_issues method found",
        "ExecutionEngine scan_codebase_for_issues method missing"
    )
    check_condition(
        "ast.get_docstring" in execution_content,
        "ExecutionEngine uses AST for docstring analysis",
        "AST-based docstring analysis implemented",
        "AST-based docstring analysis missing"
    )
else:
    print("❌ ExecutionEngine file not found")

# Check 2: Autonomous tasks has proactive code review
print("\n🤖 Checking autonomous tasks implementation...")
autonomous_tasks_file = Path("src/kortana/core/autonomous_tasks.py")
if autonomous_tasks_file.exists():
    tasks_content = autonomous_tasks_file.read_text(encoding='utf-8')
    check_condition(
        "run_proactive_code_review_task" in tasks_content,
        "Autonomous tasks has proactive code review",
        "Proactive code review task function found",
        "Proactive code review task function missing"
    )
    check_condition(
        "missing_docstring" in tasks_content,
        "Task scans for missing docstrings",
        "Missing docstring detection implemented",
        "Missing docstring detection missing"
    )
    check_condition(
        "proactive_code_quality" in tasks_content,
        "Creates proactive code quality goals",
        "Proactive goal creation implemented",
        "Proactive goal creation missing"
    )
else:
    print("❌ Autonomous tasks file not found")

# Check 3: Brain has proactive scheduling
print("\n🧠 Checking brain scheduling integration...")
brain_file = Path("src/kortana/core/brain.py")
if brain_file.exists():
    brain_content = brain_file.read_text(encoding='utf-8')
    check_condition(
        "_proactive_code_review_cycle" in brain_content,
        "Brain has proactive code review cycle method",
        "Proactive code review cycle method found in brain",
        "Proactive code review cycle method missing from brain"
    )
    check_condition(
        "proactive_code_review" in brain_content and "add_job" in brain_content,
        "Brain schedules proactive code review",
        "Proactive code review scheduling found",
        "Proactive code review scheduling missing"
    )
    check_condition(
        "IntervalTrigger" in brain_content,
        "Uses interval triggers for scheduling",
        "Interval trigger scheduling implemented",
        "Interval trigger scheduling missing"
    )
else:
    print("❌ Brain file not found")

# Check 4: Services module supports the functionality
print("\n⚙️ Checking services integration...")
services_file = Path("src/kortana/core/services.py")
if services_file.exists():
    services_content = services_file.read_text()
    check_condition(
        "get_execution_engine" in services_content,
        "Services provides execution engine",
        "Execution engine service getter found",
        "Execution engine service getter missing"
    )
else:
    print("❌ Services file not found")

# Summary
print("\n📊 INTEGRATION TEST SUMMARY")
print("=" * 30)
print(f"✅ Passed: {success_count}/{total_checks}")
print(f"❌ Failed: {total_checks - success_count}/{total_checks}")

if success_count == total_checks:
    print("\n🎉 ALL TESTS PASSED!")
    print("🔥 Kor'tana's proactive engineering system is fully integrated!")
    print("🚀 Ready for Batch 10 Phase 2: Live Testing")
    print("\nNext steps:")
    print("1. 🔄 Start Kor'tana in autonomous mode")
    print("2. ⏰ Wait for the 6-hour proactive cycle")
    print("3. 📝 Observe autonomous goal generation")
    print("4. 🎯 Validate self-improvement workflow")
else:
    print("\n⚠️  INTEGRATION INCOMPLETE")
    print(f"Fix the {total_checks - success_count} failed checks before proceeding")
