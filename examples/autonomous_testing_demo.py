"""
Sample usage of Kor'tana's Autonomous Testing Framework

This script demonstrates how to use the autonomous testing framework
and its various modules.
"""

import asyncio
import logging

from src.kortana.core.autonomous_testing_framework import (
    AutonomousTestingFramework
)
from src.kortana.core.autonomous_testing_config import (
    FrameworkConfig
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def demonstrate_self_testing():
    """Demonstrate self-testing capabilities"""
    logger.info("=== Demonstrating Self-Testing Module ===")
    
    framework = AutonomousTestingFramework()
    await framework.start()
    
    # Generate a test
    test = await framework.self_testing.generate_test("example_function", "unit")
    logger.info(f"Generated test: {test.name}")
    
    # Execute the test
    result = await framework.self_testing.execute_test(test.test_id)
    logger.info(f"Test result: {result['success']}")
    
    # Analyze results
    analysis = await framework.self_testing.analyze_test_results(test.test_id)
    logger.info(f"Test analysis: {analysis}")
    
    await framework.stop()


async def demonstrate_debugging():
    """Demonstrate autonomous debugging capabilities"""
    logger.info("=== Demonstrating Autonomous Debugging Module ===")
    
    framework = AutonomousTestingFramework()
    await framework.start()
    
    # Scan for issues
    issues = await framework.debugging.scan_for_issues()
    logger.info(f"Found {len(issues)} issues")
    
    if issues:
        issue = issues[0]
        logger.info(f"Issue: {issue.description}")
        
        # Analyze the issue
        analysis = await framework.debugging.analyze_issue(issue.issue_id)
        logger.info(f"Analysis: {analysis}")
    
    await framework.stop()


async def demonstrate_feature_expansion():
    """Demonstrate feature self-expansion capabilities"""
    logger.info("=== Demonstrating Feature Self-Expansion Module ===")
    
    framework = AutonomousTestingFramework()
    await framework.start()
    
    # Set guidelines
    guidelines = {
        "focus_areas": ["performance", "code_quality"],
        "min_test_coverage": 0.8
    }
    framework.feature_expansion.set_guidelines(guidelines)
    
    # Analyze codebase
    opportunities = await framework.feature_expansion.analyze_codebase()
    logger.info(f"Found {len(opportunities)} improvement opportunities")
    
    # Generate a suggestion
    if opportunities:
        suggestion = await framework.feature_expansion.suggest_improvement(opportunities[0])
        logger.info(f"Suggestion: {suggestion.title}")
        logger.info(f"Description: {suggestion.description}")
    
    await framework.stop()


async def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring capabilities"""
    logger.info("=== Demonstrating Performance Monitoring Module ===")
    
    framework = AutonomousTestingFramework()
    await framework.start()
    
    # Set thresholds
    framework.performance_monitoring.set_threshold("response_time", 100.0)
    framework.performance_monitoring.set_threshold("memory_usage", 500.0)
    
    # Record some metrics
    await framework.performance_monitoring.record_metric("response_time", 75.0, "ms")
    await framework.performance_monitoring.record_metric("response_time", 85.0, "ms")
    await framework.performance_monitoring.record_metric("memory_usage", 450.0, "MB")
    
    # Analyze trends
    analysis = await framework.performance_monitoring.analyze_trends("response_time")
    logger.info(f"Performance analysis: {analysis}")
    
    # Get optimization suggestions
    optimizations = await framework.performance_monitoring.suggest_optimizations()
    logger.info(f"Optimization suggestions: {len(optimizations)}")
    
    await framework.stop()


async def demonstrate_ethical_compliance():
    """Demonstrate ethical compliance self-audit"""
    logger.info("=== Demonstrating Ethical Compliance Module ===")
    
    framework = AutonomousTestingFramework()
    await framework.start()
    
    # Audit a proposed action
    action_result = await framework.ethical_compliance.audit_action(
        "modify_code",
        {"logged": True, "user_approved": True}
    )
    logger.info(f"Action audit: Compliant={action_result['compliant']}")
    
    # Perform a self-audit
    audit = await framework.ethical_compliance.perform_self_audit()
    logger.info(f"Self-audit completed. Compliance score: {audit.compliance_score}")
    logger.info(f"Guidelines checked: {len(audit.guidelines_checked)}")
    logger.info(f"Violations: {len(audit.violations)}")
    
    await framework.stop()


async def demonstrate_full_cycle():
    """Demonstrate a complete autonomous cycle"""
    logger.info("=== Demonstrating Complete Autonomous Cycle ===")
    
    framework = AutonomousTestingFramework()
    await framework.start()
    
    # Run one complete cycle
    results = await framework.run_cycle()
    logger.info(f"Cycle #{results['cycle_number']} completed")
    logger.info(f"Timestamp: {results['timestamp']}")
    
    # Display module results
    for module_name, module_results in results['modules'].items():
        logger.info(f"{module_name}: {module_results}")
    
    # Get framework status
    status = await framework.get_status()
    logger.info(f"Framework status: Active={status['active']}, Cycles={status['cycles_completed']}")
    
    await framework.stop()


async def demonstrate_with_custom_config():
    """Demonstrate framework with custom configuration"""
    logger.info("=== Demonstrating Custom Configuration ===")
    
    # Create custom configuration
    config_dict = {
        "enabled": True,
        "cycle_interval_minutes": 30,
        "self_testing": {
            "enabled": True,
            "auto_generate_tests": True,
            "max_concurrent_tests": 3
        },
        "debugging": {
            "enabled": True,
            "auto_fix_enabled": False,
            "max_severity_auto_fix": "low"
        },
        "performance": {
            "enabled": True,
            "default_thresholds": {
                "response_time_ms": 500.0,
                "memory_usage_mb": 1000.0
            }
        }
    }
    
    config = FrameworkConfig.from_dict(config_dict)
    logger.info(f"Custom config created: cycle_interval={config.cycle_interval_minutes} minutes")
    logger.info(f"Auto-fix enabled: {config.debugging.auto_fix_enabled}")
    logger.info(f"Max concurrent tests: {config.self_testing.max_concurrent_tests}")


async def main():
    """Run all demonstrations"""
    logger.info("Starting Autonomous Testing Framework Demonstrations\n")
    
    try:
        # Run individual demonstrations
        await demonstrate_self_testing()
        print("\n")
        
        await demonstrate_debugging()
        print("\n")
        
        await demonstrate_feature_expansion()
        print("\n")
        
        await demonstrate_performance_monitoring()
        print("\n")
        
        await demonstrate_ethical_compliance()
        print("\n")
        
        await demonstrate_full_cycle()
        print("\n")
        
        await demonstrate_with_custom_config()
        print("\n")
        
        logger.info("All demonstrations completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during demonstration: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
