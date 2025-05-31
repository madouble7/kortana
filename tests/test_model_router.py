"""
Comprehensive test suite for model_router.py - Sacred Model Selection System
"""

import json
import os
import sys
from unittest.mock import Mock, mock_open, patch

import pytest


def test_model_router_module_structure():
    """Test that model_router.py has expected structure and classes"""
    router_path = os.path.join(
        os.path.dirname(__file__), "..", "src", "model_router.py"
    )
    assert os.path.exists(router_path), "model_router.py file should exist"

    # Read and check for key components
    with open(router_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert (
        "class SacredModelRouter" in content
    ), "SacredModelRouter class should be defined"
    assert "class ModelArchetype" in content, "ModelArchetype enum should be defined"
    assert (
        "class AugmentedModelConfig" in content
    ), "AugmentedModelConfig dataclass should be defined"
    assert (
        "def select_model_with_sacred_guidance" in content
    ), "select_model_with_sacred_guidance method should exist"
    assert "def get_model_config" in content, "get_model_config method should exist"
    assert "def get_routing_stats" in content, "get_routing_stats method should exist"


def test_sacred_model_router_import():
    """Test that SacredModelRouter can be imported without errors"""
    try:
        # Add src to path temporarily
        src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        from model_router import AugmentedModelConfig, ModelArchetype, SacredModelRouter

        # Verify classes are importable
        assert SacredModelRouter is not None
        assert ModelArchetype is not None
        assert AugmentedModelConfig is not None

    except ImportError as e:
        pytest.fail(f"Cannot import from model_router: {e}")


def test_model_archetype_enum():
    """Test that ModelArchetype enum has expected values"""
    try:
        import sys

        src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        from model_router import ModelArchetype

        # Check for expected archetype values
        assert hasattr(ModelArchetype, "ORACLE")
        assert hasattr(ModelArchetype, "SWIFT_RESPONDER")
        assert hasattr(ModelArchetype, "MEMORY_WEAVER")
        assert hasattr(ModelArchetype, "DEV_AGENT")
        assert hasattr(ModelArchetype, "BUDGET_WORKHORSE")
        assert hasattr(ModelArchetype, "MULTIMODAL_SEER")

    except ImportError as e:
        pytest.fail(f"Cannot import ModelArchetype: {e}")


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data='{"models": {}, "default_llm_id": null}',
)
@patch("os.path.exists")
def test_sacred_model_router_initialization(mock_exists, mock_file):
    """Test SacredModelRouter initialization with mocked config"""
    mock_exists.return_value = True

    try:
        import sys

        src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        with patch("model_router.UltimateLivingSacredConfig") as mock_config:
            mock_config.return_value = Mock()
            from model_router import SacredModelRouter

            router = SacredModelRouter()

            # Verify initialization
            assert router is not None
            assert hasattr(router, "loaded_models_config")
            assert hasattr(router, "sacred_config")
            assert hasattr(router, "routing_history")
            assert hasattr(router, "category_to_archetype_map")

    except Exception as e:
        pytest.fail(f"SacredModelRouter initialization failed: {e}")


def test_get_model_config_method():
    """Test get_model_config method with mock data"""
    mock_config_data = {
        "models": {
            "test-model": {
                "provider": "test-provider",
                "model_name": "Test Model",
                "enabled": True,
            }
        },
        "default_llm_id": "test-model",
    }

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_config_data))):
        with patch("os.path.exists", return_value=True):
            with patch("model_router.UltimateLivingSacredConfig") as mock_config:
                mock_config.return_value = Mock()

                try:
                    import sys

                    src_path = os.path.abspath(
                        os.path.join(os.path.dirname(__file__), "..", "src")
                    )
                    if src_path not in sys.path:
                        sys.path.insert(0, src_path)

                    from model_router import SacredModelRouter

                    router = SacredModelRouter()

                    # Test getting existing model config
                    config = router.get_model_config("test-model")
                    assert config is not None
                    assert config["provider"] == "test-provider"
                    assert config["model_name"] == "Test Model"

                    # Test getting non-existent model config
                    config = router.get_model_config("non-existent")
                    assert config is None

                except Exception as e:
                    pytest.fail(f"get_model_config test failed: {e}")


def test_routing_stats_method():
    """Test get_routing_stats method"""
    with patch(
        "builtins.open", mock_open(read_data='{"models": {}, "default_llm_id": null}')
    ):
        with patch("os.path.exists", return_value=True):
            with patch("model_router.UltimateLivingSacredConfig") as mock_config:
                mock_config.return_value = Mock()

                try:
                    import sys

                    src_path = os.path.abspath(
                        os.path.join(os.path.dirname(__file__), "..", "src")
                    )
                    if src_path not in sys.path:
                        sys.path.insert(0, src_path)

                    from model_router import SacredModelRouter

                    router = SacredModelRouter()

                    # Test routing stats
                    stats = router.get_routing_stats()
                    assert isinstance(stats, dict)
                    assert "history_count" in stats
                    assert stats["history_count"] == 0  # Initially empty

                except Exception as e:
                    pytest.fail(f"get_routing_stats test failed: {e}")


def test_strategic_config_integration():
    """Test that model router properly integrates with strategic config"""
    with patch(
        "builtins.open", mock_open(read_data='{"models": {}, "default_llm_id": null}')
    ):
        with patch("os.path.exists", return_value=True):
            with patch("model_router.UltimateLivingSacredConfig") as mock_config:
                # Mock strategic config methods
                mock_instance = Mock()
                mock_instance.get_task_guidance.return_value = {
                    "prioritize_principles": ["wisdom"]
                }
                mock_instance.get_model_sacred_scores.return_value = {
                    "wisdom": 0.8,
                    "compassion": 0.6,
                }
                mock_instance.get_model_archetype_fits.return_value = {"oracle": 0.9}
                mock_config.return_value = mock_instance

                try:
                    import sys

                    src_path = os.path.abspath(
                        os.path.join(os.path.dirname(__file__), "..", "src")
                    )
                    if src_path not in sys.path:
                        sys.path.insert(0, src_path)

                    from model_router import SacredModelRouter

                    router = SacredModelRouter()

                    # Verify strategic config integration
                    assert router.sacred_config is not None

                    # Test sacred alignment method
                    sacred_scores = router.get_model_sacred_alignment("test-model")
                    assert isinstance(sacred_scores, dict)
                    assert "wisdom" in sacred_scores
                    assert "compassion" in sacred_scores

                except Exception as e:
                    pytest.fail(f"Strategic config integration test failed: {e}")


def test_task_category_mapping():
    """Test that task categories are properly mapped to archetypes"""
    with patch(
        "builtins.open", mock_open(read_data='{"models": {}, "default_llm_id": null}')
    ):
        with patch("os.path.exists", return_value=True):
            with patch("model_router.UltimateLivingSacredConfig") as mock_config:
                mock_config.return_value = Mock()

                try:
                    import sys

                    src_path = os.path.abspath(
                        os.path.join(os.path.dirname(__file__), "..", "src")
                    )
                    if src_path not in sys.path:
                        sys.path.insert(0, src_path)

                    from model_router import SacredModelRouter
                    from strategic_config import TaskCategory

                    router = SacredModelRouter()

                    # Verify category to archetype mapping exists
                    assert hasattr(router, "category_to_archetype_map")
                    assert isinstance(router.category_to_archetype_map, dict)

                    # Check that key task categories are mapped
                    assert (
                        TaskCategory.CREATIVE_WRITING
                        in router.category_to_archetype_map
                    )
                    assert (
                        TaskCategory.CODE_GENERATION in router.category_to_archetype_map
                    )
                    assert TaskCategory.RESEARCH in router.category_to_archetype_map

                except Exception as e:
                    pytest.fail(f"Task category mapping test failed: {e}")


def test_config_file_loading_error_handling():
    """Test that router handles config file loading errors gracefully"""
    # Test missing file
    with patch("os.path.exists", return_value=False):
        with patch("model_router.UltimateLivingSacredConfig") as mock_config:
            mock_config.return_value = Mock()

            try:
                import sys

                src_path = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "src")
                )
                if src_path not in sys.path:
                    sys.path.insert(0, src_path)

                from model_router import SacredModelRouter

                router = SacredModelRouter()

                # Should initialize with empty config
                assert router.loaded_models_config is not None
                assert "models" in router.loaded_models_config

            except Exception as e:
                pytest.fail(f"Missing config file handling failed: {e}")

    # Test JSON decode error
    with patch("builtins.open", mock_open(read_data="invalid json")):
        with patch("os.path.exists", return_value=True):
            with patch("model_router.UltimateLivingSacredConfig") as mock_config:
                mock_config.return_value = Mock()

                try:
                    import sys

                    src_path = os.path.abspath(
                        os.path.join(os.path.dirname(__file__), "..", "src")
                    )
                    if src_path not in sys.path:
                        sys.path.insert(0, src_path)

                    from model_router import SacredModelRouter

                    router = SacredModelRouter()

                    # Should initialize with default empty config
                    assert router.loaded_models_config is not None

                except Exception as e:
                    pytest.fail(f"JSON decode error handling failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
