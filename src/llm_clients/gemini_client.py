# C:\kortana\src\llm_clients\gemini_client.py
# Purpose: Implements a client for Google's Gemini models.
# Role: Enables Kor'tana to use Gemini Flash for responsive, reflective, or cost-aware interactions.

"""Gemini client implementation for Kor'tana."""

import logging
import os
from typing import Dict, List, Tuple, Any, Optional
import time

try:
    import google.genai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)

class GoogleGenAIClient(BaseLLMClient):
    """
    Google Gemini client using the correct google.genai library initialization.
    Handles multi-turn conversations and system prompts for Kor'tana.
    """
    
    def __init__(self, model_id: str, api_key_env: str = "GOOGLE_API_KEY", 
                 model_name: str = "gemini-pro", **kwargs):
        super().__init__(model_id, **kwargs)
        
        self.api_key = os.getenv(api_key_env)
        if not self.api_key:
            logger.error(f"API key environment variable {api_key_env} not found for GoogleGenAIClient.")
            raise ValueError(f"API key for {model_id} not found in environment variable {api_key_env}")
        
        self.model_name_for_api = model_name  # e.g., "gemini-1.5-flash-latest", "gemini-pro"
        self.model_id = model_id
        
        if not GENAI_AVAILABLE:
            logger.error("google.genai library not available. Install with: pip install google-genai")
            raise ImportError("google.genai library required for GoogleGenAIClient")
        
        try:
            # Configure the library with API key
            genai.configure(api_key=self.api_key)
            
            # Initialize the model
            self.model = genai.GenerativeModel(self.model_name_for_api)
            self.genai_module = genai
            
            logger.info(f"GoogleGenAIClient for model '{self.model_name_for_api}' initialized successfully.")
            
        except Exception as e:
            logger.error(f"Failed to initialize GoogleGenAIClient for model '{self.model_name_for_api}': {e}")
            raise
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return capabilities of the Google Gemini client."""
        return {
            "supports_system_prompt": True,
            "supports_function_calling": False,  # Update based on model capabilities
            "supports_streaming": True,
            "max_context_length": 1048576 if "flash" in self.model_name_for_api else 32768,
            "supports_multimodal": True
        }
    
    def generate_response(self, system_prompt: str, messages: List[Dict[str, str]], **kwargs) -> Tuple[str, Dict]:
        """
        Generate response using Google Gemini API.
        
        Args:
            system_prompt: System instructions for the model
            messages: List of conversation messages with 'role' and 'content'
            **kwargs: Additional parameters like temperature, max_tokens
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        try:
            # Prepare messages for Google API format
            formatted_messages = []
            
            # Handle system prompt by prepending to first user message or adding as instruction
            if system_prompt:
                if messages and messages[0]['role'] == 'user':
                    # Prepend system prompt to first user message
                    messages[0]['content'] = system_prompt + "\n\n" + messages[0]['content']
                else:
                    # Add system prompt as initial user message with model acknowledgment
                    formatted_messages.append({'role': 'user', 'parts': [{'text': system_prompt}]})
                    formatted_messages.append({'role': 'model', 'parts': [{'text': "I understand. I'll follow these instructions."}]})
            
            # Convert messages to Google API format
            for msg in messages:
                role = msg['role']
                content = msg['content']
                
                # Map roles: 'assistant' -> 'model', 'user' -> 'user'
                api_role = "model" if role == "assistant" else "user"
                formatted_messages.append({
                    'role': api_role, 
                    'parts': [{'text': content}]
                })
            
            # Extract generation parameters
            generation_config = {}
            if 'temperature' in kwargs:
                generation_config['temperature'] = kwargs['temperature']
            if 'max_tokens' in kwargs:
                generation_config['max_output_tokens'] = kwargs['max_tokens']
            if 'top_p' in kwargs:
                generation_config['top_p'] = kwargs['top_p']
            
            # Make the API call
            start_time = time.time()
            
            if formatted_messages:
                # Multi-turn conversation
                api_response = self.model.generate_content(
                    formatted_messages,
                    generation_config=generation_config if generation_config else None
                )
            else:
                # Single prompt (fallback)
                api_response = self.model.generate_content(
                    system_prompt or "Hello",
                    generation_config=generation_config if generation_config else None
                )
            
            end_time = time.time()
            
            # Extract response text
            response_text = api_response.text if hasattr(api_response, 'text') else str(api_response)
            
            # Extract usage data (Google API might have different structure)
            usage_data = {
                "prompt_tokens": getattr(api_response, 'prompt_token_count', 0),
                "completion_tokens": getattr(api_response, 'candidates_token_count', 0) if hasattr(api_response, 'candidates_token_count') else len(response_text.split()),
                "total_tokens": getattr(api_response, 'total_token_count', 0),
                "latency_sec": end_time - start_time
            }
            
            logger.debug(f"Google Gemini response generated successfully. Length: {len(response_text)} chars")
            return response_text, usage_data
            
        except Exception as e:
            logger.error(f"Error in GoogleGenAIClient.generate_response for model {self.model_name_for_api}: {e}")
            error_response = f"I encountered an issue while processing your request: {str(e)}"
            error_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return error_response, error_usage
    
    def get_completion(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """
        Legacy compatibility method for ChatEngine.
        Returns response in a structure compatible with existing code.
        """
        try:
            # Extract system prompt if present
            system_prompt = ""
            conversation_messages = []
            
            for msg in messages:
                if msg.get('role') == 'system':
                    system_prompt = msg.get('content', '')
                else:
                    conversation_messages.append(msg)
            
            response_text, usage_data = self.generate_response(system_prompt, conversation_messages, **kwargs)
            
            # Return in OpenAI-compatible structure for existing ChatEngine parsing
            return type('Response', (), {
                'choices': [type('Choice', (), {
                    'message': type('Message', (), {
                        'content': response_text,
                        'tool_calls': None
                    })()
                })()],
                'usage': type('Usage', (), usage_data)(),
                'model': self.model_name_for_api
            })()
            
        except Exception as e:
            logger.error(f"Error in GoogleGenAIClient.get_completion: {e}")
            # Return error in compatible structure
            return type('Response', (), {
                'choices': [type('Choice', (), {
                    'message': type('Message', (), {
                        'content': f"Error: {str(e)}",
                        'tool_calls': None
                    })()
                })()],
                'usage': type('Usage', (), {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})(),
                'model': self.model_name_for_api
            })()

    def test_connection(self) -> bool:
        """Test if the client can connect to Google's API."""
        try:
            test_response = self.model.generate_content("Test connection")
            return bool(test_response.text)
        except Exception as e:
            logger.error(f"Google Gemini connection test failed: {e}")
            return False