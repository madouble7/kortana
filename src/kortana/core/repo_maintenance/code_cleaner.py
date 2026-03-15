"""
Code Cleaner Module

Identifies and helps remove deprecated, unused, or redundant code.
"""

import ast
import logging
from pathlib import Path
from typing import List, Set, Dict, Any
from dataclasses import dataclass


@dataclass
class CleanupItem:
    """Represents an item that may need cleanup."""
    file_path: str
    item_type: str  # 'file', 'function', 'class', 'import'
    name: str
    reason: str
    recommendation: str
    safe_to_remove: bool = False


class CodeCleaner:
    """Identifies deprecated, unused, or redundant code."""
    
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        self.logger = logging.getLogger(__name__)
        self.cleanup_items: List[CleanupItem] = []
    
    def analyze_codebase(self) -> List[CleanupItem]:
        """Analyze the codebase for cleanup opportunities."""
        self.cleanup_items = []
        
        # Find empty files
        self._find_empty_files()
        
        # Find duplicate code patterns
        self._find_duplicate_imports()
        
        # Find unused imports (basic detection)
        self._find_potentially_unused_imports()
        
        return self.cleanup_items
    
    def _find_empty_files(self):
        """Find empty Python files that could be removed."""
        for py_file in self.root_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # Check if file is empty or only has comments
                if not content or all(
                    line.strip().startswith('#') or not line.strip()
                    for line in content.split('\n')
                ):
                    # Don't flag __init__.py as it can be intentionally empty
                    if py_file.name != "__init__.py":
                        self.cleanup_items.append(CleanupItem(
                            file_path=str(py_file),
                            item_type="file",
                            name=py_file.name,
                            reason="File is empty or contains only comments",
                            recommendation="Consider removing if not needed",
                            safe_to_remove=False  # Manual review needed
                        ))
            except Exception as e:
                self.logger.debug(f"Error checking {py_file}: {e}")
    
    def _find_duplicate_imports(self):
        """Find files with duplicate imports."""
        for py_file in self.root_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                imports = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            for alias in node.names:
                                imports.append(f"{node.module}.{alias.name}")
                
                # Find duplicates
                seen = set()
                duplicates = set()
                for imp in imports:
                    if imp in seen:
                        duplicates.add(imp)
                    seen.add(imp)
                
                if duplicates:
                    self.cleanup_items.append(CleanupItem(
                        file_path=str(py_file),
                        item_type="import",
                        name=", ".join(sorted(duplicates)),
                        reason="Duplicate imports detected",
                        recommendation="Remove duplicate import statements",
                        safe_to_remove=True
                    ))
            
            except Exception as e:
                self.logger.debug(f"Error analyzing imports in {py_file}: {e}")
    
    def _find_potentially_unused_imports(self):
        """Basic detection of potentially unused imports using AST."""
        for py_file in self.root_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Collect imports
                imports = {}
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            import_name = alias.asname if alias.asname else alias.name
                            imports[import_name] = node.lineno
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            import_name = alias.asname if alias.asname else alias.name
                            imports[import_name] = node.lineno
                
                # Check if imports are used in the AST
                used_names = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name):
                        used_names.add(node.id)
                
                # Flag potentially unused imports
                for import_name, lineno in imports.items():
                    if import_name not in used_names and import_name != '*':
                        self.cleanup_items.append(CleanupItem(
                            file_path=str(py_file),
                            item_type="import",
                            name=import_name,
                            reason=f"Import '{import_name}' appears unused (AST analysis)",
                            recommendation="Verify usage and remove if not needed",
                            safe_to_remove=False  # Needs verification
                        ))
            
            except Exception as e:
                self.logger.debug(f"Error checking unused imports in {py_file}: {e}")
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped."""
        skip_patterns = [
            "__pycache__",
            ".venv",
            "venv",
            "node_modules",
            ".git",
            "archive",
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of cleanup recommendations."""
        by_type = {}
        safe_to_remove_count = 0
        
        for item in self.cleanup_items:
            if item.item_type not in by_type:
                by_type[item.item_type] = 0
            by_type[item.item_type] += 1
            
            if item.safe_to_remove:
                safe_to_remove_count += 1
        
        return {
            'total_items': len(self.cleanup_items),
            'by_type': by_type,
            'safe_to_remove': safe_to_remove_count,
            'needs_review': len(self.cleanup_items) - safe_to_remove_count
        }
