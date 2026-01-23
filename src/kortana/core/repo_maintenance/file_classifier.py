"""
File Classifier Module

Classifies and organizes files by relevance and purpose with metadata tagging.
"""

import logging
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass
import json


@dataclass
class FileMetadata:
    """Metadata for a file."""
    path: str
    category: str
    tags: List[str]
    purpose: str
    is_critical: bool
    last_modified: float


class FileClassifier:
    """Classifies files and creates searchable metadata."""
    
    # Protected paths that should never be modified/deleted
    CRITICAL_PATHS = {
        "src/kortana/core",
        "src/kortana/brain.py",
        "src/kortana/main.py",
        "alembic",
        "pyproject.toml",
        "requirements.txt",
        ".git",
    }
    
    # File categories and their patterns
    CATEGORIES = {
        "core": ["src/kortana/core", "src/kortana/brain"],
        "api": ["src/kortana/api", "api_server.py"],
        "agents": ["src/kortana/agents", "autonomous_agents"],
        "tests": ["tests/", "test_"],
        "config": ["config/", ".env", ".yaml", ".toml", ".ini"],
        "docs": ["docs/", "README", "*.md"],
        "scripts": ["scripts/", "*.bat", "*.sh"],
        "data": ["data/", "*.db", "*.json", "*.csv"],
        "archive": ["archive/"],
        "temporary": ["tmp/", "temp/", "__pycache__"],
    }
    
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        self.logger = logging.getLogger(__name__)
        self.file_metadata: Dict[str, FileMetadata] = {}
    
    def classify_repository(self) -> Dict[str, FileMetadata]:
        """Classify all files in the repository."""
        self.file_metadata = {}
        
        for file_path in self.root_path.rglob("*"):
            if file_path.is_file():
                metadata = self._classify_file(file_path)
                self.file_metadata[str(file_path)] = metadata
        
        return self.file_metadata
    
    def _classify_file(self, file_path: Path) -> FileMetadata:
        """Classify a single file."""
        relative_path = file_path.relative_to(self.root_path)
        str_path = str(relative_path)
        
        # Determine category
        category = self._determine_category(str_path)
        
        # Generate tags
        tags = self._generate_tags(file_path, category)
        
        # Determine purpose
        purpose = self._infer_purpose(file_path, category)
        
        # Check if critical
        is_critical = self._is_critical_file(str_path)
        
        return FileMetadata(
            path=str_path,
            category=category,
            tags=tags,
            purpose=purpose,
            is_critical=is_critical,
            last_modified=file_path.stat().st_mtime
        )
    
    def _determine_category(self, file_path: str) -> str:
        """Determine the category of a file."""
        for category, patterns in self.CATEGORIES.items():
            for pattern in patterns:
                if pattern in file_path or file_path.startswith(pattern):
                    return category
        return "other"
    
    def _generate_tags(self, file_path: Path, category: str) -> List[str]:
        """Generate searchable tags for a file."""
        tags = [category]
        
        # Add extension-based tags
        if file_path.suffix:
            tags.append(f"ext:{file_path.suffix[1:]}")
        
        # Add name-based tags
        name_lower = file_path.name.lower()
        if "test" in name_lower:
            tags.append("test")
        if "config" in name_lower or "setup" in name_lower:
            tags.append("config")
        if "util" in name_lower or "helper" in name_lower:
            tags.append("utility")
        if "main" in name_lower or "app" in name_lower:
            tags.append("entry-point")
        if "agent" in name_lower:
            tags.append("agent")
        if "model" in name_lower or "schema" in name_lower:
            tags.append("data-model")
        
        return list(set(tags))  # Remove duplicates
    
    def _infer_purpose(self, file_path: Path, category: str) -> str:
        """Infer the purpose of a file."""
        purposes = {
            "core": "Core system functionality",
            "api": "API endpoint or service",
            "agents": "Autonomous agent implementation",
            "tests": "Test suite",
            "config": "Configuration",
            "docs": "Documentation",
            "scripts": "Utility script",
            "data": "Data storage or processing",
            "archive": "Archived/deprecated code",
            "temporary": "Temporary file",
        }
        return purposes.get(category, "General purpose file")
    
    def _is_critical_file(self, file_path: str) -> bool:
        """Check if a file is critical and should be protected."""
        return any(
            critical_path in file_path 
            for critical_path in self.CRITICAL_PATHS
        )
    
    def search_by_tag(self, tag: str) -> List[FileMetadata]:
        """Search files by tag."""
        return [
            metadata for metadata in self.file_metadata.values()
            if tag in metadata.tags
        ]
    
    def search_by_category(self, category: str) -> List[FileMetadata]:
        """Search files by category."""
        return [
            metadata for metadata in self.file_metadata.values()
            if metadata.category == category
        ]
    
    def get_critical_files(self) -> List[FileMetadata]:
        """Get all critical files that should be protected."""
        return [
            metadata for metadata in self.file_metadata.values()
            if metadata.is_critical
        ]
    
    def export_metadata(self, output_path: Path):
        """Export file metadata to JSON."""
        data = {
            path: {
                "category": meta.category,
                "tags": meta.tags,
                "purpose": meta.purpose,
                "is_critical": meta.is_critical,
                "last_modified": meta.last_modified,
            }
            for path, meta in self.file_metadata.items()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Exported metadata to {output_path}")
    
    def get_organization_report(self) -> Dict[str, any]:
        """Get a report on repository organization."""
        category_counts = {}
        critical_count = 0
        
        for metadata in self.file_metadata.values():
            category_counts[metadata.category] = category_counts.get(metadata.category, 0) + 1
            if metadata.is_critical:
                critical_count += 1
        
        return {
            "total_files": len(self.file_metadata),
            "by_category": category_counts,
            "critical_files_count": critical_count,
            "categories": list(self.CATEGORIES.keys())
        }
