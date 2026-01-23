#!/usr/bin/env python3
"""
Janitor Agent: Directory Audit & Cleanup

This script scans the project directory for scripts, logs, and obsolete files.
Moves scripts to 'scripts/', archives logs and old files, and updates the README.
"""

import shutil
from pathlib import Path

# Define paths
project_root = Path("c:/project-kortana")
scripts_dir = project_root / "scripts"
archive_dir = project_root / "archive"
data_dir = project_root / "data"
readme_path = project_root / "README.md"

# Create directories if not exist
scripts_dir.mkdir(exist_ok=True)
archive_dir.mkdir(exist_ok=True)
data_dir.mkdir(exist_ok=True)

# List of script patterns and specific files to move to scripts/
# This list should be as exhaustive as possible for files that are executable scripts
script_targets = [
    "test_*.py",
    "check_*.py",
    "run_*.py",
    "*.bat",
    "*.ps1",
    "activate_autonomous_engineer.py",
    "activate_autonomous_kortana.py",
    "activate_autonomous_menu.py",
    "activate_genesis_protocol.py",
    "activate_goal_processing.py",
    "activate_kortana.py",
    "agent_personality_manager.py",
    "analyze_ruff.py",
    "api_learning_check.py",
    "arch_test_script.py",
    "arch_test_script_simple.py",
    "ascii_import_test.py",
    "assign_first_goal.py",
    "assign_genesis_goal.py",
    "assign_genesis_spark.py",
    "assign_genesis_spark_direct.py",
    "automation_control.py",
    "automation_guide.py",
    "autonomous_awakening_demo.py",
    "autonomous_goal_processor.py",
    "autonomous_intelligence_monitor.py",
    "autonomous_learning_engine.py",
    "autonomous_monitor.py",
    "autonomous_validation_silent.py",
    "batch10_final_validation.py",
    "batch10_validation.py",
    "batch8_final_verification.py",
    "batch8_learning_test.py",
    "batch8_verification.py",
    "BATCH9_COMPLETION_REPORT.py", # This seems like a script that generates a report
    "code_review_analysis.py",
    "collect_tests.py",
    "complete_autonomous_verification.py",
    "complete_system_validation.py",
    "comprehensive_api_test.py",
    "comprehensive_fix.py",
    "comprehensive_import_test.py",
    "comprehensive_system_fix.py",
    "covenant_methods.py",
    "covenant_test.py",
    "covenant_test_direct.py",
    "create_db_tables.py",
    "create_genesis_clean.py",
    "create_genesis_correct.py",
    "create_genesis_goal.py",
    "create_genesis_goal_final.py",
    "create_goal_tables.py",
    "create_monitoring_dashboard.py",
    "create_test_goal.py",
    "db_check_file_output.py",
    "debug_config_loading.py",
    "debug_imports.py",
    "debug_phase5.py",
    "debug_system.py",
    "demonstrate_autonomous_engineering.py",
    "demonstrate_proactive_capabilities.py",
    "demo_autonomous.py",
    "diagnose_activation.py",
    "diagnose_pinecone.py",
    "diagnostic_import_test.py",
    "direct_autonomous_test.py",
    "direct_boot.py",
    "direct_router_test.py",
    "direct_run.py",
    "dual_validation.py",
    "enhanced_code_scanner.py",
    "enhanced_execution_engine.py",
    "enhanced_relay.py",
    "environmental_scanner.py",
    "environment_check.py",
    "environment_summary.cmd",
    "execute_awakening_sequence.py",
    "file_system_monitor.py",
    "final_validation.py",
    "FIRST_AUTONOMOUS_ASSIGNMENT.py",
    "Fix-And-Run.ps1",
    "fix_execution_engine.py",
    "fix_imports.py",
    "fix_indentation.py",
    "fix_vscode_interpreter.bat",
    "genesis_demo.py",
    "genesis_development_goal.py",
    "genesis_protocol_ascii.py",
    "genesis_protocol_direct.py",
    "genesis_protocol_final.py",
    "genesis_protocol_fixed.py",
    "genesis_protocol_simple.py",
    "genesis_protocol_test.py",
    "genesis_protocol_validation.py",
    "genesis_readiness_final.py",
    "genesis_status_check.py",
    "genesis_test.py.backup_1749846254",
    "genesis_verification.py",
    "hands_off_runner.py",
    "health_check.py",
    "health_check_simple.py",
    "import_status_report.py",
    "import_test.py",
    "import_test_script.py",
    "initialize_database.py",
    "initiate_genesis_spark.py",
    "initiate_proving_ground.py",
    "init_db.py",
    "init_db_clean.py",
    "inspect_db.py",
    "inspect_learning_state.py",
    "Install-Fixed-Brain.ps1",
    "integrate_arch_torch.py",
    "investigate_db.py",
    "isolated_test_evaluator.py",
    "janitor_analyze_project.py",
    "kortana_awakening.py",
    "kortana_direct_activation.py",
    "launch_autonomous.bat",
    "launch_autonomous_kortana.py",
    "launch_autonomous_monitoring.py",
    "launch_complete_proving_ground.py",
    "launch_genesis_protocol.bat",
    "launch_kortana.bat",
    "launch_kortana.py",
    "launch_phase5.py",
    "launch_phase5_enhanced.py",
    "launch_proving_ground.py",
    "launch_proving_ground_complete.py",
    "launch_proving_ground_fixed.py",
    "launch_secure_server.py",
    "launch_server.py",
    "learning_test_file_output.py", # This seems like output, but was in script list
    "list_test_candidates.py", # This seems like output, but was in script list
    "main.py", # Main entry point script
    "manual_proactive_test.py",
    "manual_scan_test.py",
    "memory_verification.py",
    "minimal_test.py",
    "model_config_manager.py",
    "monitoring_dashboard.py",
    "monitoring_dashboard_enhanced.py",
    "monitor_autonomous_activity.py",
    "monitor_autonomous_activity_new.py",
    "monitor_autonomous_development.py",
    "monitor_autonomous_intelligence.py",
    "monitor_first_assignment.py",
    "monitor_genesis_protocol.py",
    "monitor_proving_ground.py",
    "observe_proactive_engineer.py",
    "open_vscode_root.cmd",
    "phase4_db_check.py",
    "phase4_db_check_clean.py",
    "phase4_observation.py",
    "phase4_observer.py",
    "phase4_status_check.py",
    "phase5_advanced_autonomous.py",
    "phase6_validation.py",
    "prepare_diagnostics.bat",
    "proving_ground_launch.py",
    "proving_ground_monitor.py",
    "proving_ground_setup.py",
    "pydantic_warning_check.py",
    "quick_api_test.py",
    "quick_autonomy_check.py",
    "quick_db_check.py",
    "quick_proactive_test.py",
    "quick_run.bat",
    "quick_run.py",
    "quick_server_test.py",
    "quick_start_genesis.py",
    "quick_test.py",
    "real_autonomous_kortana.py",
    "restart_autonomous_fixed.py",
    "run-audit.bat",
    "Run-Complete-Kortana.ps1",
    "Run-Diagnostics.ps1",
    "Run-Kortana.ps1",
    "run_api_check.bat",
    "run_arch_test.bat",
    "run_autonomous_capture.py",
    "run_autonomous_continuous.py",
    "run_codex_task.py",
    "run_diagnostics.bat",
    "run_evaluator_tests.py",
    "run_import_test.bat",
    "run_kortana.bat",
    "run_kortana_api.bat",
    "run_kortana_api.ps1",
    "run_kortana_server.bat",
    "run_learning_loop.py",
    "run_pytest_batch.bat",
    "run_pytest_capture.py",
    "run_pytest_diagnostic.py",
    "run_pytest_diagnostic_new.py",
    "run_system_test.py",
    "run_test.bat",
    "run_tests.bat",
    "run_test_check.py",
    "run_test_collection.py",
    "run_validation.bat",
    "run_with_debug.py",
    "run_with_logs.bat",
    "scan_public_members.py",
    "Setup-Files.ps1",
    "setup.py",
    "setup_and_run.bat",
    "setup_automation.py",
    "setup_directories.py",
    "setup_phase4_db.py",
    "setup_task_scheduler.py",
    "silent_learning_check.py",
    "simple_activation_test.py",
    "simple_api_test.py",
    "simple_diagnostic.py",
    "simple_endpoint_test.py",
    "simple_import_test.py",
    "simple_kortana.py",
    "simple_learning_test.py",
    "simple_proactive_test.py",
    "simple_router_test.py",
    "simple_server.py",
    "simple_test.py",
    "simple_validation.py",
    "simulate_autonomous_processing.py",
    "standalone_activation_test.py",
    "start_autonomous_engineering.py",
    "start_autonomous_processor.bat",
    "start_autonomy.py",
    "start_backend.py",
    "start_genesis.py",
    "start_genesis_protocol.bat",
    "START_KORTANA.bat",
    "start_kortana_agent.bat",
    "start_kortana_server.bat",
    "start_server.bat",
    "start_server.py",
    "start_servers.bat",
    "start_server_direct.py",
    "status_check.py",
    "submit_genesis_goal.py",
    "submit_proving_ground_goal.py",
    "temp_core_test.py",
    "temp_path_test.py",
    "torch_protocol.py",
    "tracked_files.txt",
    "trigger_autonomous_cycle.py",
    "trigger_proactive_review.py",
    "ultra_simple.py",
    "update_import_check.py",
    "update_living_log.py",
    "validate_database.py",
    "validate_full_system.py",
    "validate_infrastructure.py",
    "validate_learning_loop.py",
    "validate_phase2_strategic_insights.py",
    "validate_scanner.py",
    "verify_autonomous.py",
    "verify_autonomous_intelligence.py",
    "verify_brain_init.py",
    "verify_imports.py",
    "verify_proving_ground_ready.py",
    "verify_test_files.py",
    "write_dashboard.py",
]

# List of obsolete file patterns and specific files to archive
obsolete_targets = [
    "*.log",
    "*.txt",
    "*.md", # Archive old markdown reports, keep README.md and KOR'TANA_BLUEPRINT.md
    "*.sql",
    "*.json",
    "*.jsonl",
    "*.csv",
    "*.backup*",
    "*.old",
    "*.tmp",
    "collection_output.txt",
    "complexity_analysis.txt",
    "config_check.txt",
    "config_debug_output.txt",
    "config_files_check.txt",
    "config_test_*.txt",
    "context_test_output.log",
    "current_dependencies.txt",
    "db_check_output.txt",
    "dependency_conflicts.txt",
    "environmental_scanner_test.log",
    "extensions.txt",
    "final_health.txt",
    "final_integration_result.txt",
    "final_validation.txt",
    "focused_result.txt",
    "genesis_goal.sql",
    "genesis_run_shell.log",
    "genesis_validation_output.txt",
    "health_results.txt",
    "import_check.txt",
    "import_check_new.txt",
    "import_check_updated.txt",
    "import_deps.txt",
    "integration_result.txt",
    "learning_test_file_output.py", # This seems like output, not a script
    "list_test_candidates.py", # This seems like output, not a script
    "load_config_import_test.txt",
    "missing_docstrings.txt",
    "multi_line_test_out.txt",
    "mypy_errors.txt",
    "mypy_errors_detailed.txt",
    "mypy_goals_current.txt",
    "mypy_goals_fixed.txt",
    "mypy_goals_fixed2.txt",
    "mypy_goals_fixed3.txt",
    "mypy_goals_new_report.txt",
    "mypy_goals_report.txt",
    "mypy_goals_updated.txt",
    "mypy_report.txt",
    "mypy_report_after_core_fixes.txt",
    "mypy_report_after_prioritizer_fix.txt",
    "mypy_report_phase2.txt",
    "pytest_batch4_results.txt",
    "pytest_collect.txt",
    "pytest_output.txt",
    "pytest_verbose_output.txt",
    "radon_cc.txt",
    "radon_cc_updated.txt",
    "radon_mi.txt",
    "ruff_final_status.txt",
    "ruff_format_diff.txt",
    "ruff_latest_report.txt",
    "ruff_lint.txt",
    "ruff_lint_final_pass1.txt",
    "ruff_lint_final_pass2.txt",
    "ruff_lint_updated.txt",
    "ruff_violations_after.txt",
    "ruff_violations_before.txt",
    "schema_import_test.txt",
    "simple_test_collection.log",
    "temp_core_test_output.txt",
    "temp_docstring_check.txt",
    "test_collection_report.txt",
    "test_output.log",
    "test_output.txt",
    "test_result.txt",
    "updated_missing_docstrings.txt",
    "validation_output.txt",
    "validation_results.txt",
    "yaml_grep.txt",
    "0.5.3", # Obsolete file
    "ACTIVATION_COMPLETE.md", # Obsolete report
    "AUDIT_PACKAGE.md", # Obsolete report
    "audit_package_summary.md", # Obsolete report
    "AUTONOMOUS_ACTIVATION_PLAN.md", # Obsolete report
    "AUTONOMOUS_ACTIVATION_SUCCESS.md", # Obsolete report
    "AUTONOMOUS_AWAKENING_SUCCESS.md", # Obsolete report
    "AUTONOMOUS_AWAKENING_VALIDATION_COMPLETE.md", # Obsolete report
    "AUTONOMOUS_ENGINEERING_SUCCESS_REPORT.md", # Obsolete report
    "AUTONOMOUS_VERIFICATION_GUIDE.md", # Obsolete report
    "BATCH10_COMPLETION_REPORT.md", # Obsolete report
    "BATCH10_FINAL_COMPLETION_REPORT.md", # Obsolete report
    "BATCH10_PHASE1_COMPLETION_REPORT.md", # Obsolete report
    "BATCH10_PHASE2_COMPLETION_REPORT.md", # Obsolete report
    "BATCH10_PROACTIVE_ENGINEER_COMPLETE.md", # Obsolete report
    "BATCH8_COMPLETION_REPORT.md", # Obsolete report
    "BATCH8_LEARNING_LOOP_COMPLETE.md", # Obsolete report
    "BATCH8_VERIFICATION_SUMMARY.md", # Obsolete report
    "BATCH9_GENESIS_PROTOCOL.md", # Obsolete report
    "BATCH9_GENESIS_PROTOCOL_COMPLETE.md", # Obsolete report
    "BATCH9_PHASE1_COMPLETION_REPORT.md", # Obsolete report
    "BATCH9_PHASE3_PROVING_GROUND.md", # Obsolete report
    "BATCH_1_COMPLETION_STATUS.md", # Obsolete report
    "CIRCULAR_DEPENDENCY_REFACTORING_PROGRESS.md", # Obsolete report
    "CODE_HEALTH_AUDIT_PHASE1.md", # Obsolete report
    "DATABASE_INFRASTRUCTURE_COMPLETE.md", # Obsolete report
    "DATABASE_INFRASTRUCTURE_LOCKED.md", # Obsolete report
    "DEPENDENCIES_ALEMBIC_VERIFICATION.md", # Obsolete report
    "DEPLOYMENT_READY.md", # Obsolete report
    "EXECUTION_BLOCKER_RESOLVED.md", # Obsolete report
    "FINAL_INFRASTRUCTURE_SUMMARY.md", # Obsolete report
    "FIRST_AUTONOMOUS_ASSIGNMENT_COMPLETE.md", # Obsolete report
    "FULL_SYSTEM_VALIDATION_REPORT.md", # Obsolete report
    "GENESIS_MONITORING_ACTIVE.md", # Obsolete report
    "GENESIS_PROTOCOL_MISSION_COMPLETE.md", # Obsolete report
    "GENESIS_PROTOCOL_VALIDATION_COMPLETE.md", # Obsolete report
    "GENESIS_SPARK_OBSERVATION_LOG.md", # Obsolete report
    "GENESIS_SPARK_ULTIMATE_TEST.md", # Obsolete report
    "GENESIS_STATUS_CLARIFICATION.md", # Obsolete report
    "GOALS_API_FIX_APPLIED.md", # Obsolete report
    "HOW_TO_OBSERVE_AUTONOMOUS_DEVELOPMENT.md", # Obsolete report
    "HOW_TO_VERIFY_AUTONOMOUS_ACTIVITY.md", # Obsolete report
    "HOW_TO_VERIFY_AUTONOMOUS_INTELLIGENCE.md", # Obsolete report
    "IMPORT_ISSUES_RESOLVED.md", # Obsolete report
    "IMPORT_RESOLUTION_SUMMARY.md", # Obsolete report
    "INFRASTRUCTURE_COMMIT_MESSAGE.md", # Obsolete report
    "INFRASTRUCTURE_LOCKED_FINAL.md", # Obsolete report
    "INFRASTRUCTURE_STATUS_LOCKED.md", # Obsolete report
    "INFRASTRUCTURE_VALIDATION_COMPLETE.md", # Obsolete report
    "INTEGRATION_STATUS_REPORT.md", # Obsolete report
    "Kor'tana.State.md", # Obsolete report
    "Kor'tana.Vision.md", # Obsolete report
    "LAUNCH_SEQUENCE_FINAL.md", # Obsolete report
    "MODEL_ROUTING_COMPLETION_REPORT.md", # Obsolete report
    "PHASE2_COMPLETE_SUCCESS.md", # Obsolete report
    "PHASE2_COMPLETION_SUMMARY.md", # Obsolete report
    "PHASE2_FRONTEND_IMPLEMENTATION.md", # Obsolete report
    "PHASE4_CODE_REVIEW_COMPLETE.md", # Obsolete report
    "PHASE4_CODE_REVIEW_REPORT.md", # Obsolete report
    "PHASE4_OBSERVATION_INITIATION_COMPLETE.md", # Obsolete report
    "PHASE4_OBSERVATION_REPORT.md", # Obsolete report
    "PHASE6_COMPLETION_REPORT.md", # Obsolete report
    "PROJECT_STATUS_AUTONOMOUS.md", # Obsolete report
    "PROVING_GROUND_COMPLETE_STATUS.md", # Obsolete report
    "PROVING_GROUND_FINAL_STATUS.md", # Obsolete report
    "PROVING_GROUND_INITIATION.md", # Obsolete report
    "PROVING_GROUND_LAUNCH_PROTOCOL.md", # Obsolete report
    "PROVING_GROUND_LAUNCH_READY.md", # Obsolete report
    "PROVING_GROUND_LAUNCH_STATUS.md", # Obsolete report
    "PROVING_GROUND_REPORT_1.md", # Obsolete report
    "PROVING_GROUND_STATUS_UPDATE.md", # Obsolete report
    "PROVING_GROUND_SUCCESS_REPORT.md", # Obsolete report
    "QUICKSTART_CONNECTION.md", # Obsolete report
    "QUICK_START_VERIFICATION.md", # Obsolete report
    "README_PRODUCTION.md", # Obsolete report
    "SERVER_FIX_APPLIED.md", # Obsolete report
    "STABILIZATION_COMPLETION_REPORT.md", # Obsolete report
    "STATUS.md", # Obsolete report
    "TWO_TERMINAL_PROTOCOL.md", # Obsolete report
    "VSCODE_SETUP.md", # Obsolete report
    "kortana.db", # Database file
    "kortana_memory_dev.db", # Database file
    "temp_path_test.py", # Seems like a temporary script
    "temp_core_test.py", # Seems like a temporary script
    "temp_docstring_check.txt", # Temporary file
    "tracked_files.txt", # Temporary file
    "item['code']", # Likely a leftover from debugging
    "dict[str", # Likely a leftover from debugging
    "tuple[bool", # Likely a leftover from debugging
    "check)", # Likely a leftover from debugging
]

# Audit: move scripts
print("\n🔍 Auditing and moving scripts...")
scripts_moved_count = 0
for target in script_targets:
    for file in project_root.glob(target):
        if file.is_file() and file.name != "clean_and_document.py": # Don't move self
            try:
                print(f"Moving script: {file.name} to scripts/")
                shutil.move(str(file), str(scripts_dir / file.name))
                scripts_moved_count += 1
            except PermissionError:
                print(f"Skipping locked file: {file.name}")
            except Exception as e:
                print(f"Error moving {file.name}: {e}")

print(f"✅ Moved {scripts_moved_count} scripts.")

# Archive: move logs and obsolete files from root
print("\n🔍 Archiving logs and obsolete files from root...")
obsolete_archived_count = 0
for target in obsolete_targets:
    for file in project_root.glob(target):
        if file.is_file() and file.name not in ["README.md", "KOR'TANA_BLUEPRINT.md"]:# Don't archive key docs
            try:
                print(f"Archiving obsolete file: {file.name} to archive/")
                shutil.move(str(file), str(archive_dir / file.name))
                obsolete_archived_count += 1
            except PermissionError:
                print(f"Skipping locked file: {file.name}")
            except Exception as e:
                print(f"Error archiving {file.name}: {e}")

print(f"✅ Archived {obsolete_archived_count} obsolete files from root.")

# Archive: move logs and obsolete files from data/
print("\n🔍 Archiving logs and obsolete files from data/...")
data_obsolete_archived_count = 0
for target in obsolete_targets:
    for file in data_dir.glob(target):
        if file.is_file():
            try:
                print(f"Archiving obsolete file: {file.name} from data/ to archive/")
                shutil.move(str(file), str(archive_dir / file.name))
                data_obsolete_archived_count += 1
            except PermissionError:
                print(f"Skipping locked file: {file.name}")
            except Exception as e:
                print(f"Error archiving {file.name}: {e}")

print(f"✅ Archived {data_obsolete_archived_count} obsolete files from data/.")

# Update README.md
print("\n📝 Updating README.md with new directory structure...")
if readme_path.exists():
    content = readme_path.read_text()
    # Remove old directory structure section if it exists
    content = content.split("\n## Directory Structure\n")[0]
    new_content = content
    new_content += "\n## Directory Structure\n" + \
        "\nThis section describes the main directories in the project.\n" + \
        "\n- **`/src`**: Contains the main Kor'tana source code.\n" + \
        "- **`/scripts`**: Contains all utility scripts, test runners, and one-off automation scripts.\n" + \
        "- **`/archive`**: Stores old logs, temporary files, and obsolete documentation/reports.\n" + \
        "- **`/data`**: Contains runtime data, logs, and outputs generated by Kor'tana.\n" + \
        "- **`/tests`**: Contains dedicated unit and integration tests (managed separately from scripts).\n" + \
        "- **`/docs`**: Project documentation.\n" + \
        "- **`/notebooks`**: Jupyter notebooks for exploration and analysis.\n" + \
        "- **`/alembic`**: Database migration scripts.\n" + \
        "- **`/config`**: Configuration files.\n" + \
        "- **`/state`**: Runtime state information.\n" + \
        "- **`/vault`**: Sensitive configuration or data (if applicable).\n" + \
        "- **`/venv`**: Python virtual environment.\n" + \
        "- **`/node_modules`**: Frontend dependencies (for LobeChat frontend).\n" + \
        "- **`/lobechat-frontend`**: LobeChat frontend source code.\n"

    readme_path.write_text(new_content)
    print("✅ README.md updated")
else:
    print("Warning: README.md not found, skipping update")

print("\n✅ Janitor Agent: Directory audit and cleanup complete")
