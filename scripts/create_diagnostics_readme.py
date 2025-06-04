#!/usr/bin/env python
"""
Create README for Diagnostics Results

This script creates a README.md file in the diagnostics_results directory
to guide sanctuary through analyzing the diagnostic outputs.
"""

import datetime
from pathlib import Path


def create_readme():
    """Create the README.md file in the diagnostics_results directory."""
    # Create the directory if it doesn't exist
    output_dir = Path("diagnostic_results")
    output_dir.mkdir(exist_ok=True)

    # Create the README file
    readme_path = output_dir / "README.md"

    with open(readme_path, "w") as f:
        f.write(f"""# Kor'tana Environment Diagnostics

Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Diagnostic Files

This directory contains the outputs from various diagnostic tests run on the Kor'tana environment:

1. **exec_result.txt** - Basic Python execution test
   - Shows the Python executable path
   - Current working directory
   - sys.path entries

2. **environment_report.txt** - Comprehensive environment details
   - System information
   - Virtual environment info
   - Python path
   - Environment variables
   - Installed packages
   - Configuration files

3. **diag_env_result.txt** - Output from diagnose_environment.py
   - Detailed environment diagnostic
   - Import success/failure
   - Package structure analysis

4. **config_load_result.txt** - Configuration loading test results
   - Config module import
   - YAML file loading
   - Overlay configuration
   - Environment variable handling

5. **integrated_result.txt** - Integrated environment and config test
   - Combined test of environment and configuration
   - End-to-end configuration pipeline testing

6. **audit_log.txt** - Complete audit artifacts collection
   - Repository details
   - Tracked files
   - Test coverage results
   - Full diagnostics

7. **summary.txt** - Key findings summary
   - Highlights critical information from all tests
   - Current environment state assessment

## How to Review

1. Start by reviewing the **summary.txt** file for a high-level overview
2. Check **exec_result.txt** to confirm the basic Python environment
3. Review **environment_report.txt** for detailed environment diagnostics
4. Examine **config_load_result.txt** to see if configuration loading works
5. Check **integrated_result.txt** for end-to-end testing
6. Review **diag_env_result.txt** for in-depth environment analysis
7. Review **audit_log.txt** for complete audit details

## Important Note

**DO NOT** proceed with any configuration code or environment refactors until sanctuary (matt) has reviewed these diagnostic results and confirmed a stable, reproducible environment.

The purpose of these diagnostics is to establish a known-good environment baseline for the configuration system before making any changes.
""")

    print(f"Created README.md in {output_dir}")
    return str(readme_path)


if __name__ == "__main__":
    readme_path = create_readme()
    print(f"README created: {readme_path}")
    print("Run the diagnostic scripts to populate this directory with test results.")
