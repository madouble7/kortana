#!/usr/bin/env python3
"""
Simple Directory Analysis for Kor'tana Project
"""

from pathlib import Path


def analyze_directory():
    """Generate stats and recommendations for directory cleanup."""
    root_dir = Path(".")

    # Get all files in the root directory
    root_files = [f for f in root_dir.glob("*") if f.is_file()]

    # Count files by type/pattern
    python_files = [f for f in root_files if f.name.endswith(".py")]
    md_files = [f for f in root_files if f.name.endswith(".md")]
    log_files = [f for f in root_files if f.name.endswith(".log")]
    txt_files = [f for f in root_files if f.name.endswith(".txt")]
    batch_files = [f for f in root_files if f.name.endswith(".bat") or f.name.endswith(".cmd")]
    ps_files = [f for f in root_files if f.name.endswith(".ps1")]

    # Count specific patterns
    test_scripts = [f for f in python_files if f.name.startswith("test_")]
    check_scripts = [f for f in python_files if f.name.startswith("check_")]
    run_scripts = [f for f in python_files if f.name.startswith("run_")]
    validate_scripts = [f for f in python_files if f.name.startswith("validate_")]
    launch_scripts = [f for f in python_files if f.name.startswith("launch_")]
    batch_scripts = [f for f in python_files if f.name.startswith("batch")]
    monitoring_scripts = [f for f in python_files if f.name.startswith("monitor_")]

    # Print directory analysis
    print("\nPROJECT DIRECTORY ANALYSIS")
    print("=" * 50)
    print(f"Total files in root directory: {len(root_files)}")
    print(f"Python scripts in root: {len(python_files)} ({len(python_files)/len(root_files)*100:.1f}%)")
    print(f"Markdown files in root: {len(md_files)} ({len(md_files)/len(root_files)*100:.1f}%)")
    print(f"Log files in root: {len(log_files)} ({len(log_files)/len(root_files)*100:.1f}%)")
    print(f"Text files in root: {len(txt_files)} ({len(txt_files)/len(root_files)*100:.1f}%)")
    print(f"Batch/CMD files in root: {len(batch_files)} ({len(batch_files)/len(root_files)*100:.1f}%)")
    print(f"PowerShell scripts in root: {len(ps_files)} ({len(ps_files)/len(root_files)*100:.1f}%)")

    print("\nSCRIPT CATEGORIES")
    print("-" * 50)
    print(f"Test scripts (test_*.py): {len(test_scripts)}")
    print(f"Check scripts (check_*.py): {len(check_scripts)}")
    print(f"Run scripts (run_*.py): {len(run_scripts)}")
    print(f"Validate scripts (validate_*.py): {len(validate_scripts)}")
    print(f"Launch scripts (launch_*.py): {len(launch_scripts)}")
    print(f"Batch scripts (batch*.py): {len(batch_scripts)}")
    print(f"Monitoring scripts (monitor_*.py): {len(monitoring_scripts)}")

    # Check for existing organization directories
    scripts_dir = root_dir / "scripts"
    archive_dir = root_dir / "archive"

    print("\nDIRECTORY STATUS")
    print("-" * 50)
    print(f"Scripts directory: {'EXISTS' if scripts_dir.exists() else 'NEEDS CREATION'}")
    print(f"Archive directory: {'EXISTS' if archive_dir.exists() else 'NEEDS CREATION'}")

    # Generate cleanup plan
    print("\nCLEANUP ACTION PLAN")
    print("=" * 50)
    print("1. Create organization directories")
    if not scripts_dir.exists():
        print("   - Create scripts/ directory")
    if not archive_dir.exists():
        print("   - Create archive/ directory")

    print("\n2. Move one-off scripts to scripts/ directory")
    print(f"   - {len(test_scripts)} test scripts")
    print(f"   - {len(check_scripts)} check scripts")
    print(f"   - {len(run_scripts)} run scripts")
    print(f"   - {len(validate_scripts)} validate scripts")
    print(f"   - {len(launch_scripts)} launch scripts")
    print(f"   - {len(batch_scripts)} batch scripts")
    print(f"   - {len(monitoring_scripts)} monitoring scripts")

    print("\n3. Move old logs and output files to archive/ directory")
    print(f"   - {len(log_files)} log files")
    print(f"   - {len(txt_files)} text files (reports, outputs)")

    print("\n4. Update README.md with new directory structure")

if __name__ == "__main__":
    analyze_directory()
