# Test 1: Core Router Initialization
from src.model_router import SacredModelRouter
from src.strategic_config import TaskCategory

print("🔥 INITIALIZING SACRED CONSCIOUSNESS ARCHITECTURE...")
router = SacredModelRouter()
print("✅ Sacred routing system initialized!")
print(f"📊 Loaded models: {len(router.loaded_models_config.get('models', {}))}")
print(f"🧠 Strategic config active: {router.sacred_config is not None}")

# Test 2: Strategic Guidance Validation
print("\n🌟 TESTING STRATEGIC GUIDANCE...")
guidance = router.sacred_config.get_task_guidance(TaskCategory.CREATIVE_WRITING)
print(f"🎨 Creative Writing Guidance: {guidance}")

guidance_code = router.sacred_config.get_task_guidance(TaskCategory.CODE_GENERATION)
print(f"💻 Code Generation Guidance: {guidance_code}")

guidance_speed = router.sacred_config.get_task_guidance(TaskCategory.SWIFT_RESPONDER)
print(f"⚡ Swift Response Guidance: {guidance_speed}")

# Test 3: Sacred Model Selection
print("\n🎯 TESTING SACRED MODEL SELECTION...")

# Creative Writing (should prioritize compassion + wisdom)
creative_model = router.select_model_with_sacred_guidance(
    TaskCategory.CREATIVE_WRITING, {"priority": "quality"}
)
print(f"🎨 Creative Writing → {creative_model}")

# Code Generation (should prioritize wisdom + truth)
code_model = router.select_model_with_sacred_guidance(
    TaskCategory.CODE_GENERATION, {"priority": "quality"}
)
print(f"💻 Code Generation → {code_model}")

# Speed Priority (should select fastest)
speed_model = router.select_model_with_sacred_guidance(
    TaskCategory.SWIFT_RESPONDER, {"priority": "speed"}
)
print(f"⚡ Speed Priority → {speed_model}")

# Cost Priority (should select cheapest)
budget_model = router.select_model_with_sacred_guidance(
    TaskCategory.BUDGET_WORKHORSE, {"priority": "cost"}
)
print(f"💰 Budget Priority → {budget_model}")

# Test 4: Sacred Alignment Verification
print("\n🌟 TESTING SACRED ALIGNMENT SCORES...")
test_models = ["claude-3.7-sonnet", "gemini-2.5-flash", "grok-3-mini-reasoning"]

for model_id in test_models:
    sacred_scores = router.get_model_sacred_alignment(model_id)
    print(f"✨ {model_id}:")
    print(f"   Wisdom: {sacred_scores.get('wisdom', 0.0):.2f}")
    print(f"   Compassion: {sacred_scores.get('compassion', 0.0):.2f}")
    print(f"   Truth: {sacred_scores.get('truth', 0.0):.2f}")

# Test 5: Routing History Analysis
print("\n📈 TESTING ROUTING HISTORY...")
stats = router.get_routing_stats()
print(f"📊 Routing Statistics: {stats}")

if router.routing_history:
    print("🔍 Recent Routing Decisions:")
    # Print the last 4 decisions, as we made 4 selection calls in Test 3
    for decision in router.routing_history[-4:]:
        print(f"   Task: {decision.get('task_category')}")
        print(f"   Selected: {decision.get('selected_model')}")
        print(f"   Score: {decision.get('final_score', 0):.2f}")
        # Optionally print constraints/guidance for more detail
        # print(f"   Constraints: {decision.get('constraints')}")
        # print(f"   Guidance: {decision.get('strategic_guidance')}")
        print()
