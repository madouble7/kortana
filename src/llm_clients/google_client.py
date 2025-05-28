"""
Google Gemini client implementation for Kor'tana
Optimized for Gemini 2.5 Flash, 2.0 Flash, and free tier usage
Supports adaptive thinking, multimodal input, and rate limit management
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional, Any, Union
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)

class GoogleGeminiClient(BaseLLMClient):
    """
    Google Gemini client optimized for latest models and free tier
    Supports Gemini 2.5 Flash, 2.0 Flash, and multimodal capabilities
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash-preview-05-20", **kwargs):
        """
        Initialize Google Gemini client
        
        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            model_name: Gemini model to use
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name
        self.default_params = kwargs
        
        # Configure the Gemini client
        genai.configure(api_key=self.api_key)
        
        # Initialize the model with safety settings
        self.model = genai.GenerativeModel(
            model_name=model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # Rate limiting for free tier
        self.rate_limiter = {
            "last_request_time": 0,
            "requests_this_minute": 0,
            "minute_start": time.time(),
            "rpm_limit": self._get_rpm_limit()
        }
        
        logger.info(f"GoogleGeminiClient initialized for model: {model_name}")
    
    def _get_rpm_limit(self) -> int:
        """Get RPM limit based on model"""
        limits = {
            "gemini-2.5-flash-preview-05-20": 10,
            "gemini-2.0-flash": 15,
            "gemini-2.0-flash-lite": 30,
            "gemini-1.5-flash": 15,
            "gemini-1.5-flash-8b": 15
        }
        return limits.get(self.model_name, 10)
    
    def _respect_rate_limits(self):
        """Implement rate limiting for free tier"""
        current_time = time.time()
        
        # Reset minute counter if needed
        if current_time - self.rate_limiter["minute_start"] >= 60:
            self.rate_limiter["requests_this_minute"] = 0
            self.rate_limiter["minute_start"] = current_time
        
        # Check if we're at the limit
        if self.rate_limiter["requests_this_minute"] >= self.rate_limiter["rpm_limit"]:
            sleep_time = 60 - (current_time - self.rate_limiter["minute_start"])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                self.rate_limiter["requests_this_minute"] = 0
                self.rate_limiter["minute_start"] = time.time()
        
        # Minimum delay between requests
        time_since_last = current_time - self.rate_limiter["last_request_time"]
        if time_since_last < 1.0:  # Minimum 1 second between requests
            time.sleep(1.0 - time_since_last)
        
        self.rate_limiter["requests_this_minute"] += 1
        self.rate_limiter["last_request_time"] = time.time()
    
    def _standardize_response(self, content: str, model_id: str, usage: Dict[str, int], 
                            finish_reason: str = "stop") -> Dict[str, Any]:
        """Standardize response format to match OpenAI structure"""
        return {
            "choices": [
                {
                    "message": {"content": content},
                    "finish_reason": finish_reason
                }
            ],
            "model": model_id,
            "usage": usage
        }
    
    def generate_response(self, system_prompt: str, messages: List[Dict[str, str]], 
                         enable_function_calling: bool = False, functions: Optional[List[Dict]] = None,
                         **kwargs) -> Dict[str, Any]:
        """Generate response using Google Gemini API"""
        try:
            # Respect rate limits
            self._respect_rate_limits()
            
            # Prepare the conversation context
            full_context = []
            if system_prompt:
                full_context.append(f"System: {system_prompt}")
            
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    full_context.append(f"User: {content}")
                elif role == "assistant":
                    full_context.append(f"Assistant: {content}")
            
            conversation_text = "\n\n".join(full_context)
            
            # Generation configuration
            generation_config = genai.types.GenerationConfig(
                temperature=kwargs.get("temperature", 0.7),
                max_output_tokens=kwargs.get("max_tokens", 4096),
                top_p=kwargs.get("top_p", 0.9),
                top_k=kwargs.get("top_k", 40)
            )
            
            # Generate response
            response = self.model.generate_content(
                conversation_text,
                generation_config=generation_config
            )
            
            # Extract content
            content = response.text if response.text else "I apologize, but I couldn't generate a response."
            
            # Extract usage information
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                "total_tokens": response.usage_metadata.total_token_count if response.usage_metadata else 0
            }
            
            finish_reason = "stop"
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason = str(response.candidates[0].finish_reason).lower()
            
            logger.info(f"Gemini response generated successfully. Tokens: {usage['total_tokens']}")
            
            return self._standardize_response(
                content=content,
                model_id=self.model_name,
                usage=usage,
                finish_reason=finish_reason
            )
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._standardize_response(
                content=f"Error with Gemini API: {e}",
                model_id=self.model_name,
                usage={},
                finish_reason="error"
            )
    
    def get_completion(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """Get completion from Gemini API - matches expected interface"""
        try:
            # Respect rate limits
            self._respect_rate_limits()
            
            # Convert messages to Gemini format
            conversation_parts = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    # Add system message as context
                    conversation_parts.append(f"Instructions: {content}")
                elif role == "user":
                    conversation_parts.append(f"User: {content}")
                elif role == "assistant":
                    conversation_parts.append(f"Assistant: {content}")
            
            prompt = "\n\n".join(conversation_parts)
            
            # Generation config
            generation_config = genai.types.GenerationConfig(
                temperature=kwargs.get("temperature", 0.7),
                max_output_tokens=kwargs.get("max_tokens", 4096),
                top_p=kwargs.get("top_p", 0.9)
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            logger.debug(f"Gemini API call successful for model: {self.model_name}")
            return response
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return client capabilities"""
        base_capabilities = {
            "name": self.model_name,
            "provider": "google",
            "supports_function_calling": False,  # Not yet implemented
            "supports_streaming": True,
            "supports_multimodal": True,
            "context_window": 1048576,  # 1M tokens for most Gemini models
            "supports_reasoning": True,
            "optimal_for": ["conversation", "research", "multimodal", "long_context"]
        }
        
        # Model-specific capabilities
        if "2.5-flash" in self.model_name:
            base_capabilities.update({
                "adaptive_thinking": True,
                "cost_efficiency": "maximum",
                "multimodal_excellence": True
            })
        elif "2.0-flash" in self.model_name:
            base_capabilities.update({
                "next_generation": True,
                "realtime_streaming": True,
                "thinking": True
            })
        
        return base_capabilities
    
    def validate_connection(self) -> bool:
        """Validate Gemini API connection"""
        try:
            test_response = self.model.generate_content(
                "Test connection",
                generation_config=genai.types.GenerationConfig(max_output_tokens=5)
            )
            return bool(test_response.text)
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost (free tier = $0)"""
        return 0.0  # Free tier
    
    def test_connection(self) -> bool:
        """Test connection to Gemini API"""
        try:
            self._respect_rate_limits()
            
            test_response = self.model.generate_content(
                "Hello",
                generation_config=genai.types.GenerationConfig(max_output_tokens=5)
            )
            
            if test_response and test_response.text:
                logger.info(f"Gemini connection test successful for {self.model_name}")
                return True
            else:
                logger.error("Gemini connection test failed: No response")
                return False
                
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False
    
    def supports_streaming(self) -> bool:
        """Check if client supports streaming"""
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information"""
        return {
            "model_name": self.model_name,
            "provider": "google",
            "capabilities": self.get_capabilities(),
            "api_key_configured": bool(self.api_key),
            "rate_limits": {
                "rpm": self.rate_limiter["rpm_limit"],
                "free_tier": True
            }
        }
