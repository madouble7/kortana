"""
Module Registry for Kor'tana Marketplace
Manages module metadata and installations
"""

from datetime import datetime
from typing import Any, Optional


class ModuleMetadata:
    """Represents a marketplace module"""

    def __init__(
        self,
        name: str,
        version: str,
        author: str,
        description: str,
        category: str,
    ):
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.category = category
        self.downloads = 0
        self.rating = 0.0
        self.ratings_count = 0
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "category": self.category,
            "downloads": self.downloads,
            "rating": self.rating,
            "ratings_count": self.ratings_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ModuleRegistry:
    """Registry for marketplace modules"""

    def __init__(self):
        self.modules: dict[str, ModuleMetadata] = {}
        self.installed_modules: set[str] = set()

    def register_module(
        self,
        name: str,
        version: str,
        author: str,
        description: str,
        category: str = "general",
    ) -> ModuleMetadata:
        """
        Register a new module in the marketplace

        Args:
            name: Module name
            version: Module version
            author: Module author
            description: Module description
            category: Module category

        Returns:
            Module metadata
        """
        module = ModuleMetadata(name, version, author, description, category)
        self.modules[name] = module
        return module

    def get_module(self, name: str) -> Optional[ModuleMetadata]:
        """Get module metadata"""
        return self.modules.get(name)

    def list_modules(
        self, category: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        List all modules, optionally filtered by category

        Args:
            category: Optional category filter

        Returns:
            List of module metadata
        """
        modules = self.modules.values()
        if category:
            modules = [m for m in modules if m.category == category]
        return [m.to_dict() for m in modules]

    def search_modules(self, query: str) -> list[dict[str, Any]]:
        """
        Search modules by name or description

        Args:
            query: Search query

        Returns:
            List of matching modules
        """
        query_lower = query.lower()
        results = []
        for module in self.modules.values():
            if (
                query_lower in module.name.lower()
                or query_lower in module.description.lower()
            ):
                results.append(module.to_dict())
        return results

    def install_module(self, name: str) -> bool:
        """
        Mark a module as installed

        Args:
            name: Module name

        Returns:
            True if successful
        """
        if name not in self.modules:
            return False
        self.modules[name].downloads += 1
        self.installed_modules.add(name)
        return True

    def uninstall_module(self, name: str) -> bool:
        """
        Mark a module as uninstalled

        Args:
            name: Module name

        Returns:
            True if successful
        """
        if name in self.installed_modules:
            self.installed_modules.remove(name)
            return True
        return False

    def is_installed(self, name: str) -> bool:
        """Check if module is installed"""
        return name in self.installed_modules

    def rate_module(self, name: str, rating: float) -> bool:
        """
        Add a rating to a module

        Args:
            name: Module name
            rating: Rating value (1-5)

        Returns:
            True if successful
        """
        if name not in self.modules:
            return False

        module = self.modules[name]
        total = module.rating * module.ratings_count
        module.ratings_count += 1
        module.rating = (total + rating) / module.ratings_count
        return True
