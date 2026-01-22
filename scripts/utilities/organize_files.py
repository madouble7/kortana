#!/usr/bin/env python3
"""
Script to organize root directory files into appropriate subdirectories.
"""
import os
import shutil
from pathlib import Path

def move_files():
    """Move files from root to appropriate subdirectories."""
    root = Path(".")
    
    # Define move mappings
    moves = {
        # Test scripts -> scripts/tests/
        "scripts/tests/": [f for f in root.glob("test_*.py") if f.is_file()],
        
        # Check scripts -> scripts/checks/
        "scripts/checks/": [f for f in root.glob("check_*.py") if f.is_file()],
        
        # Launch scripts -> scripts/launchers/
        "scripts/launchers/": [
            *list(root.glob("launch_*.py")),
            *list(root.glob("launch_*.bat")),
            *list(root.glob("start_*.py")),
            *list(root.glob("start_*.bat")),
            *list(root.glob("run_*.bat")),
        ],
        
        # Monitor scripts -> scripts/monitoring/
        "scripts/monitoring/": [f for f in root.glob("monitor_*.py") if f.is_file()],
        
        # Batch/validation scripts -> scripts/utilities/
        "scripts/utilities/": [
            *list(root.glob("batch*.py")),
            *list(root.glob("validate_*.py")),
            *list(root.glob("verify_*.py")),
            *list(root.glob("run_*.py")),
            *list(root.glob("*_check*.py")),
            *list(root.glob("*_test*.py")),
            *list(root.glob("diagnose_*.py")),
            *list(root.glob("debug_*.py")),
            *list(root.glob("inspect_*.py")),
            *list(root.glob("investigate_*.py")),
            *list(root.glob("create_*.py")),
            *list(root.glob("setup_*.py")),
            *list(root.glob("init*.py")),
            *list(root.glob("activate_*.py")),
            *list(root.glob("assign_*.py")),
            *list(root.glob("*_demo.py")),
            *list(root.glob("*_validation*.py")),
            *list(root.glob("*_verification*.py")),
            *list(root.glob("demonstrate_*.py")),
            *list(root.glob("autonomous_*.py")),
            *list(root.glob("genesis_*.py")),
            *list(root.glob("kortana_*.py")),
            *list(root.glob("observe_*.py")),
            *list(root.glob("phase*.py")),
            *list(root.glob("proving_ground_*.py")),
            *list(root.glob("quick_*.py")),
            *list(root.glob("submit_*.py")),
            *list(root.glob("trigger_*.py")),
            *list(root.glob("simulate_*.py")),
            *list(root.glob("complete_*.py")),
            *list(root.glob("restart_*.py")),
            *list(root.glob("*.ps1")),
            *list(root.glob("*.cmd")),
        ],
        
        # Reports and completion docs -> archive/reports/
        "archive/reports/": [
            *list(root.glob("*_REPORT*.md")),
            *list(root.glob("*_COMPLETION*.md")),
            *list(root.glob("*_STATUS*.md")),
            *list(root.glob("*_SUCCESS*.md")),
            *list(root.glob("*_VALIDATION*.md")),
            *list(root.glob("*_VERIFICATION*.md")),
            *list(root.glob("*_COMPLETE*.md")),
            *list(root.glob("BATCH*.md")),
            *list(root.glob("PHASE*.md")),
            *list(root.glob("*_PROTOCOL*.md")),
            *list(root.glob("*_LOG*.md")),
            *list(root.glob("*_GUIDE*.md")),
            *list(root.glob("*PROVING_GROUND*.md")),
            *list(root.glob("*GENESIS*.md")),
            *list(root.glob("*AUTONOMOUS*.md")),
            *list(root.glob("*GHOST*.md")),
            *list(root.glob("TWO_TERMINAL_PROTOCOL.md")),
        ],
        
        # Batch-related python files -> archive/batches/
        "archive/batches/": [
            *list(root.glob("BATCH*.py")),
            *list(root.glob("FIRST_AUTONOMOUS*.py")),
        ],
    }
    
    # Move files
    moved_count = 0
    for dest_dir, files in moves.items():
        # Get unique files (avoid duplicates from multiple globs)
        unique_files = list(set(f for f in files if f.is_file()))
        
        for file_path in unique_files:
            # Skip if file is already in a subdirectory
            if len(file_path.parts) > 1:
                continue
            
            # Skip core files
            if file_path.name in ["push.py", "initialize_database.py", "initiate_proving_ground.py"]:
                continue
            
            dest_path = Path(dest_dir) / file_path.name
            
            # Skip if destination already exists
            if dest_path.exists():
                print(f"  Skipping {file_path.name} (already exists at destination)")
                continue
            
            try:
                shutil.move(str(file_path), str(dest_path))
                print(f"  Moved: {file_path.name} -> {dest_dir}")
                moved_count += 1
            except Exception as e:
                print(f"  Error moving {file_path.name}: {e}")
    
    print(f"\nTotal files moved: {moved_count}")
    
    # List remaining files in root
    print("\n" + "="*50)
    print("Remaining files in root directory:")
    print("="*50)
    remaining = sorted([f for f in root.glob("*") if f.is_file() and not f.name.startswith(".")])
    for f in remaining:
        size = f.stat().st_size
        print(f"  {f.name:50s} ({size:>8d} bytes)")
    print(f"\nTotal remaining files: {len(remaining)}")

if __name__ == "__main__":
    move_files()
