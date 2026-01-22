"""
Error Detection Module

Autonomously detects errors and inconsistencies in the codebase.
"""

import ast
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class DetectedError:
    """Represents a detected error or issue."""
    file_path: str
    line_number: int
    error_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    message: str
    suggestion: str = ""


class ErrorDetector:
    """Detects errors and inconsistencies in code automatically."""
    
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        self.logger = logging.getLogger(__name__)
        self.detected_errors: List[DetectedError] = []
    
    def scan_directory(self, directory: Path = None) -> List[DetectedError]:
        """Scan a directory for potential errors."""
        if directory is None:
            directory = self.root_path
        
        self.detected_errors = []
        
        for python_file in directory.rglob("*.py"):
            if self._should_skip_file(python_file):
                continue
            
            try:
                self._scan_python_file(python_file)
            except Exception as e:
                self.logger.warning(f"Error scanning {python_file}: {e}")
        
        return self.detected_errors
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped during scanning."""
        skip_patterns = [
            "__pycache__",
            ".venv",
            "venv",
            "node_modules",
            ".git",
            "archive",
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _scan_python_file(self, file_path: Path):
        """Scan a Python file for syntax and common errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for syntax errors
            try:
                ast.parse(content)
            except SyntaxError as e:
                self.detected_errors.append(DetectedError(
                    file_path=str(file_path),
                    line_number=e.lineno or 0,
                    error_type="SyntaxError",
                    severity="critical",
                    message=str(e),
                    suggestion="Fix syntax error to allow Python to parse the file."
                ))
            
            # Check for empty files that shouldn't be empty
            if len(content.strip()) == 0 and file_path.name != "__init__.py":
                self.detected_errors.append(DetectedError(
                    file_path=str(file_path),
                    line_number=0,
                    error_type="EmptyFile",
                    severity="low",
                    message="File is empty",
                    suggestion="Consider removing empty files or adding content."
                ))
            
            # Check for common anti-patterns
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Check for bare excepts
                if "except:" in line and "except Exception" not in line:
                    self.detected_errors.append(DetectedError(
                        file_path=str(file_path),
                        line_number=i,
                        error_type="BareExcept",
                        severity="medium",
                        message="Bare except clause found",
                        suggestion="Use specific exception types instead of bare 'except:'."
                    ))
                
                # Check for TODO/FIXME comments
                if "TODO" in line or "FIXME" in line:
                    self.detected_errors.append(DetectedError(
                        file_path=str(file_path),
                        line_number=i,
                        error_type="TodoComment",
                        severity="low",
                        message=f"Found: {line.strip()}",
                        suggestion="Address pending TODOs and FIXMEs."
                    ))
        
        except Exception as e:
            self.logger.debug(f"Could not parse {file_path}: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of detected errors."""
        severity_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for error in self.detected_errors:
            severity_counts[error.severity] += 1
        
        return {
            'total_errors': len(self.detected_errors),
            'by_severity': severity_counts,
            'critical_files': list(set(
                e.file_path for e in self.detected_errors 
                if e.severity == 'critical'
            ))
        }
