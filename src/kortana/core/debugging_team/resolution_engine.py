"""
Resolution Engine Module

Provides automated resolution suggestions and helpers for detected errors.
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
from .error_detector import DetectedError


class ResolutionEngine:
    """Generates and applies automated resolutions for detected errors."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.resolution_strategies = {
            "SyntaxError": self._suggest_syntax_fix,
            "BareExcept": self._suggest_bare_except_fix,
            "EmptyFile": self._suggest_empty_file_fix,
            "TodoComment": self._suggest_todo_fix,
        }
    
    def generate_resolutions(
        self, 
        errors: List[DetectedError]
    ) -> Dict[str, List[str]]:
        """
        Generate resolution suggestions for errors.
        
        Returns:
            Dictionary mapping error types to lists of suggestions
        """
        resolutions = {}
        
        for error in errors:
            if error.error_type not in resolutions:
                resolutions[error.error_type] = []
            
            strategy = self.resolution_strategies.get(error.error_type)
            if strategy:
                suggestion = strategy(error)
                resolutions[error.error_type].append(suggestion)
        
        return resolutions
    
    def _suggest_syntax_fix(self, error: DetectedError) -> str:
        """Suggest fix for syntax errors."""
        return (
            f"File: {error.file_path}\n"
            f"Line {error.line_number}: {error.message}\n"
            f"Action: Review and fix the syntax error manually.\n"
            f"This requires developer attention to understand the context."
        )
    
    def _suggest_bare_except_fix(self, error: DetectedError) -> str:
        """Suggest fix for bare except clauses."""
        return (
            f"File: {error.file_path}\n"
            f"Line {error.line_number}: Replace 'except:' with specific exception.\n"
            f"Example: except Exception as e:\n"
            f"         or except (ValueError, TypeError) as e:"
        )
    
    def _suggest_empty_file_fix(self, error: DetectedError) -> str:
        """Suggest fix for empty files."""
        return (
            f"File: {error.file_path}\n"
            f"Action: Either remove the file or add content.\n"
            f"If it's intentionally empty, add a docstring explaining why."
        )
    
    def _suggest_todo_fix(self, error: DetectedError) -> str:
        """Suggest fix for TODO comments."""
        return (
            f"File: {error.file_path}\n"
            f"Line {error.line_number}: {error.message}\n"
            f"Action: Create an issue or implement the TODO item."
        )
    
    def get_quick_fixes(
        self, 
        errors: List[DetectedError], 
        max_fixes: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get a list of quick fixes that can be automated.
        
        Args:
            errors: List of detected errors
            max_fixes: Maximum number of quick fixes to return
        
        Returns:
            List of quick fix suggestions
        """
        quick_fixes = []
        
        for error in errors[:max_fixes]:
            if error.error_type == "BareExcept":
                quick_fixes.append({
                    "file": error.file_path,
                    "line": error.line_number,
                    "type": "replace",
                    "old": "except:",
                    "new": "except Exception as e:",
                    "description": "Replace bare except with specific exception"
                })
        
        return quick_fixes
    
    def create_action_plan(
        self, 
        errors: List[DetectedError]
    ) -> List[str]:
        """
        Create a prioritized action plan for fixing errors.
        
        Returns:
            List of action items prioritized by severity
        """
        action_plan = []
        
        # Group by severity
        critical = [e for e in errors if e.severity == "critical"]
        high = [e for e in errors if e.severity == "high"]
        medium = [e for e in errors if e.severity == "medium"]
        low = [e for e in errors if e.severity == "low"]
        
        if critical:
            action_plan.append(
                f"PRIORITY 1: Fix {len(critical)} critical errors immediately"
            )
            for error in critical[:5]:  # Show first 5
                action_plan.append(f"  - {error.file_path}:{error.line_number} - {error.error_type}")
        
        if high:
            action_plan.append(
                f"PRIORITY 2: Address {len(high)} high-severity issues"
            )
        
        if medium:
            action_plan.append(
                f"PRIORITY 3: Review {len(medium)} medium-severity issues"
            )
        
        if low:
            action_plan.append(
                f"PRIORITY 4: Consider addressing {len(low)} low-severity items"
            )
        
        return action_plan
