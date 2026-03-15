"""
Health Monitor Module

Real-time repository health monitoring and metrics collection.
"""

import ast
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import json


class HealthMonitor:
    """Monitors repository health and provides real-time insights."""
    
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        self.logger = logging.getLogger(__name__)
        self.metrics_history: List[Dict[str, Any]] = []
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current repository health metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "code_quality": self._measure_code_quality(),
            "repository_stats": self._collect_repo_stats(),
            "file_organization": self._measure_organization(),
            "health_score": 0.0  # Will be calculated
        }
        
        # Calculate overall health score
        metrics["health_score"] = self._calculate_health_score(metrics)
        
        # Store in history
        self.metrics_history.append(metrics)
        
        return metrics
    
    def _measure_code_quality(self) -> Dict[str, Any]:
        """Measure basic code quality metrics using AST."""
        python_files = list(self.root_path.rglob("*.py"))
        
        # Filter out non-source files
        source_files = [
            f for f in python_files
            if not any(skip in str(f) for skip in [
                "__pycache__", ".venv", "venv", "archive", "node_modules"
            ])
        ]
        
        total_lines = 0
        total_functions = 0
        total_classes = 0
        files_with_docstrings = 0
        
        for file_path in source_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    total_lines += len(lines)
                    
                    # Use AST for accurate counting
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                            total_functions += 1
                        elif isinstance(node, ast.ClassDef):
                            total_classes += 1
                    
                    # Check for module docstring (first statement is a string)
                    if (tree.body and 
                        isinstance(tree.body[0], ast.Expr) and 
                        isinstance(tree.body[0].value, ast.Constant) and
                        isinstance(tree.body[0].value.value, str)):
                        files_with_docstrings += 1
            
            except Exception as e:
                self.logger.debug(f"Error reading {file_path}: {e}")
        
        documentation_rate = (
            files_with_docstrings / len(source_files) * 100
            if source_files else 0
        )
        
        return {
            "total_python_files": len(source_files),
            "total_lines_of_code": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "documentation_rate": f"{documentation_rate:.1f}%",
            "avg_lines_per_file": total_lines // len(source_files) if source_files else 0
        }
    
    def _collect_repo_stats(self) -> Dict[str, Any]:
        """Collect general repository statistics."""
        all_files = list(self.root_path.rglob("*"))
        files = [f for f in all_files if f.is_file()]
        
        # Count by extension
        extensions = {}
        for file in files:
            ext = file.suffix or "no_extension"
            extensions[ext] = extensions.get(ext, 0) + 1
        
        # Calculate total size
        total_size = sum(f.stat().st_size for f in files if f.exists())
        
        return {
            "total_files": len(files),
            "total_directories": len([f for f in all_files if f.is_dir()]),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": len(extensions),
            "most_common_extensions": self._get_top_extensions(extensions, 5)
        }
    
    def _get_top_extensions(
        self, 
        extensions: Dict[str, int], 
        top_n: int = 5
    ) -> Dict[str, int]:
        """Get the most common file extensions."""
        sorted_ext = sorted(
            extensions.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        return dict(sorted_ext[:top_n])
    
    def _measure_organization(self) -> Dict[str, Any]:
        """Measure repository organization quality."""
        required_files = [
            "README.md",
            "pyproject.toml",
            ".gitignore",
        ]
        
        required_dirs = [
            "src",
            "tests",
            "docs",
        ]
        
        files_present = sum(
            1 for f in required_files 
            if (self.root_path / f).exists()
        )
        
        dirs_present = sum(
            1 for d in required_dirs 
            if (self.root_path / d).exists()
        )
        
        organization_score = (
            (files_present / len(required_files) + dirs_present / len(required_dirs)) / 2 * 100
        )
        
        return {
            "required_files_present": files_present,
            "required_files_total": len(required_files),
            "required_dirs_present": dirs_present,
            "required_dirs_total": len(required_dirs),
            "organization_score": f"{organization_score:.1f}%"
        }
    
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate an overall health score (0-100)."""
        scores = []
        
        # Code quality score (based on documentation rate)
        doc_rate = float(metrics["code_quality"]["documentation_rate"].rstrip('%'))
        scores.append(doc_rate)
        
        # Organization score
        org_score = float(metrics["file_organization"]["organization_score"].rstrip('%'))
        scores.append(org_score)
        
        # File size health (penalize if too large)
        size_mb = metrics["repository_stats"]["total_size_mb"]
        size_score = min(100, max(0, 100 - (size_mb - 100) / 10)) if size_mb > 100 else 100
        scores.append(size_score)
        
        # Calculate weighted average
        return round(sum(scores) / len(scores), 1)
    
    def get_health_status(self) -> str:
        """Get human-readable health status."""
        current_metrics = self.collect_metrics()
        score = current_metrics["health_score"]
        
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Needs Attention"
    
    def get_trend_analysis(self) -> Dict[str, Any]:
        """Analyze trends in repository health over time."""
        if len(self.metrics_history) < 2:
            return {
                "trend": "insufficient_data",
                "message": "Need at least 2 data points for trend analysis"
            }
        
        # Compare first and last metrics
        first = self.metrics_history[0]
        last = self.metrics_history[-1]
        
        score_change = last["health_score"] - first["health_score"]
        
        return {
            "trend": "improving" if score_change > 0 else "declining" if score_change < 0 else "stable",
            "score_change": score_change,
            "data_points": len(self.metrics_history),
            "time_span": f"{first['timestamp']} to {last['timestamp']}"
        }
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard data."""
        current_metrics = self.collect_metrics()
        
        return {
            "timestamp": current_metrics["timestamp"],
            "health_score": current_metrics["health_score"],
            "health_status": self.get_health_status(),
            "metrics": current_metrics,
            "trend": self.get_trend_analysis(),
            "recommendations": self._generate_recommendations(current_metrics)
        }
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on metrics."""
        recommendations = []
        
        # Check documentation
        doc_rate = float(metrics["code_quality"]["documentation_rate"].rstrip('%'))
        if doc_rate < 50:
            recommendations.append(
                "Improve documentation: Less than 50% of files have docstrings"
            )
        
        # Check file organization
        org_score = float(metrics["file_organization"]["organization_score"].rstrip('%'))
        if org_score < 100:
            recommendations.append(
                "Complete repository structure: Some required files/directories are missing"
            )
        
        # Check repository size
        size_mb = metrics["repository_stats"]["total_size_mb"]
        if size_mb > 500:
            recommendations.append(
                f"Repository size is {size_mb}MB. Consider cleaning up large files or using Git LFS"
            )
        
        if not recommendations:
            recommendations.append("Repository health is good! Keep up the great work.")
        
        return recommendations
    
    def export_dashboard(self, output_path: Path):
        """Export dashboard data to JSON file."""
        dashboard_data = self.generate_dashboard_data()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2)
        
        self.logger.info(f"Exported dashboard to {output_path}")
