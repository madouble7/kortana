#!/usr/bin/env python3
"""
Simple test script for debugging and maintenance modules.
Run this to verify the modules work correctly.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Direct imports to avoid core __init__.py issues
from kortana.core.debugging_team.error_detector import ErrorDetector, DetectedError
from kortana.core.debugging_team.error_reporter import ErrorReporter
from kortana.core.debugging_team.resolution_engine import ResolutionEngine

from kortana.core.repo_maintenance.code_cleaner import CodeCleaner
from kortana.core.repo_maintenance.file_classifier import FileClassifier
from kortana.core.repo_maintenance.health_monitor import HealthMonitor


def test_error_detector():
    """Test ErrorDetector."""
    print("Testing ErrorDetector...")
    
    # Create temp repo
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Create test files
        (temp_path / "good.py").write_text('def hello(): return "hi"')
        (temp_path / "syntax_err.py").write_text('def bad(: pass')
        (temp_path / "bare_except.py").write_text('try:\n    x=1\nexcept:\n    pass')
        
        # Test detection
        detector = ErrorDetector(temp_path)
        errors = detector.scan_directory()
        
        assert len(errors) > 0, "Should detect errors"
        assert any(e.error_type == "SyntaxError" for e in errors), "Should detect syntax error"
        assert any(e.error_type == "BareExcept" for e in errors), "Should detect bare except"
        
        # Test summary
        summary = detector.get_summary()
        assert summary['total_errors'] == len(errors)
        
        print(f"✓ ErrorDetector passed ({len(errors)} errors detected)")
    
    finally:
        shutil.rmtree(temp_dir)


def test_error_reporter():
    """Test ErrorReporter."""
    print("Testing ErrorReporter...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Create sample errors
        errors = [
            DetectedError(
                file_path="test.py",
                line_number=10,
                error_type="SyntaxError",
                severity="critical",
                message="Invalid syntax",
                suggestion="Fix it"
            )
        ]
        
        # Test report generation
        reporter = ErrorReporter(Path(temp_dir))
        report_path = reporter.generate_report(errors, format="json")
        
        assert Path(report_path).exists(), "Report should be created"
        
        print("✓ ErrorReporter passed")
    
    finally:
        shutil.rmtree(temp_dir)


def test_resolution_engine():
    """Test ResolutionEngine."""
    print("Testing ResolutionEngine...")
    
    errors = [
        DetectedError(
            file_path="test.py",
            line_number=10,
            error_type="BareExcept",
            severity="medium",
            message="Bare except",
            suggestion="Use specific exception"
        )
    ]
    
    engine = ResolutionEngine()
    
    # Test resolutions
    resolutions = engine.generate_resolutions(errors)
    assert len(resolutions) > 0, "Should generate resolutions"
    
    # Test quick fixes
    quick_fixes = engine.get_quick_fixes(errors)
    assert isinstance(quick_fixes, list), "Should return list"
    
    # Test action plan
    action_plan = engine.create_action_plan(errors)
    assert len(action_plan) > 0, "Should create action plan"
    
    print("✓ ResolutionEngine passed")


def test_code_cleaner():
    """Test CodeCleaner."""
    print("Testing CodeCleaner...")
    
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Create test files
        (temp_path / "good.py").write_text('import os\nprint(os.name)')
        (temp_path / "empty.py").write_text('')
        (temp_path / "dup_imports.py").write_text('import os\nimport os')
        
        cleaner = CodeCleaner(temp_path)
        items = cleaner.analyze_codebase()
        
        assert len(items) > 0, "Should find cleanup items"
        
        summary = cleaner.get_summary()
        assert summary['total_items'] == len(items)
        
        print(f"✓ CodeCleaner passed ({len(items)} items found)")
    
    finally:
        shutil.rmtree(temp_dir)


def test_file_classifier():
    """Test FileClassifier."""
    print("Testing FileClassifier...")
    
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Create structure
        (temp_path / "src" / "kortana" / "core").mkdir(parents=True)
        (temp_path / "tests").mkdir()
        (temp_path / "src" / "kortana" / "core" / "brain.py").write_text("# core")
        (temp_path / "tests" / "test.py").write_text("# test")
        
        classifier = FileClassifier(temp_path)
        metadata = classifier.classify_repository()
        
        assert len(metadata) > 0, "Should classify files"
        
        # Test search
        core_files = classifier.search_by_category("core")
        test_files = classifier.search_by_category("tests")
        
        assert len(core_files) > 0, "Should find core files"
        assert len(test_files) > 0, "Should find test files"
        
        # Test report
        report = classifier.get_organization_report()
        assert report['total_files'] > 0
        
        print(f"✓ FileClassifier passed ({report['total_files']} files classified)")
    
    finally:
        shutil.rmtree(temp_dir)


def test_health_monitor():
    """Test HealthMonitor."""
    print("Testing HealthMonitor...")
    
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Create structure
        (temp_path / "src").mkdir()
        (temp_path / "src" / "module.py").write_text('"""Module."""\ndef func(): pass')
        (temp_path / "README.md").write_text("# Test")
        (temp_path / "pyproject.toml").write_text("[project]")
        
        monitor = HealthMonitor(temp_path)
        
        # Test metrics collection
        metrics = monitor.collect_metrics()
        assert 'health_score' in metrics
        assert 0 <= metrics['health_score'] <= 100
        
        # Test status
        status = monitor.get_health_status()
        assert status in ["Excellent", "Good", "Fair", "Needs Attention"]
        
        # Test dashboard
        dashboard = monitor.generate_dashboard_data()
        assert 'health_score' in dashboard
        assert 'recommendations' in dashboard
        
        print(f"✓ HealthMonitor passed (health score: {metrics['health_score']})")
    
    finally:
        shutil.rmtree(temp_dir)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("TESTING DEBUGGING & MAINTENANCE MODULES")
    print("=" * 60 + "\n")
    
    tests = [
        test_error_detector,
        test_error_reporter,
        test_resolution_engine,
        test_code_cleaner,
        test_file_classifier,
        test_health_monitor,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
