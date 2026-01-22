"""
Tests for the Debugging Team modules.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.kortana.core.debugging_team import (
    ErrorDetector,
    ErrorReporter,
    ResolutionEngine,
    DetectedError
)


class TestErrorDetector:
    """Test the ErrorDetector class."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        
        # Create test files
        (temp_path / "good_file.py").write_text("""
def hello():
    \"\"\"A good function.\"\"\"
    return "Hello"
""")
        
        (temp_path / "syntax_error.py").write_text("""
def broken(:
    return "broken"
""")
        
        (temp_path / "bare_except.py").write_text("""
try:
    do_something()
except Exception as e:
    # This is better than bare except
    pass
""")
        
        (temp_path / "test_bare_except.py").write_text("""
# This file intentionally contains a bare except for testing
try:
    do_something()
except:  # noqa: E722 - intentional for testing
    pass
""")
        
        (temp_path / "empty_file.py").write_text("")
        
        (temp_path / "todo_file.py").write_text("""
# TODO: Implement this
def placeholder():
    pass
""")
        
        yield temp_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_scan_directory(self, temp_repo):
        """Test scanning a directory for errors."""
        detector = ErrorDetector(temp_repo)
        errors = detector.scan_directory()
        
        assert len(errors) > 0
        assert any(e.error_type == "SyntaxError" for e in errors)
    
    def test_detect_syntax_errors(self, temp_repo):
        """Test detection of syntax errors."""
        detector = ErrorDetector(temp_repo)
        errors = detector.scan_directory()
        
        syntax_errors = [e for e in errors if e.error_type == "SyntaxError"]
        assert len(syntax_errors) > 0
        assert any("syntax_error.py" in e.file_path for e in syntax_errors)
    
    def test_detect_bare_except(self, temp_repo):
        """Test detection of bare except clauses."""
        detector = ErrorDetector(temp_repo)
        errors = detector.scan_directory()
        
        bare_excepts = [e for e in errors if e.error_type == "BareExcept"]
        assert len(bare_excepts) > 0
        # Should detect in test_bare_except.py which has intentional bare except
        assert any("test_bare_except.py" in e.file_path for e in bare_excepts)
    
    def test_detect_empty_files(self, temp_repo):
        """Test detection of empty files."""
        detector = ErrorDetector(temp_repo)
        errors = detector.scan_directory()
        
        empty_files = [e for e in errors if e.error_type == "EmptyFile"]
        assert len(empty_files) > 0
        assert any("empty_file.py" in e.file_path for e in empty_files)
    
    def test_detect_todos(self, temp_repo):
        """Test detection of TODO comments."""
        detector = ErrorDetector(temp_repo)
        errors = detector.scan_directory()
        
        todos = [e for e in errors if e.error_type == "TodoComment"]
        assert len(todos) > 0
        assert any("todo_file.py" in e.file_path for e in todos)
    
    def test_get_summary(self, temp_repo):
        """Test getting error summary."""
        detector = ErrorDetector(temp_repo)
        errors = detector.scan_directory()
        summary = detector.get_summary()
        
        assert summary['total_errors'] == len(errors)
        assert 'by_severity' in summary
        assert all(
            severity in summary['by_severity']
            for severity in ['critical', 'high', 'medium', 'low']
        )


class TestErrorReporter:
    """Test the ErrorReporter class."""
    
    @pytest.fixture
    def sample_errors(self):
        """Create sample errors for testing."""
        return [
            DetectedError(
                file_path="test.py",
                line_number=10,
                error_type="SyntaxError",
                severity="critical",
                message="Invalid syntax",
                suggestion="Fix syntax"
            ),
            DetectedError(
                file_path="test2.py",
                line_number=20,
                error_type="BareExcept",
                severity="medium",
                message="Bare except found",
                suggestion="Use specific exception"
            )
        ]
    
    def test_generate_json_report(self, sample_errors, tmp_path):
        """Test generating JSON report."""
        reporter = ErrorReporter(tmp_path)
        report_path = reporter.generate_report(sample_errors, format="json")
        
        assert Path(report_path).exists()
        assert report_path.endswith(".json")
    
    def test_generate_markdown_report(self, sample_errors, tmp_path):
        """Test generating Markdown report."""
        reporter = ErrorReporter(tmp_path)
        report_path = reporter.generate_report(sample_errors, format="markdown")
        
        assert Path(report_path).exists()
        assert report_path.endswith(".md")
    
    def test_generate_text_report(self, sample_errors, tmp_path):
        """Test generating text report."""
        reporter = ErrorReporter(tmp_path)
        report_path = reporter.generate_report(sample_errors, format="text")
        
        assert Path(report_path).exists()
        assert report_path.endswith(".txt")


class TestResolutionEngine:
    """Test the ResolutionEngine class."""
    
    @pytest.fixture
    def sample_errors(self):
        """Create sample errors for testing."""
        return [
            DetectedError(
                file_path="test.py",
                line_number=10,
                error_type="SyntaxError",
                severity="critical",
                message="Invalid syntax",
                suggestion="Fix syntax"
            ),
            DetectedError(
                file_path="test2.py",
                line_number=20,
                error_type="BareExcept",
                severity="medium",
                message="Bare except found",
                suggestion="Use specific exception"
            ),
            DetectedError(
                file_path="test3.py",
                line_number=5,
                error_type="EmptyFile",
                severity="low",
                message="File is empty",
                suggestion="Add content or remove"
            )
        ]
    
    def test_generate_resolutions(self, sample_errors):
        """Test generating resolutions."""
        engine = ResolutionEngine()
        resolutions = engine.generate_resolutions(sample_errors)
        
        assert len(resolutions) > 0
        assert "SyntaxError" in resolutions
        assert "BareExcept" in resolutions
    
    def test_get_quick_fixes(self, sample_errors):
        """Test getting quick fixes."""
        engine = ResolutionEngine()
        quick_fixes = engine.get_quick_fixes(sample_errors)
        
        assert isinstance(quick_fixes, list)
        # Should have quick fix for BareExcept
        bare_except_fixes = [f for f in quick_fixes if f.get('type') == 'replace']
        assert len(bare_except_fixes) > 0
    
    def test_create_action_plan(self, sample_errors):
        """Test creating action plan."""
        engine = ResolutionEngine()
        action_plan = engine.create_action_plan(sample_errors)
        
        assert isinstance(action_plan, list)
        assert len(action_plan) > 0
        # Should prioritize critical errors
        assert any("PRIORITY 1" in item and "critical" in item for item in action_plan)
