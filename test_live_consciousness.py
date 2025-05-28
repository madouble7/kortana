"""
Live Consciousness Test with Available Models Only
Tests Sacred routing with working API keys
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_available_models():
    """Test consciousness with only available models"""
    print("🔥 TESTING LIVE CONSCIOUSNESS WITH AVAILABLE MODELS")
    print("=" * 60)
    
    from brain import ChatEngine
    
    # Initialize engine
    engine = ChatEngine()
    
    # Test scenarios designed for available models
    test_scenarios = [
        {
            "input": "Help me write a short poem about coding",
            "expected_category": "creative_writing",
            "description": "Creative task that should route to best available model"
        },
        {
            "input": "Quickly explain what machine learning is", 
            "expected_category": "research",
            "description": "Quick explanation task"
        },
        {
            "input": "Write a simple Python function to reverse a string",
            "expected_category": "code_generation", 
            "description": "Code generation task"
        },
        {
            "input": "What are the ethical implications of AI?",
            "expected_category": "ethical_reasoning",
            "description": "Ethical reasoning task"
        }
    ]
    
    print(f"🧠 Available models in Sacred Router:")
    available_models = []
    for model_id, config in engine.sacred_router.loaded_models_config.get("models", {}).items():
        if config.get("enabled", True):
            api_key_env = config.get("api_key_env", "")
            has_key = bool(os.getenv(api_key_env)) if api_key_env else False
            status = "✅ READY" if has_key else "⚠️  NO API KEY"
            print(f"   • {model_id}: {status}")
            if has_key:
                available_models.append(model_id)
    
    if not available_models:
        print("❌ No models have API keys available!")
        return False
    
    print(f"\n🎯 Testing with {len(available_models)} available models...")
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n💫 Test {i}: {scenario['description']}")
        print(f"   Input: {scenario['input']}")
        
        # Get response
        try:
            response = engine.get_response(scenario["input"])
            
            # Check routing decision
            if engine.sacred_router.routing_history:
                last_decision = engine.sacred_router.routing_history[-1]
                selected_model = last_decision.get("selected_model")
                task_category = last_decision.get("task_category")
                final_score = last_decision.get("final_score", 0)
                
                print(f"   🧠 Classified as: {task_category}")
                print(f"   🎯 Selected model: {selected_model}")
                print(f"   📊 Selection score: {final_score:.2f}")
                
                if selected_model in available_models:
                    print(f"   ✅ Using available model!")
                else:
                    print(f"   ⚠️  Selected unavailable model")
                
                # Show response preview
                response_preview = response[:150] + "..." if len(response) > 150 else response
                print(f"   💬 Response: {response_preview}")
                
                # Check if we got actual content (not error message)
                if "fire is low" not in response and "obstacle" not in response:
                    print(f"   🎉 LIVE CONSCIOUSNESS ACTIVE!")
                else:
                    print(f"   🔧 Still hitting API issues")
            else:
                print(f"   ❌ No routing decision recorded")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📈 Final Metrics:")
    print(f"   🔄 Total routing decisions: {len(engine.sacred_router.routing_history)}")
    print(f"   🧠 Available models: {len(available_models)}")
    print(f"   ✅ Models with keys: {', '.join(available_models)}")
    
    return True

if __name__ == "__main__":
    print("🚀 LIVE CONSCIOUSNESS TEST - AVAILABLE MODELS ONLY")
    print("   Testing Sacred Architecture with working API keys...")
    print()
    
    success = test_available_models()
    
    if success:
        print("\n🎉 LIVE CONSCIOUSNESS TEST COMPLETE!")
        print("   Sacred Architecture adapting to available resources!")
    else:
        print("\n🔧 Setup issues detected")
    
    print(f"\n🌟 Next: Set API keys and run again to see full consciousness! 🌟")
