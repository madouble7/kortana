#!/usr/bin/env python3
"""
Repository Health & Maintenance CLI

Command-line interface for the debugging and repository maintenance team.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Direct imports to avoid circular dependency issues with core/__init__.py
from kortana.core.debugging_team.error_detector import ErrorDetector
from kortana.core.debugging_team.error_reporter import ErrorReporter
from kortana.core.debugging_team.resolution_engine import ResolutionEngine

from kortana.core.repo_maintenance.code_cleaner import CodeCleaner
from kortana.core.repo_maintenance.file_classifier import FileClassifier
from kortana.core.repo_maintenance.branch_manager import BranchManager
from kortana.core.repo_maintenance.health_monitor import HealthMonitor


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def cmd_detect_errors(args):
    """Detect errors in the codebase."""
    print("\n🔍 Scanning codebase for errors...")
    
    detector = ErrorDetector(Path.cwd())
    errors = detector.scan_directory()
    
    reporter = ErrorReporter()
    reporter.print_summary(errors)
    
    if args.report:
        report_path = reporter.generate_report(errors, format=args.format)
        print(f"\n📄 Report generated: {report_path}")
    
    if args.resolution:
        print("\n🔧 Generating resolution suggestions...")
        resolver = ResolutionEngine()
        action_plan = resolver.create_action_plan(errors)
        
        print("\n📋 ACTION PLAN:")
        for item in action_plan:
            print(f"  {item}")


def cmd_clean_code(args):
    """Analyze code for cleanup opportunities."""
    print("\n🧹 Analyzing codebase for cleanup opportunities...")
    
    cleaner = CodeCleaner(Path.cwd())
    cleanup_items = cleaner.analyze_codebase()
    
    summary = cleaner.get_summary()
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"  Total items found: {summary['total_items']}")
    print(f"  Safe to remove: {summary['safe_to_remove']}")
    print(f"  Needs review: {summary['needs_review']}")
    print(f"\n  By type:")
    for item_type, count in summary['by_type'].items():
        print(f"    {item_type}: {count}")
    
    if args.details:
        print("\n📝 CLEANUP ITEMS:")
        for item in cleanup_items[:20]:  # Show first 20
            print(f"\n  [{item.item_type}] {item.name}")
            print(f"    File: {item.file_path}")
            print(f"    Reason: {item.reason}")
            print(f"    Recommendation: {item.recommendation}")


def cmd_classify_files(args):
    """Classify and organize repository files."""
    print("\n📂 Classifying repository files...")
    
    classifier = FileClassifier(Path.cwd())
    classifier.classify_repository()
    
    report = classifier.get_organization_report()
    
    print(f"\n📊 ORGANIZATION REPORT:")
    print(f"  Total files: {report['total_files']}")
    print(f"  Critical files: {report['critical_files_count']}")
    print(f"\n  Files by category:")
    for category, count in sorted(report['by_category'].items()):
        print(f"    {category}: {count}")
    
    if args.export:
        output_path = Path("audit_results/file_metadata.json")
        output_path.parent.mkdir(exist_ok=True)
        classifier.export_metadata(output_path)
        print(f"\n💾 Metadata exported to: {output_path}")
    
    if args.critical:
        print("\n🔒 CRITICAL FILES (protected):")
        critical_files = classifier.get_critical_files()
        for file_meta in critical_files[:20]:
            print(f"  - {file_meta.path}")


def cmd_analyze_branches(args):
    """Analyze git branches."""
    print("\n🌿 Analyzing git branches...")
    
    manager = BranchManager()
    report = manager.get_branch_report()
    
    print(f"\n📊 BRANCH REPORT:")
    print(f"  Total branches: {report['total_branches']}")
    print(f"  Active branches: {report['active_branches']}")
    print(f"  Merged branches: {report['merged_branches']}")
    print(f"  Compliant branches: {report['compliant_branches']}")
    print(f"  Compliance rate: {report['compliance_rate']}")
    print(f"  Cleanup candidates: {report['cleanup_candidates']}")
    
    if args.recommendations:
        print("\n💡 CLEANUP RECOMMENDATIONS:")
        recommendations = manager.get_cleanup_recommendations()
        
        if recommendations['safe_to_delete']:
            print(f"\n  Safe to delete ({len(recommendations['safe_to_delete'])}):")
            for branch in recommendations['safe_to_delete'][:10]:
                print(f"    - {branch}")
        
        if recommendations['non_compliant_naming']:
            print(f"\n  Non-compliant naming ({len(recommendations['non_compliant_naming'])}):")
            for branch in recommendations['non_compliant_naming'][:10]:
                print(f"    - {branch}")


def cmd_health_check(args):
    """Check repository health."""
    print("\n❤️  Checking repository health...")
    
    monitor = HealthMonitor(Path.cwd())
    dashboard_data = monitor.generate_dashboard_data()
    
    print(f"\n📊 HEALTH DASHBOARD:")
    print(f"  Health Score: {dashboard_data['health_score']}/100")
    print(f"  Status: {dashboard_data['health_status']}")
    
    print(f"\n📈 CODE QUALITY:")
    cq = dashboard_data['metrics']['code_quality']
    print(f"  Python files: {cq['total_python_files']}")
    print(f"  Lines of code: {cq['total_lines_of_code']}")
    print(f"  Functions: {cq['total_functions']}")
    print(f"  Classes: {cq['total_classes']}")
    print(f"  Documentation rate: {cq['documentation_rate']}")
    
    print(f"\n📦 REPOSITORY STATS:")
    rs = dashboard_data['metrics']['repository_stats']
    print(f"  Total files: {rs['total_files']}")
    print(f"  Total size: {rs['total_size_mb']} MB")
    print(f"  File types: {rs['file_types']}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in dashboard_data['recommendations']:
        print(f"  • {rec}")
    
    if args.export:
        output_path = Path("audit_results/health_dashboard.json")
        output_path.parent.mkdir(exist_ok=True)
        monitor.export_dashboard(output_path)
        print(f"\n💾 Dashboard exported to: {output_path}")


def cmd_full_audit(args):
    """Run a complete repository audit."""
    print("\n" + "=" * 70)
    print("🔍 RUNNING FULL REPOSITORY AUDIT")
    print("=" * 70)
    
    # Error detection
    print("\n1️⃣  ERROR DETECTION")
    print("-" * 70)
    detector = ErrorDetector(Path.cwd())
    errors = detector.scan_directory()
    summary = detector.get_summary()
    print(f"Found {summary['total_errors']} issues")
    print(f"  Critical: {summary['by_severity']['critical']}")
    print(f"  High: {summary['by_severity']['high']}")
    print(f"  Medium: {summary['by_severity']['medium']}")
    print(f"  Low: {summary['by_severity']['low']}")
    
    # Code cleanup
    print("\n2️⃣  CODE CLEANUP ANALYSIS")
    print("-" * 70)
    cleaner = CodeCleaner(Path.cwd())
    cleanup_items = cleaner.analyze_codebase()
    cleanup_summary = cleaner.get_summary()
    print(f"Found {cleanup_summary['total_items']} cleanup opportunities")
    print(f"  Safe to remove: {cleanup_summary['safe_to_remove']}")
    print(f"  Needs review: {cleanup_summary['needs_review']}")
    
    # File classification
    print("\n3️⃣  FILE ORGANIZATION")
    print("-" * 70)
    classifier = FileClassifier(Path.cwd())
    classifier.classify_repository()
    org_report = classifier.get_organization_report()
    print(f"Analyzed {org_report['total_files']} files")
    print(f"Protected {org_report['critical_files_count']} critical files")
    
    # Branch analysis
    print("\n4️⃣  BRANCH ANALYSIS")
    print("-" * 70)
    try:
        manager = BranchManager()
        branch_report = manager.get_branch_report()
        print(f"Total branches: {branch_report['total_branches']}")
        print(f"Active: {branch_report['active_branches']}")
        print(f"Cleanup candidates: {branch_report['cleanup_candidates']}")
    except Exception as e:
        print(f"Branch analysis skipped: {e}")
    
    # Health check
    print("\n5️⃣  HEALTH ASSESSMENT")
    print("-" * 70)
    monitor = HealthMonitor(Path.cwd())
    dashboard_data = monitor.generate_dashboard_data()
    print(f"Health Score: {dashboard_data['health_score']}/100")
    print(f"Status: {dashboard_data['health_status']}")
    
    # Generate reports
    print("\n" + "=" * 70)
    print("📄 GENERATING REPORTS")
    print("=" * 70)
    
    output_dir = Path("audit_results")
    output_dir.mkdir(exist_ok=True)
    
    # Error report
    reporter = ErrorReporter(output_dir)
    error_report = reporter.generate_report(errors, format="markdown")
    print(f"✓ Error report: {error_report}")
    
    # Health dashboard
    monitor.export_dashboard(output_dir / "health_dashboard.json")
    print(f"✓ Health dashboard: {output_dir / 'health_dashboard.json'}")
    
    # File metadata
    classifier.export_metadata(output_dir / "file_metadata.json")
    print(f"✓ File metadata: {output_dir / 'file_metadata.json'}")
    
    print("\n" + "=" * 70)
    print("✅ AUDIT COMPLETE")
    print("=" * 70)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Kor'tana Repository Health & Maintenance Tool"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Error detection command
    detect_parser = subparsers.add_parser('detect', help='Detect errors in codebase')
    detect_parser.add_argument('--report', action='store_true', help='Generate report')
    detect_parser.add_argument('--format', choices=['json', 'markdown', 'text'], 
                              default='markdown', help='Report format')
    detect_parser.add_argument('--resolution', action='store_true', 
                              help='Generate resolution suggestions')
    
    # Code cleanup command
    clean_parser = subparsers.add_parser('clean', help='Analyze code for cleanup')
    clean_parser.add_argument('--details', action='store_true', 
                             help='Show detailed cleanup items')
    
    # File classification command
    classify_parser = subparsers.add_parser('classify', help='Classify repository files')
    classify_parser.add_argument('--export', action='store_true', 
                                help='Export metadata to JSON')
    classify_parser.add_argument('--critical', action='store_true', 
                                help='List critical files')
    
    # Branch analysis command
    branch_parser = subparsers.add_parser('branches', help='Analyze git branches')
    branch_parser.add_argument('--recommendations', action='store_true', 
                              help='Show cleanup recommendations')
    
    # Health check command
    health_parser = subparsers.add_parser('health', help='Check repository health')
    health_parser.add_argument('--export', action='store_true', 
                              help='Export dashboard data')
    
    # Full audit command
    audit_parser = subparsers.add_parser('audit', help='Run full repository audit')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    setup_logging(args.verbose)
    
    # Route to appropriate command
    commands = {
        'detect': cmd_detect_errors,
        'clean': cmd_clean_code,
        'classify': cmd_classify_files,
        'branches': cmd_analyze_branches,
        'health': cmd_health_check,
        'audit': cmd_full_audit,
    }
    
    command_func = commands.get(args.command)
    if command_func:
        try:
            command_func(args)
        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
