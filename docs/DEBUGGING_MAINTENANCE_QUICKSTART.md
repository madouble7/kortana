# Quick Start Guide: Debugging & Repository Maintenance Team

This guide will help you get started with Kor'tana's debugging and repository maintenance tools.

## Installation

The tools are part of the Kor'tana core package. No additional dependencies are required beyond the standard Kor'tana installation.

## Quick Start

### 1. Run a Full Repository Audit

The easiest way to get started is to run a complete audit:

```bash
python src/repo_health_cli.py audit
```

This will:
- Scan all Python files for errors
- Analyze code for cleanup opportunities
- Classify all files with metadata
- Check git branches
- Calculate repository health score
- Generate detailed reports in `audit_results/`

### 2. Check Repository Health

Get a quick health check:

```bash
python src/repo_health_cli.py health
```

Output example:
```
📊 HEALTH DASHBOARD:
  Health Score: 75.2/100
  Status: Good

📈 CODE QUALITY:
  Python files: 837
  Lines of code: 96837
  Functions: 2866
  Classes: 435
  Documentation rate: 25.6%

💡 RECOMMENDATIONS:
  • Improve documentation: Less than 50% of files have docstrings
```

### 3. Detect Errors

Find errors and get resolution suggestions:

```bash
python src/repo_health_cli.py detect --report --resolution
```

This will:
- Scan for syntax errors
- Find anti-patterns (bare excepts, etc.)
- Detect TODO/FIXME comments
- Generate a prioritized action plan
- Save a detailed report

### 4. Analyze Code for Cleanup

Find code that can be cleaned up:

```bash
python src/repo_health_cli.py clean --details
```

This identifies:
- Empty files
- Duplicate imports
- Potentially unused imports
- Items safe to remove vs. needing review

### 5. Classify Files

Organize and tag all repository files:

```bash
python src/repo_health_cli.py classify --export --critical
```

This will:
- Categorize all files (core, api, tests, docs, etc.)
- Generate searchable tags
- Identify critical files that should be protected
- Export metadata to JSON

### 6. Analyze Branches

Check git branch health:

```bash
python src/repo_health_cli.py branches --recommendations
```

This identifies:
- Stale branches (90+ days old)
- Branches that don't follow naming conventions
- Merged branches safe to delete
- Active vs. inactive branches

## Understanding the Output

### Health Score

- **80-100**: Excellent - Repository is well-maintained
- **60-79**: Good - Minor improvements recommended  
- **40-59**: Fair - Several issues to address
- **0-39**: Needs Attention - Significant maintenance required

### Error Severity Levels

- **Critical**: Syntax errors, blockers that prevent code execution
- **High**: Security issues, major bugs
- **Medium**: Anti-patterns, code smells
- **Low**: TODOs, minor issues

### Reports Location

All reports are saved to `audit_results/`:
- `error_report_[timestamp].md` - Markdown format error report
- `health_dashboard.json` - JSON format health metrics
- `file_metadata.json` - Complete file classification data

## Common Use Cases

### Before Committing Code

Run error detection to catch issues:
```bash
python src/repo_health_cli.py detect
```

### Weekly Maintenance

Run full audit to track repository health:
```bash
python src/repo_health_cli.py audit
```

### Before Release

1. Run full audit
2. Fix critical and high-severity issues
3. Clean up stale branches
4. Verify health score is above 70

### Code Review Preparation

Get cleanup recommendations:
```bash
python src/repo_health_cli.py clean --details
python src/repo_health_cli.py classify --critical
```

## Integrating with CI/CD

You can add the health check to your CI pipeline:

```yaml
# Example GitHub Actions workflow
- name: Repository Health Check
  run: |
    python src/repo_health_cli.py health
    python src/repo_health_cli.py detect --report
```

## Advanced Usage

### Programmatic Access

```python
from pathlib import Path
from kortana.core.debugging_team.error_detector import ErrorDetector
from kortana.core.repo_maintenance.health_monitor import HealthMonitor

# Detect errors
detector = ErrorDetector(Path.cwd())
errors = detector.scan_directory()

# Get health metrics
monitor = HealthMonitor(Path.cwd())
metrics = monitor.collect_metrics()
print(f"Health Score: {metrics['health_score']}")
```

### Custom Thresholds

Modify branch age threshold for stale detection:

```python
from kortana.core.repo_maintenance.branch_manager import BranchManager

manager = BranchManager()
stale_branches = manager.get_stale_branches(days_threshold=60)  # 60 days instead of default 90
```

## Troubleshooting

### No Git Repository Found

If branch analysis fails, ensure you're running from a git repository:
```bash
cd /path/to/kortana
python src/repo_health_cli.py branches
```

### Import Errors

If you see import errors, ensure you're running from the repository root:
```bash
cd /path/to/kortana
python src/repo_health_cli.py --help
```

### Permission Issues

On Unix systems, you may need to make the CLI executable:
```bash
chmod +x src/repo_health_cli.py
./src/repo_health_cli.py health
```

## Getting Help

Use the `--help` flag with any command:
```bash
python src/repo_health_cli.py --help
python src/repo_health_cli.py detect --help
python src/repo_health_cli.py health --help
```

Enable verbose logging for debugging:
```bash
python src/repo_health_cli.py -v health
```

## Next Steps

1. Run your first audit: `python src/repo_health_cli.py audit`
2. Review the generated reports in `audit_results/`
3. Address critical issues first
4. Set up regular health checks (weekly/monthly)
5. Consider integrating with your CI/CD pipeline

For more detailed information, see the [full README](./README.md).
