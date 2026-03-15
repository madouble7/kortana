# Debugging and Repository Maintenance Team

This module provides comprehensive debugging, code cleaning, and repository maintenance capabilities for the Kor'tana framework.

## Overview

The debugging and repository-cleaning team consists of several integrated modules:

1. **Automated Debugging** (`debugging_team/`)
   - Error detection and reporting
   - Resolution suggestions
   - Action plan generation

2. **Code Cleaning** (`repo_maintenance/`)
   - Deprecated code identification
   - Unused code detection
   - Duplicate code finder

3. **Repository Organization** 
   - File classification and tagging
   - Critical file protection
   - Searchable metadata

4. **Branch Management**
   - Stale branch detection
   - Naming convention enforcement
   - Cleanup recommendations

5. **Health Monitoring**
   - Real-time repository metrics
   - Code quality assessment
   - Health dashboard

## Installation

The modules are part of the Kor'tana core package. No additional installation is required.

## Usage

### Command-Line Interface

The primary interface is the `repo_health_cli.py` tool:

```bash
# Get help
python src/repo_health_cli.py --help

# Detect errors in codebase
python src/repo_health_cli.py detect --report --resolution

# Analyze code for cleanup opportunities
python src/repo_health_cli.py clean --details

# Classify repository files
python src/repo_health_cli.py classify --export --critical

# Analyze git branches
python src/repo_health_cli.py branches --recommendations

# Check repository health
python src/repo_health_cli.py health --export

# Run full audit
python src/repo_health_cli.py audit
```

### Programmatic Usage

```python
from kortana.core.debugging_team.error_detector import ErrorDetector
from kortana.core.debugging_team.error_reporter import ErrorReporter
from kortana.core.debugging_team.resolution_engine import ResolutionEngine

from kortana.core.repo_maintenance.code_cleaner import CodeCleaner
from kortana.core.repo_maintenance.file_classifier import FileClassifier
from kortana.core.repo_maintenance.branch_manager import BranchManager
from kortana.core.repo_maintenance.health_monitor import HealthMonitor

# Detect errors
detector = ErrorDetector(Path.cwd())
errors = detector.scan_directory()

# Generate report
reporter = ErrorReporter()
report_path = reporter.generate_report(errors, format="markdown")

# Get resolution suggestions
engine = ResolutionEngine()
action_plan = engine.create_action_plan(errors)

# Analyze code for cleanup
cleaner = CodeCleaner(Path.cwd())
cleanup_items = cleaner.analyze_codebase()

# Classify files
classifier = FileClassifier(Path.cwd())
metadata = classifier.classify_repository()
critical_files = classifier.get_critical_files()

# Monitor health
monitor = HealthMonitor(Path.cwd())
dashboard_data = monitor.generate_dashboard_data()
```

## Features

### Error Detection

- **Syntax Errors**: Identifies Python syntax errors
- **Anti-patterns**: Detects bare except clauses, unused imports
- **Code Smells**: Finds TODO/FIXME comments, empty files
- **Severity Levels**: Critical, High, Medium, Low

### Code Cleaning

- **Empty Files**: Identifies files with no content
- **Duplicate Imports**: Finds and flags duplicate import statements
- **Unused Imports**: Detects potentially unused imports
- **Safe Removal Flags**: Marks items safe to remove vs. needs review

### File Classification

- **Category System**: Organizes files into core, api, agents, tests, config, docs, scripts, data, archive
- **Tagging**: Automatic tag generation for searchability
- **Critical Protection**: Identifies and protects critical system files
- **Metadata Export**: Exports searchable metadata to JSON

Protected paths include:
- `src/kortana/core`
- `src/kortana/brain.py`
- `src/kortana/main.py`
- `alembic`
- `pyproject.toml`
- `.git`

### Branch Management

- **Naming Conventions**: Enforces standard naming (feature/, bugfix/, hotfix/, release/)
- **Stale Detection**: Identifies branches not updated in 90+ days
- **Merge Status**: Checks which branches are already merged
- **Cleanup Recommendations**: Suggests branches safe to delete

### Health Monitoring

Metrics collected:
- **Code Quality**: Files, lines of code, functions, classes, documentation rate
- **Repository Stats**: Total files/directories, size, file types
- **Organization**: Required files/directories present
- **Health Score**: Overall score (0-100) with status (Excellent/Good/Fair/Needs Attention)

## Report Outputs

All audit results are saved to the `audit_results/` directory:

- `error_report_[timestamp].md` - Detailed error report
- `health_dashboard.json` - Health metrics and recommendations  
- `file_metadata.json` - Complete file classification data

## Examples

### Full Repository Audit

```bash
python src/repo_health_cli.py audit
```

This runs a comprehensive audit including:
1. Error detection across all Python files
2. Code cleanup analysis
3. File organization review
4. Branch analysis
5. Health assessment
6. Report generation

### Targeted Error Detection

```bash
python src/repo_health_cli.py detect --report --format markdown --resolution
```

This generates a detailed error report with resolution suggestions.

### Branch Cleanup

```bash
python src/repo_health_cli.py branches --recommendations
```

This provides recommendations for cleaning up stale or non-compliant branches.

## Architecture

```
src/kortana/core/
├── debugging_team/
│   ├── __init__.py
│   ├── error_detector.py      # Error detection engine
│   ├── error_reporter.py      # Report generation
│   └── resolution_engine.py   # Resolution suggestions
└── repo_maintenance/
    ├── __init__.py
    ├── code_cleaner.py        # Code cleanup analysis
    ├── file_classifier.py     # File classification & tagging
    ├── branch_manager.py      # Branch management
    └── health_monitor.py      # Health monitoring & metrics
```

## Testing

Tests are located in `tests/test_debugging_team.py` and `tests/test_repo_maintenance.py`.

Run tests with:
```bash
pytest tests/test_debugging_team.py tests/test_repo_maintenance.py -v
```

## Future Enhancements

Potential areas for expansion:
- Integration with CI/CD pipelines
- Automated fix application (with safety checks)
- Historical trend analysis
- Slack/Discord notifications
- Web-based dashboard UI
- Custom rule configuration
- Language support beyond Python

## Contributing

When extending these modules:
1. Maintain minimal, surgical changes
2. Add comprehensive tests
3. Update documentation
4. Follow existing code style
5. Protect critical system files
6. Consider safety in all operations

## License

Part of the Kor'tana project. See main LICENSE file for details.
