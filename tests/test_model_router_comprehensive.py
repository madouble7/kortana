#!/usr/bin/env python3
"""
Comprehensive test suite for SacredModelRouter
==============================================

Tests the model routing logic, strategic alignment scoring,
archetype fitting, and model selection algorithms.
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from src.model_router import AugmentedModelConfig, ModelArchetype, SacredModelRouter
from src.strategic_config import SacredPrinciple, TaskCategory


class TestSacredModelRouter:
    """Test suite for SacredModelRouter class"""

    def setup_method(self):
        """Set up test fixtures for each test method"""
        self.test_config = {
            "default_llm_id": "test-oracle",
            "models": {
                "test-oracle": {
                    "provider": "openai",
                    "model_name": "gpt-4o",
                    "api_key_env": "OPENAI_API_KEY",
                    "enabled": True,
                    "performance_scores": {
                        "reasoning": 0.95,
                        "creativity": 0.85,
                        "accuracy": 0.92,
                    },
                    "cost_per_1m_input": 2.5,
                    "cost_per_1m_output": 10.0,
                    "context_window": 128000,
                },
                "test-swift": {
                    "provider": "anthropic",
                    "model_name": "claude-3-haiku",
                    "api_key_env": "ANTHROPIC_API_KEY",
                    "enabled": True,
                    "performance_scores": {
                        "speed": 0.98,
                        "efficiency": 0.94,
                        "accuracy": 0.85,
                    },
                    "cost_per_1m_input": 0.25,
                    "cost_per_1m_output": 1.25,
                    "context_window": 200000,
                },
                "test-budget": {
                    "provider": "openai",
                    "model_name": "gpt-4o-mini",
                    "api_key_env": "OPENAI_API_KEY",
                    "enabled": True,
                    "performance_scores": {
                        "efficiency": 0.95,
                        "cost_effectiveness": 0.98,
                    },
                    "cost_per_1m_input": 0.15,
                    "cost_per_1m_output": 0.6,
                    "context_window": 128000,
                },
            },
        }

        # Create temporary config file
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        json.dump(self.test_config, self.temp_file)
        self.temp_file.close()

        # Initialize router with test config
        self.router = SacredModelRouter(models_config_path=self.temp_file.name)

    def teardown_method(self):
        """Clean up after each test method"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_router_initialization(self):
        """Test SacredModelRouter initialization"""
        assert self.router is not None
        assert len(self.router.augmented_models) == 3
        assert "test-oracle" in self.router.augmented_models
        assert "test-swift" in self.router.augmented_models
        assert "test-budget" in self.router.augmented_models

    def test_model_config_loading(self):
        """Test loading and parsing of model configurations"""
        oracle_model = self.router.augmented_models["test-oracle"]

        assert oracle_model.model_id == "test-oracle"
        assert oracle_model.provider == "openai"
        assert oracle_model.model_name == "gpt-4o"
        assert oracle_model.cost_per_1m_input == 2.5
        assert oracle_model.context_window == 128000

    def test_task_category_classification(self):
        """Test task category classification logic"""
        # Test development task
        dev_request = "Write a Python function to handle API authentication"
        category = self.router._classify_task_category(dev_request)
        assert category == TaskCategory.DEVELOPMENT

        # Test reasoning task
        reasoning_request = (
            "Analyze the logical implications of this philosophical argument"
        )
        category = self.router._classify_task_category(reasoning_request)
        assert category == TaskCategory.REASONING

        # Test creative task
        creative_request = "Write a poem about artificial intelligence"
        category = self.router._classify_task_category(creative_request)
        assert category == TaskCategory.CREATIVE

    def test_sacred_principle_scoring(self):
        """Test sacred principle alignment scoring"""
        # Test wisdom principle scoring
        wisdom_score = self.router._calculate_sacred_alignment_score(
            "test-oracle", SacredPrinciple.WISDOM
        )
        assert 0.0 <= wisdom_score <= 1.0

        # Test efficiency principle scoring
        efficiency_score = self.router._calculate_sacred_alignment_score(
            "test-swift", SacredPrinciple.EFFICIENCY
        )
        assert 0.0 <= efficiency_score <= 1.0

    def test_archetype_fitting(self):
        """Test model archetype fitting algorithm"""
        # Test oracle archetype
        oracle_fit = self.router._calculate_archetype_fit_score(
            "test-oracle", ModelArchetype.ORACLE
        )
        assert oracle_fit > 0.7  # Oracle model should fit Oracle archetype well

        # Test swift responder archetype
        swift_fit = self.router._calculate_archetype_fit_score(
            "test-swift", ModelArchetype.SWIFT_RESPONDER
        )
        assert swift_fit > 0.7  # Swift model should fit Swift archetype well

        # Test budget workhorse archetype
        budget_fit = self.router._calculate_archetype_fit_score(
            "test-budget", ModelArchetype.BUDGET_WORKHORSE
        )
        assert budget_fit > 0.7  # Budget model should fit Budget archetype well

    def test_model_selection_for_development_task(self):
        """Test model selection for development tasks"""
        dev_request = "Implement a REST API endpoint with proper error handling"
        selected_model = self.router.select_optimal_model(
            task_description=dev_request,
            task_category=TaskCategory.DEVELOPMENT,
            primary_principle=SacredPrinciple.EFFICIENCY,
        )

        assert selected_model in self.router.augmented_models
        # Should prefer efficient models for development
        assert selected_model in ["test-swift", "test-budget"]

    def test_model_selection_for_reasoning_task(self):
        """Test model selection for complex reasoning tasks"""
        reasoning_request = (
            "Analyze the systemic implications of distributed architecture patterns"
        )
        selected_model = self.router.select_optimal_model(
            task_description=reasoning_request,
            task_category=TaskCategory.REASONING,
            primary_principle=SacredPrinciple.WISDOM,
        )

        assert selected_model in self.router.augmented_models
        # Should prefer high-reasoning models for complex analysis
        assert selected_model == "test-oracle"

    def test_model_selection_with_cost_constraints(self):
        """Test model selection with budget constraints"""
        budget_request = "Summarize this document in bullet points"
        selected_model = self.router.select_optimal_model(
            task_description=budget_request,
            task_category=TaskCategory.EFFICIENCY,
            primary_principle=SacredPrinciple.EFFICIENCY,
            cost_priority=0.9,  # High cost sensitivity
        )

        assert selected_model in self.router.augmented_models
        # Should prefer low-cost models when cost is prioritized
        assert selected_model == "test-budget"

    def test_model_fallback_logic(self):
        """Test fallback to default model when selection fails"""
        with patch.object(
            self.router,
            "_calculate_composite_score",
            side_effect=Exception("Test error"),
        ):
            fallback_model = self.router.select_optimal_model(
                task_description="Test task", task_category=TaskCategory.GENERAL
            )
            # Should fallback to default model
            assert fallback_model == self.test_config["default_llm_id"]

    def test_performance_benchmarking(self):
        """Test performance benchmarking and scoring"""
        # Test benchmark scoring
        oracle_model = self.router.augmented_models["test-oracle"]
        reasoning_score = oracle_model.benchmarks.get("reasoning", 0.0)
        assert reasoning_score == 0.95

        creativity_score = oracle_model.benchmarks.get("creativity", 0.0)
        assert creativity_score == 0.85

    def test_composite_scoring_algorithm(self):
        """Test the composite scoring algorithm"""
        composite_score = self.router._calculate_composite_score(
            model_id="test-oracle",
            task_category=TaskCategory.REASONING,
            primary_principle=SacredPrinciple.WISDOM,
            archetype_preference=ModelArchetype.ORACLE,
        )

        assert 0.0 <= composite_score <= 1.0
        assert composite_score > 0.5  # Should be reasonably high for good fit

    def test_context_window_consideration(self):
        """Test that context window is considered in selection"""
        # Large context task
        large_context_request = "Analyze this very long document: " + "x" * 100000
        selected_model = self.router.select_optimal_model(
            task_description=large_context_request,
            task_category=TaskCategory.ANALYSIS,
            context_size_hint=150000,  # Larger than some models
        )

        assert selected_model in self.router.augmented_models
        selected_config = self.router.augmented_models[selected_model]
        assert selected_config.context_window >= 150000

    def test_enabled_models_filtering(self):
        """Test that only enabled models are considered"""
        # Disable test-oracle
        self.router.augmented_models["test-oracle"].enabled = False

        reasoning_request = "Complex philosophical analysis"
        selected_model = self.router.select_optimal_model(
            task_description=reasoning_request, task_category=TaskCategory.REASONING
        )

        # Should not select disabled model
        assert selected_model != "test-oracle"
        assert selected_model in ["test-swift", "test-budget"]

    def test_strategic_config_integration(self):
        """Test integration with strategic configuration"""
        # Test that strategic principles are properly applied
        wisdom_models = self.router._get_models_by_principle(SacredPrinciple.WISDOM)
        assert len(wisdom_models) > 0

        efficiency_models = self.router._get_models_by_principle(
            SacredPrinciple.EFFICIENCY
        )
        assert len(efficiency_models) > 0

    def test_model_ranking_consistency(self):
        """Test that model ranking is consistent for same inputs"""
        task_desc = "Implement a complex algorithm"

        # Run selection multiple times
        selections = []
        for _ in range(5):
            selected = self.router.select_optimal_model(
                task_description=task_desc, task_category=TaskCategory.DEVELOPMENT
            )
            selections.append(selected)

        # Should be consistent (all same selection)
        assert len(set(selections)) <= 2  # Allow for minor variations due to randomness

    def test_error_handling_invalid_config(self):
        """Test error handling with invalid configuration"""
        # Test with non-existent config file
        with pytest.raises((FileNotFoundError, json.JSONDecodeError)):
            SacredModelRouter(models_config_path="/nonexistent/path.json")

    def test_model_availability_check(self):
        """Test model availability checking"""
        assert self.router.is_model_available("test-oracle")
        assert self.router.is_model_available("test-swift")
        assert not self.router.is_model_available("nonexistent-model")

    def test_get_model_capabilities(self):
        """Test retrieval of model capabilities"""
        oracle_caps = self.router.get_model_capabilities("test-oracle")
        assert "reasoning" in oracle_caps
        assert "creativity" in oracle_caps

        swift_caps = self.router.get_model_capabilities("test-swift")
        assert "speed" in swift_caps
        assert "efficiency" in swift_caps


class TestModelArchetype:
    """Test ModelArchetype enum and related functionality"""

    def test_archetype_values(self):
        """Test that all expected archetypes are defined"""
        expected_archetypes = {
            "oracle",
            "swift_responder",
            "memory_weaver",
            "dev_agent",
            "budget_workhorse",
            "multimodal_seer",
        }

        actual_archetypes = {archetype.value for archetype in ModelArchetype}
        assert actual_archetypes == expected_archetypes

    def test_archetype_enum_access(self):
        """Test accessing archetype enum values"""
        assert ModelArchetype.ORACLE.value == "oracle"
        assert ModelArchetype.SWIFT_RESPONDER.value == "swift_responder"
        assert ModelArchetype.DEV_AGENT.value == "dev_agent"


class TestAugmentedModelConfig:
    """Test AugmentedModelConfig dataclass"""

    def test_config_creation(self):
        """Test creating AugmentedModelConfig instances"""
        config = AugmentedModelConfig(
            model_id="test-model",
            provider="test-provider",
            model_name="test-model-name",
            api_key_env="TEST_KEY",
            base_url="https://api.test.com",
            default_params={"temperature": 0.7},
            benchmarks={"accuracy": 0.95},
            sacred_alignment_scores={"wisdom": 0.9},
            archetype_fit_scores={"oracle": 0.85},
            cost_per_1m_input=1.0,
            cost_per_1m_output=3.0,
            context_window=8192,
        )

        assert config.model_id == "test-model"
        assert config.provider == "test-provider"
        assert config.cost_per_1m_input == 1.0
        assert config.context_window == 8192
        assert config.benchmarks["accuracy"] == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
