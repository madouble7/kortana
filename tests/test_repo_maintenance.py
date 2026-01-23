"""
Tests for the Repository Maintenance modules.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import json

from src.kortana.core.repo_maintenance import (
    CodeCleaner,
    FileClassifier,
    HealthMonitor
)


class TestCodeCleaner:
    """Test the CodeCleaner class."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        
        # Create test files
        (temp_path / "good_file.py").write_text("""
import os
def hello():
    return os.path.exists('test')
""")
        
        (temp_path / "empty_file.py").write_text("")
        
        (temp_path / "duplicate_imports.py").write_text("""
import os
import sys
import os
""")
        
        (temp_path / "unused_import.py").write_text("""
import unused_module
def hello():
    return "hello"
""")
        
        yield temp_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_analyze_codebase(self, temp_repo):
        """Test analyzing codebase for cleanup."""
        cleaner = CodeCleaner(temp_repo)
        cleanup_items = cleaner.analyze_codebase()
        
        assert len(cleanup_items) > 0
    
    def test_find_empty_files(self, temp_repo):
        """Test finding empty files."""
        cleaner = CodeCleaner(temp_repo)
        cleanup_items = cleaner.analyze_codebase()
        
        empty_files = [item for item in cleanup_items if item.item_type == "file"]
        assert len(empty_files) > 0
        assert any("empty_file.py" in item.file_path for item in empty_files)
    
    def test_find_duplicate_imports(self, temp_repo):
        """Test finding duplicate imports."""
        cleaner = CodeCleaner(temp_repo)
        cleanup_items = cleaner.analyze_codebase()
        
        duplicates = [
            item for item in cleanup_items 
            if item.reason == "Duplicate imports detected"
        ]
        assert len(duplicates) > 0
    
    def test_get_summary(self, temp_repo):
        """Test getting cleanup summary."""
        cleaner = CodeCleaner(temp_repo)
        cleanup_items = cleaner.analyze_codebase()
        summary = cleaner.get_summary()
        
        assert summary['total_items'] == len(cleanup_items)
        assert 'by_type' in summary
        assert 'safe_to_remove' in summary
        assert 'needs_review' in summary


class TestFileClassifier:
    """Test the FileClassifier class."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        
        # Create directory structure
        (temp_path / "src" / "kortana" / "core").mkdir(parents=True)
        (temp_path / "tests").mkdir()
        (temp_path / "docs").mkdir()
        (temp_path / "config").mkdir()
        
        # Create files
        (temp_path / "src" / "kortana" / "core" / "brain.py").write_text("# core")
        (temp_path / "tests" / "test_example.py").write_text("# test")
        (temp_path / "docs" / "README.md").write_text("# docs")
        (temp_path / "config" / "settings.yaml").write_text("# config")
        (temp_path / "pyproject.toml").write_text("# project")
        
        yield temp_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_classify_repository(self, temp_repo):
        """Test classifying repository files."""
        classifier = FileClassifier(temp_repo)
        metadata = classifier.classify_repository()
        
        assert len(metadata) > 0
    
    def test_file_categories(self, temp_repo):
        """Test file categorization."""
        classifier = FileClassifier(temp_repo)
        classifier.classify_repository()
        
        # Check that files are categorized correctly
        core_files = classifier.search_by_category("core")
        test_files = classifier.search_by_category("tests")
        doc_files = classifier.search_by_category("docs")
        
        assert len(core_files) > 0
        assert len(test_files) > 0
        assert len(doc_files) > 0
    
    def test_search_by_tag(self, temp_repo):
        """Test searching files by tag."""
        classifier = FileClassifier(temp_repo)
        classifier.classify_repository()
        
        # Search for Python files
        py_files = classifier.search_by_tag("ext:py")
        assert len(py_files) > 0
    
    def test_critical_files(self, temp_repo):
        """Test identifying critical files."""
        classifier = FileClassifier(temp_repo)
        classifier.classify_repository()
        
        critical_files = classifier.get_critical_files()
        # Should have at least the core files marked as critical
        assert len(critical_files) > 0
    
    def test_export_metadata(self, temp_repo, tmp_path):
        """Test exporting metadata."""
        classifier = FileClassifier(temp_repo)
        classifier.classify_repository()
        
        output_path = tmp_path / "metadata.json"
        classifier.export_metadata(output_path)
        
        assert output_path.exists()
        
        # Verify JSON is valid
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert len(data) > 0
    
    def test_organization_report(self, temp_repo):
        """Test getting organization report."""
        classifier = FileClassifier(temp_repo)
        classifier.classify_repository()
        
        report = classifier.get_organization_report()
        
        assert 'total_files' in report
        assert 'by_category' in report
        assert 'critical_files_count' in report
        assert report['total_files'] > 0


class TestHealthMonitor:
    """Test the HealthMonitor class."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        
        # Create directory structure
        (temp_path / "src").mkdir()
        (temp_path / "tests").mkdir()
        (temp_path / "docs").mkdir()
        
        # Create Python files
        (temp_path / "src" / "module1.py").write_text("""
\"\"\"Module 1 docstring.\"\"\"

def function1():
    return "test"

class Class1:
    pass
""")
        
        (temp_path / "src" / "module2.py").write_text("""
def function2():
    return "test2"
""")
        
        # Create other files
        (temp_path / "README.md").write_text("# Test")
        (temp_path / "pyproject.toml").write_text("[project]")
        (temp_path / ".gitignore").write_text("*.pyc")
        
        yield temp_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_collect_metrics(self, temp_repo):
        """Test collecting metrics."""
        monitor = HealthMonitor(temp_repo)
        metrics = monitor.collect_metrics()
        
        assert 'timestamp' in metrics
        assert 'code_quality' in metrics
        assert 'repository_stats' in metrics
        assert 'file_organization' in metrics
        assert 'health_score' in metrics
    
    def test_code_quality_metrics(self, temp_repo):
        """Test code quality metrics."""
        monitor = HealthMonitor(temp_repo)
        metrics = monitor.collect_metrics()
        
        cq = metrics['code_quality']
        assert cq['total_python_files'] > 0
        assert cq['total_lines_of_code'] > 0
        assert cq['total_functions'] > 0
        assert cq['total_classes'] > 0
    
    def test_repository_stats(self, temp_repo):
        """Test repository statistics."""
        monitor = HealthMonitor(temp_repo)
        metrics = monitor.collect_metrics()
        
        rs = metrics['repository_stats']
        assert rs['total_files'] > 0
        assert rs['total_size_mb'] >= 0
    
    def test_health_score(self, temp_repo):
        """Test health score calculation."""
        monitor = HealthMonitor(temp_repo)
        metrics = monitor.collect_metrics()
        
        assert 0 <= metrics['health_score'] <= 100
    
    def test_health_status(self, temp_repo):
        """Test health status."""
        monitor = HealthMonitor(temp_repo)
        status = monitor.get_health_status()
        
        assert status in ["Excellent", "Good", "Fair", "Needs Attention"]
    
    def test_generate_dashboard_data(self, temp_repo):
        """Test generating dashboard data."""
        monitor = HealthMonitor(temp_repo)
        dashboard = monitor.generate_dashboard_data()
        
        assert 'timestamp' in dashboard
        assert 'health_score' in dashboard
        assert 'health_status' in dashboard
        assert 'metrics' in dashboard
        assert 'recommendations' in dashboard
    
    def test_export_dashboard(self, temp_repo, tmp_path):
        """Test exporting dashboard."""
        monitor = HealthMonitor(temp_repo)
        output_path = tmp_path / "dashboard.json"
        
        monitor.export_dashboard(output_path)
        
        assert output_path.exists()
        
        # Verify JSON is valid
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert 'health_score' in data
