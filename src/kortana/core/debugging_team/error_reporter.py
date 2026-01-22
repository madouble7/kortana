"""
Error Reporting Module

Creates structured reports of detected errors and issues.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from .error_detector import DetectedError


class ErrorReporter:
    """Generates structured reports of detected errors."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("audit_results")
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def generate_report(
        self, 
        errors: List[DetectedError], 
        format: str = "json"
    ) -> str:
        """
        Generate an error report in the specified format.
        
        Args:
            errors: List of detected errors
            format: Output format ('json', 'markdown', 'text')
        
        Returns:
            Path to the generated report file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            return self._generate_json_report(errors, timestamp)
        elif format == "markdown":
            return self._generate_markdown_report(errors, timestamp)
        else:
            return self._generate_text_report(errors, timestamp)
    
    def _generate_json_report(
        self, 
        errors: List[DetectedError], 
        timestamp: str
    ) -> str:
        """Generate a JSON report."""
        report_path = self.output_dir / f"error_report_{timestamp}.json"
        
        report_data = {
            "timestamp": timestamp,
            "total_errors": len(errors),
            "errors": [
                {
                    "file_path": e.file_path,
                    "line_number": e.line_number,
                    "error_type": e.error_type,
                    "severity": e.severity,
                    "message": e.message,
                    "suggestion": e.suggestion
                }
                for e in errors
            ]
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        self.logger.info(f"Generated JSON report: {report_path}")
        return str(report_path)
    
    def _generate_markdown_report(
        self, 
        errors: List[DetectedError], 
        timestamp: str
    ) -> str:
        """Generate a Markdown report."""
        report_path = self.output_dir / f"error_report_{timestamp}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Error Report - {timestamp}\n\n")
            f.write(f"**Total Errors:** {len(errors)}\n\n")
            
            # Group by severity
            for severity in ['critical', 'high', 'medium', 'low']:
                severity_errors = [e for e in errors if e.severity == severity]
                if severity_errors:
                    f.write(f"## {severity.upper()} Severity ({len(severity_errors)})\n\n")
                    
                    for error in severity_errors:
                        f.write(f"### {error.error_type}\n")
                        f.write(f"- **File:** `{error.file_path}`\n")
                        f.write(f"- **Line:** {error.line_number}\n")
                        f.write(f"- **Message:** {error.message}\n")
                        if error.suggestion:
                            f.write(f"- **Suggestion:** {error.suggestion}\n")
                        f.write("\n")
        
        self.logger.info(f"Generated Markdown report: {report_path}")
        return str(report_path)
    
    def _generate_text_report(
        self, 
        errors: List[DetectedError], 
        timestamp: str
    ) -> str:
        """Generate a plain text report."""
        report_path = self.output_dir / f"error_report_{timestamp}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"ERROR REPORT - {timestamp}\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total Errors: {len(errors)}\n\n")
            
            for i, error in enumerate(errors, 1):
                f.write(f"{i}. [{error.severity.upper()}] {error.error_type}\n")
                f.write(f"   File: {error.file_path}:{error.line_number}\n")
                f.write(f"   {error.message}\n")
                if error.suggestion:
                    f.write(f"   Suggestion: {error.suggestion}\n")
                f.write("\n")
        
        self.logger.info(f"Generated text report: {report_path}")
        return str(report_path)
    
    def print_summary(self, errors: List[DetectedError]):
        """Print a summary of errors to console."""
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for error in errors:
            severity_counts[error.severity] += 1
        
        print("\n" + "=" * 60)
        print("ERROR DETECTION SUMMARY")
        print("=" * 60)
        print(f"Total Errors Found: {len(errors)}")
        print(f"  Critical: {severity_counts['critical']}")
        print(f"  High:     {severity_counts['high']}")
        print(f"  Medium:   {severity_counts['medium']}")
        print(f"  Low:      {severity_counts['low']}")
        print("=" * 60 + "\n")
