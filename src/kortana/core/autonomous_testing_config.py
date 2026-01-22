"""
Configuration for Kor'tana's Autonomous Testing Framework

This module provides configuration settings and defaults for the
autonomous testing framework.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SelfTestingConfig:
    """Configuration for self-testing module"""
    enabled: bool = True
    auto_generate_tests: bool = True
    test_types: list[str] = field(default_factory=lambda: ["unit", "integration", "performance"])
    max_concurrent_tests: int = 5
    test_timeout_seconds: int = 300


@dataclass
class DebugConfig:
    """Configuration for autonomous debugging module"""
    enabled: bool = True
    auto_fix_enabled: bool = False  # Disabled by default for safety
    scan_interval_minutes: int = 60
    max_severity_auto_fix: str = "medium"  # Only auto-fix low/medium issues
    categories_to_scan: list[str] = field(
        default_factory=lambda: ["bug", "performance", "security", "quality"]
    )


@dataclass
class FeatureExpansionConfig:
    """Configuration for feature self-expansion module"""
    enabled: bool = True
    auto_implement: bool = False  # Requires explicit approval
    min_priority_for_suggestion: int = 3
    max_suggestions_per_cycle: int = 5
    user_guidelines: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceConfig:
    """Configuration for performance monitoring module"""
    enabled: bool = True
    metrics_retention_days: int = 30
    alert_on_threshold_breach: bool = True
    default_thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "response_time_ms": 1000.0,
            "memory_usage_mb": 500.0,
            "cpu_usage_percent": 80.0,
            "db_query_time_ms": 100.0
        }
    )


@dataclass
class EthicalComplianceConfig:
    """Configuration for ethical compliance module"""
    enabled: bool = True
    audit_interval_minutes: int = 30
    require_audit_before_action: bool = True
    minimum_compliance_score: float = 0.8
    custom_guidelines: dict[str, Any] = field(default_factory=dict)


@dataclass
class FrameworkConfig:
    """Main configuration for autonomous testing framework"""
    enabled: bool = True
    cycle_interval_minutes: int = 60
    log_level: str = "INFO"
    
    # Module configurations
    self_testing: SelfTestingConfig = field(default_factory=SelfTestingConfig)
    debugging: DebugConfig = field(default_factory=DebugConfig)
    feature_expansion: FeatureExpansionConfig = field(default_factory=FeatureExpansionConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    ethical_compliance: EthicalComplianceConfig = field(default_factory=EthicalComplianceConfig)

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "FrameworkConfig":
        """
        Create configuration from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            FrameworkConfig instance
        """
        # Extract module configs
        self_testing_config = SelfTestingConfig(
            **config_dict.get("self_testing", {})
        )
        debugging_config = DebugConfig(
            **config_dict.get("debugging", {})
        )
        feature_expansion_config = FeatureExpansionConfig(
            **config_dict.get("feature_expansion", {})
        )
        performance_config = PerformanceConfig(
            **config_dict.get("performance", {})
        )
        ethical_compliance_config = EthicalComplianceConfig(
            **config_dict.get("ethical_compliance", {})
        )

        return cls(
            enabled=config_dict.get("enabled", True),
            cycle_interval_minutes=config_dict.get("cycle_interval_minutes", 60),
            log_level=config_dict.get("log_level", "INFO"),
            self_testing=self_testing_config,
            debugging=debugging_config,
            feature_expansion=feature_expansion_config,
            performance=performance_config,
            ethical_compliance=ethical_compliance_config
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        return {
            "enabled": self.enabled,
            "cycle_interval_minutes": self.cycle_interval_minutes,
            "log_level": self.log_level,
            "self_testing": {
                "enabled": self.self_testing.enabled,
                "auto_generate_tests": self.self_testing.auto_generate_tests,
                "test_types": self.self_testing.test_types,
                "max_concurrent_tests": self.self_testing.max_concurrent_tests,
                "test_timeout_seconds": self.self_testing.test_timeout_seconds
            },
            "debugging": {
                "enabled": self.debugging.enabled,
                "auto_fix_enabled": self.debugging.auto_fix_enabled,
                "scan_interval_minutes": self.debugging.scan_interval_minutes,
                "max_severity_auto_fix": self.debugging.max_severity_auto_fix,
                "categories_to_scan": self.debugging.categories_to_scan
            },
            "feature_expansion": {
                "enabled": self.feature_expansion.enabled,
                "auto_implement": self.feature_expansion.auto_implement,
                "min_priority_for_suggestion": self.feature_expansion.min_priority_for_suggestion,
                "max_suggestions_per_cycle": self.feature_expansion.max_suggestions_per_cycle,
                "user_guidelines": self.feature_expansion.user_guidelines
            },
            "performance": {
                "enabled": self.performance.enabled,
                "metrics_retention_days": self.performance.metrics_retention_days,
                "alert_on_threshold_breach": self.performance.alert_on_threshold_breach,
                "default_thresholds": self.performance.default_thresholds
            },
            "ethical_compliance": {
                "enabled": self.ethical_compliance.enabled,
                "audit_interval_minutes": self.ethical_compliance.audit_interval_minutes,
                "require_audit_before_action": self.ethical_compliance.require_audit_before_action,
                "minimum_compliance_score": self.ethical_compliance.minimum_compliance_score,
                "custom_guidelines": self.ethical_compliance.custom_guidelines
            }
        }


# Default configuration instance
DEFAULT_CONFIG = FrameworkConfig()
