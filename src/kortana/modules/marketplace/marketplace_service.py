"""
Marketplace Service for Kor'tana
Manages module discovery, installation, and feedback
"""

from typing import Any

from .module_registry import ModuleRegistry


class MarketplaceService:
    """Service for marketplace operations"""

    def __init__(self):
        self.registry = ModuleRegistry()
        self._seed_example_modules()

    def _seed_example_modules(self):
        """Seed marketplace with example modules"""
        # Add some example modules
        self.registry.register_module(
            name="advanced-nlp",
            version="1.0.0",
            author="community-user-1",
            description="Advanced natural language processing capabilities",
            category="nlp",
        )
        self.registry.register_module(
            name="voice-commands",
            version="1.2.0",
            author="community-user-2",
            description="Voice command integration for Kor'tana",
            category="audio",
        )
        self.registry.register_module(
            name="database-connector",
            version="2.0.1",
            author="community-user-3",
            description="Connect to external databases",
            category="integration",
        )

    def browse_modules(self, category: str = None) -> dict[str, Any]:
        """
        Browse available modules

        Args:
            category: Optional category filter

        Returns:
            Dictionary with modules and count
        """
        modules = self.registry.list_modules(category)
        return {"modules": modules, "count": len(modules)}

    def search_modules(self, query: str) -> dict[str, Any]:
        """
        Search for modules

        Args:
            query: Search query

        Returns:
            Dictionary with matching modules
        """
        results = self.registry.search_modules(query)
        return {"results": results, "count": len(results)}

    def get_module_details(self, name: str) -> dict[str, Any]:
        """
        Get detailed information about a module

        Args:
            name: Module name

        Returns:
            Module details
        """
        module = self.registry.get_module(name)
        if not module:
            return {"error": "Module not found"}

        details = module.to_dict()
        details["installed"] = self.registry.is_installed(name)
        return details

    def install_module(self, name: str) -> dict[str, Any]:
        """
        Install a module

        Args:
            name: Module name

        Returns:
            Installation result
        """
        success = self.registry.install_module(name)
        if not success:
            return {"error": "Module not found"}

        return {"module": name, "status": "installed"}

    def uninstall_module(self, name: str) -> dict[str, Any]:
        """
        Uninstall a module

        Args:
            name: Module name

        Returns:
            Uninstallation result
        """
        success = self.registry.uninstall_module(name)
        if not success:
            return {"error": "Module not installed"}

        return {"module": name, "status": "uninstalled"}

    def rate_module(self, name: str, rating: float) -> dict[str, Any]:
        """
        Rate a module

        Args:
            name: Module name
            rating: Rating value (1-5)

        Returns:
            Rating result
        """
        if not 1 <= rating <= 5:
            return {"error": "Rating must be between 1 and 5"}

        success = self.registry.rate_module(name, rating)
        if not success:
            return {"error": "Module not found"}

        module = self.registry.get_module(name)
        return {
            "module": name,
            "new_rating": module.rating,
            "total_ratings": module.ratings_count,
        }
