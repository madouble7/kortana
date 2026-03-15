import sys

sys.path.insert(0, ".")

from src.kortana.core.enhanced_model_router import EnhancedModelRouter, TaskType


class MockSettings:
    def __init__(self):
        pass


print("Testing Enhanced Model Router...")

settings = MockSettings()
print("Settings created")

router = EnhancedModelRouter(settings)
print("Router created")

models = router.get_available_models()
print(f"Available models: {len(models)}")

model_id = router.select_optimal_model(TaskType.REASONING, prefer_free=True)
print(f"Selected reasoning model: {model_id}")

test_input = "Help me solve this math problem"
result = router.route(test_input, {}, prefer_free=True)
print(f"Routing result: {result[0]}, {result[1]}")

print("All tests passed!")
