"""
Kor'tana Model Resolver
Handles model aliases and unified configuration for autonomous repair system
"""

import json
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class ModelResolver:
    """
    Resolves model names and aliases for unified configuration support
    Enables autonomous repair system compatibility
    """
    
    def __init__(self, config_path: str = "config/models_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.aliases = self.config.get("model_aliases", {})
        
    def _load_config(self) -> Dict:
        """Load the unified models configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load model config: {e}")
            return {}
    
    def resolve_model_id(self, model_identifier: str) -> Optional[str]:
        """
        Resolve model identifier to actual model ID
        Handles aliases and direct model IDs
        """
        # Check if it's already a valid model ID
        if model_identifier in self.config.get("models", {}):
            return model_identifier
            
        # Check aliases
        resolved = self.aliases.get(model_identifier)
        if resolved and resolved in self.config.get("models", {}):
            return resolved
            
        # Check routing rules
        routing = self.config.get("model_routing", {})
        for route_type, model_id in routing.items():
            if model_identifier == route_type:
                return model_id
                
        logger.warning(f"Could not resolve model identifier: {model_identifier}")
        return None
    
    def get_model_config(self, model_identifier: str) -> Optional[Dict]:
        """Get model configuration by identifier (supports aliases)"""
        resolved_id = self.resolve_model_id(model_identifier)
        if resolved_id:
            return self.config.get("models", {}).get(resolved_id)
        return None
    
    def get_available_models(self) -> List[str]:
        """Get list of all available model IDs and aliases"""
        models = list(self.config.get("models", {}).keys())
        aliases = list(self.aliases.keys()) 
        routing = list(self.config.get("model_routing", {}).keys())
        return sorted(set(models + aliases + routing))
    
    def verify_autonomous_models(self) -> Dict[str, bool]:
        """
        Verify that all required autonomous repair system models are available
        Returns dict of model_id -> availability
        """
        required_models = [
            "grok-3-mini-reasoning",
            "gemini-2.5-flash", 
            "gpt-4.1-nano"
        ]
        
        verification = {}
        for model_id in required_models:
            config = self.get_model_config(model_id)
            enabled = config is not None and config.get("enabled", False)
            
            # Additional check for XAI models
            if model_id == "grok-3-mini-reasoning" and enabled:
                api_key = config.get("api_key_env")
                if api_key:
                    import os
                    has_key = bool(os.getenv(api_key))
                    verification[model_id] = has_key
                    if not has_key:
                        logger.warning(f"XAI API key not found in environment: {api_key}")
                else:
                    verification[model_id] = False
            else:
                verification[model_id] = enabled
            
        return verification
    
    def test_xai_integration(self) -> bool:
        """Test XAI Grok client integration"""
        try:
            from llm_clients.xai_client import XAIClient
            
            # Test client initialization
            xai_config = self.get_model_config("grok-3-mini-reasoning")
            if not xai_config:
                logger.error("XAI model configuration not found")
                return False
            
            # Create test client
            client = XAIClient(model_name="grok-3-mini")
            
            # Test capabilities
            capabilities = client.get_capabilities()
            logger.info(f"XAI capabilities: {capabilities}")
            
            # Test autonomous reasoning
            test_result = client.autonomous_reasoning(
                "Test autonomous reasoning capability",
                {"test": True, "verification": "model_resolver"}
            )
            
            success = bool(test_result.get("content"))
            logger.info(f"XAI autonomous reasoning test: {'✅ Passed' if success else '❌ Failed'}")
            
            return success
            
        except Exception as e:
            logger.error(f"XAI integration test failed: {e}")
            return False

# Test the enhanced resolver
if __name__ == "__main__":
    resolver = ModelResolver()
    
    print("🔧 KOR'TANA MODEL RESOLVER TEST")
    print("=" * 50)
    
    # Test alias resolution
    test_identifiers = [
        "grok-3-mini-reasoning",
        "grok-3-mini", 
        "gemini-2.5-flash",
        "gemini-flash",
        "autonomous_development",
        "primary"
    ]
    
    print("📋 Model Resolution Test:")
    for identifier in test_identifiers:
        resolved = resolver.resolve_model_id(identifier)
        config = resolver.get_model_config(identifier)
        available = config is not None and config.get("enabled", False)
        
        print(f"   '{identifier}' -> '{resolved}' {'✅' if available else '❌'}")
    
    print(f"\n🔍 Autonomous System Verification:")
    verification = resolver.verify_autonomous_models()
    for model_id, available in verification.items():
        print(f"   {model_id}: {'✅ Available' if available else '❌ Missing'}")
    
    print(f"\n📊 Total Available Models: {len(resolver.get_available_models())}")
    
    print(f"\n🤖 XAI Integration Test:")
    xai_test = resolver.test_xai_integration()
    print(f"   XAI Grok Client: {'✅ Working' if xai_test else '❌ Failed'}")
