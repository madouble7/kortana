# Integration Guide: Autonomous Testing Framework

This guide explains how to integrate the new Autonomous Testing Framework with the existing Kor'tana codebase.

## Overview

The Autonomous Testing Framework has been designed to work alongside the existing autonomous development capabilities in Kor'tana, including:
- Existing `AutonomousDevelopmentEngine` in `src/kortana/core/autonomous_development_engine.py`
- Existing agent system in `src/kortana/agents/`
- Existing testing infrastructure

## Integration Points

### 1. With Brain Module

The framework can be integrated with the main brain module to enable continuous autonomous testing:

```python
# In src/kortana/core/brain.py or main initialization
from kortana.core.autonomous_testing_framework import AutonomousTestingFramework

class Brain:
    def __init__(self):
        # Existing initialization
        self.autonomous_framework = AutonomousTestingFramework()
        
    async def start(self):
        # Existing startup code
        await self.autonomous_framework.start()
        
    async def run_autonomous_cycle(self):
        # Run the autonomous testing cycle
        results = await self.autonomous_framework.run_cycle()
        return results
```

### 2. With Existing Agents

The framework complements the existing agents:

```python
# Integration with existing CodingAgent, TestingAgent, etc.
from kortana.agents.autonomous_agents import CodingAgent, TestingAgent
from kortana.core.autonomous_testing_framework import AutonomousTestingFramework

class EnhancedAutonomousSystem:
    def __init__(self):
        # Existing agents
        self.coding_agent = CodingAgent(...)
        self.testing_agent = TestingAgent()
        
        # New framework
        self.testing_framework = AutonomousTestingFramework()
        
    async def develop_and_test(self, task):
        # Use coding agent to develop
        code = await self.coding_agent.generate_code(task)
        
        # Use framework to test
        test = await self.testing_framework.self_testing.generate_test(
            task['target_function'],
            'unit'
        )
        result = await self.testing_framework.self_testing.execute_test(test.test_id)
        
        return {'code': code, 'test_result': result}
```

### 3. With Scheduler

Integrate with the existing scheduler for periodic autonomous cycles:

```python
# In src/kortana/core/scheduler.py or similar
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from kortana.core.autonomous_testing_framework import AutonomousTestingFramework

scheduler = AsyncIOScheduler()
framework = AutonomousTestingFramework()

async def run_autonomous_cycle():
    await framework.start()
    results = await framework.run_cycle()
    logger.info(f"Autonomous cycle completed: {results}")

# Schedule to run every hour
scheduler.add_job(run_autonomous_cycle, 'interval', hours=1)
```

### 4. With API Endpoints

Add API endpoints to expose framework functionality:

```python
# In src/kortana/api/ or main.py
from fastapi import APIRouter
from kortana.core.autonomous_testing_framework import AutonomousTestingFramework

router = APIRouter()
framework = AutonomousTestingFramework()

@router.post("/autonomous/start")
async def start_framework():
    await framework.start()
    return {"status": "started"}

@router.post("/autonomous/cycle")
async def run_cycle():
    results = await framework.run_cycle()
    return results

@router.get("/autonomous/status")
async def get_status():
    status = await framework.get_status()
    return status

@router.post("/autonomous/stop")
async def stop_framework():
    await framework.stop()
    return {"status": "stopped"}
```

### 5. With Configuration System

Integrate with existing configuration:

```python
# In src/kortana/config.py or similar
from kortana.core.autonomous_testing_config import FrameworkConfig

class KortanaConfig:
    def __init__(self):
        # Existing config
        self.llm_settings = ...
        
        # Add framework config
        self.autonomous_framework = FrameworkConfig(
            cycle_interval_minutes=60,
            self_testing=SelfTestingConfig(
                enabled=True,
                auto_generate_tests=True
            ),
            debugging=DebugConfig(
                enabled=True,
                auto_fix_enabled=False  # Keep disabled for safety
            )
        )
```

### 6. With Memory System

Integrate with the memory system to track autonomous activities:

```python
# Integration with memory
from kortana.core.autonomous_testing_framework import AutonomousTestingFramework

async def run_with_memory(memory_manager):
    framework = AutonomousTestingFramework()
    await framework.start()
    
    # Run cycle
    results = await framework.run_cycle()
    
    # Store in memory
    await memory_manager.store_memory({
        'type': 'autonomous_cycle',
        'timestamp': results['timestamp'],
        'cycle_number': results['cycle_number'],
        'results': results['modules']
    })
    
    return results
```

## Configuration

### YAML Configuration Example

Create a configuration file for the framework:

```yaml
# config/autonomous_framework.yaml
enabled: true
cycle_interval_minutes: 60
log_level: INFO

self_testing:
  enabled: true
  auto_generate_tests: true
  max_concurrent_tests: 5

debugging:
  enabled: true
  auto_fix_enabled: false
  max_severity_auto_fix: medium

feature_expansion:
  enabled: true
  auto_implement: false

performance:
  enabled: true
  default_thresholds:
    response_time_ms: 1000.0
    memory_usage_mb: 500.0

ethical_compliance:
  enabled: true
  minimum_compliance_score: 0.8
```

Load in code:

```python
import yaml
from kortana.core.autonomous_testing_config import FrameworkConfig

with open('config/autonomous_framework.yaml') as f:
    config_dict = yaml.safe_load(f)
    config = FrameworkConfig.from_dict(config_dict)
```

## Startup Integration

### Option 1: Standalone Service

Run as a separate background service:

```python
# scripts/run_autonomous_framework.py
import asyncio
from kortana.core.autonomous_testing_framework import AutonomousTestingFramework

async def main():
    framework = AutonomousTestingFramework()
    await framework.start()
    
    # Run continuously
    while True:
        await framework.run_cycle()
        await asyncio.sleep(3600)  # Wait 1 hour

if __name__ == "__main__":
    asyncio.run(main())
```

### Option 2: Integrated with Main Application

```python
# In main application startup
from kortana.core.autonomous_testing_framework import AutonomousTestingFramework

class KortanaApp:
    def __init__(self):
        self.framework = AutonomousTestingFramework()
        
    async def startup(self):
        # Start framework
        await self.framework.start()
        
        # Schedule periodic cycles
        asyncio.create_task(self._run_cycles())
        
    async def _run_cycles(self):
        while True:
            try:
                await self.framework.run_cycle()
            except Exception as e:
                logger.error(f"Cycle error: {e}")
            await asyncio.sleep(3600)
```

## Monitoring Integration

### Logging Integration

The framework uses Python's logging module. Configure it with your existing logging:

```python
import logging

# Configure for framework
logging.getLogger('kortana.core.autonomous_testing_framework').setLevel(logging.INFO)
logging.getLogger('SelfTesting').setLevel(logging.DEBUG)
logging.getLogger('AutonomousDebugging').setLevel(logging.INFO)
```

### Metrics Integration

Integrate framework metrics with existing monitoring:

```python
async def collect_metrics():
    status = await framework.get_status()
    
    # Send to your monitoring system
    metrics = {
        'autonomous_cycles': status['cycles_completed'],
        'tests_executed': status['modules']['self_testing']['test_history'],
        'issues_found': status['modules']['debugging']['active_issues'],
        'compliance_score': status['modules']['ethical_compliance']['audits_performed']
    }
    
    # Send to Prometheus, CloudWatch, etc.
    send_metrics(metrics)
```

## Safety Recommendations

1. **Start with Auto-Fix Disabled**: Keep `auto_fix_enabled=False` until confident
2. **Review Logs Regularly**: Monitor autonomous actions
3. **Set Conservative Thresholds**: Start with lenient thresholds, adjust based on experience
4. **Require Approval**: Keep `auto_implement=False` for feature expansion
5. **Monitor Compliance**: Track ethical compliance scores

## Testing Integration

The framework works with existing test infrastructure:

```python
# tests/test_integration.py
import pytest
from kortana.core.autonomous_testing_framework import AutonomousTestingFramework

@pytest.fixture
async def framework():
    fw = AutonomousTestingFramework()
    await fw.start()
    yield fw
    await fw.stop()

@pytest.mark.asyncio
async def test_framework_integration(framework):
    # Test integration with existing systems
    results = await framework.run_cycle()
    assert results['cycle_number'] > 0
```

## Troubleshooting

### Issue: Import Errors
**Solution**: Ensure PYTHONPATH includes src directory:
```bash
export PYTHONPATH=/path/to/kortana/src:$PYTHONPATH
```

### Issue: Configuration Not Loading
**Solution**: Verify configuration file path and format:
```python
import yaml
with open('config/autonomous_framework.yaml') as f:
    config = yaml.safe_load(f)
    print(config)  # Verify structure
```

### Issue: Framework Not Running Cycles
**Solution**: Check that framework is started:
```python
status = await framework.get_status()
print(f"Active: {status['active']}")
```

## Next Steps

1. Review the full documentation in `docs/AUTONOMOUS_TESTING_FRAMEWORK.md`
2. Run the demo: `python examples/autonomous_testing_demo.py`
3. Integrate one module at a time
4. Monitor and adjust configuration based on results
5. Gradually enable more autonomous features as confidence grows

## Support

For questions or issues:
1. Check the documentation: `docs/AUTONOMOUS_TESTING_FRAMEWORK.md`
2. Review the implementation summary: `AUTONOMOUS_FRAMEWORK_SUMMARY.md`
3. Run the demo to see working examples
4. Check test cases for usage patterns
