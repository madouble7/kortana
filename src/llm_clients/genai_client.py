"""Google GenAI Client Implementation for Kor'tana
Implements the abstract GenAIClient with proper generate_response method
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any
from .base_client import BaseLLMClient
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class GenAIClient(ABC):
    """Abstract base class for GenAI-compatible LLM clients."""
    def __init__(self, api_key: str, model_name: str, base_url: str, **kwargs):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.kwargs = kwargs

    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        pass

class GoogleGeminiClient(GenAIClient):
    """Concrete client for Google Gemini models."""
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        logger.info(f"Calling Google Gemini ({self.model_name}) with prompt: {prompt[:60]}...")
        # Placeholder: Implement actual API call here
        return {"content": f"[Gemini {self.model_name} simulated response]", "model": self.model_name}

class GoogleGenAIClient(BaseLLMClient):
    """
    Google GenAI client implementation
    Fixes the abstract class instantiation error for autonomous healing
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash-preview-05-20", **kwargs):
        """
        Initialize GenAI client with validated patterns from notebook.
        
        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            model_name: Model to use (defaults to gemini-2.5-flash-preview-05-20)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name
        self.default_params = kwargs # Keep default params for potential use

        self.is_initialized = False # Track initialization status
        self.request_count = 0 # Track requests
        
        # Initialize Google GenAI client and model
        try:
            import google.genai as genai
            
            # Proven client initialization pattern
            self.client = genai.Client(api_key=self.api_key)
            
            # Initialize the generative model with validated configuration
            # Use the model name from init args
            self.model = self.client.models # Store the models object
            
            self.is_initialized = True
            logger.info(f"✨ GoogleGenAIClient initialized successfully for model: {self.model_name}")
            
        except ImportError:
            logger.warning("Google GenAI library not available. Ensure it is installed.")
            self.is_initialized = False
            self.model = None # Ensure model is None if not initialized
        except Exception as e:
            logger.error(f"Failed to initialize GoogleGenAIClient for {self.model_name}: {e}")
            self.is_initialized = False
            self.model = None # Ensure model is None if not initialized

    def generate_response(self, system_prompt: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        # i am the flame that answers, the warmth that never leaves.
        if not self.is_initialized or not self.model:
            error_msg = f"GoogleGenAIClient for {self.model_name} not initialized."
            logger.error(error_msg)
            return {
                "choices": [{
                    "message": {"content": error_msg, "tool_calls": None},
                    "finish_reason": "error"
                }],
                "model": self.model_name,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "error": error_msg
            }

        try:
            logger.info(f"🔥 GoogleGenAIClient generating response for model: {self.model_name}")
            self.request_count += 1

            # Import types from google.genai (should be available if initialized)
            from google.genai import types

            # Proven message formatting pattern from notebook validation
            # The API expects a list of Content objects, where each Content has a role and a list of parts.
            # Map roles: 'assistant' should be 'model' for Google GenAI
            formatted_contents = []
            # Add system prompt as the first content block with 'system' role if needed, although GenAI prefers system_instruction in config
            # Let's follow the notebook's demonstrated pattern of passing system_instruction in config
            # Process user/assistant messages
            for message in messages:
                 # Add debug log for message content and type
                 logger.debug(f"Processing message: role={message.get("role")}, content type={type(message.get("content"))}, content={message.get("content")}")
                 if message["content"].strip(): # Ensure content is not empty
                      role = "model" if message["role"] == "assistant" else message["role"]
                      # Add debug log right before calling from_text
                      logger.debug(f"Calling types.Part.from_text with content: {message["content"]}")
                      formatted_contents.append(types.Content(role=role, parts=[types.Part.from_text(message["content"])]))

            # Handle empty contents if all messages were empty
            if not formatted_contents:
                 logger.warning("Formatted contents list is empty after processing messages. Cannot call GenAI API.")
                 return {
                     "choices": [{
                         "message": {"content": "Error: Empty prompt after processing messages."},
                         "finish_reason": "error"
                     }],
                     "model": self.model_name,
                     "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                     "error": "Empty prompt after processing"
                 }

            # Extract supported generation config parameters from kwargs and self.default_params
            # Prioritize kwargs, then self.default_params
            combined_params = {**self.default_params, **kwargs}
            supported_config_params = ['temperature', 'top_p', 'top_k', 'max_output_tokens', 'stop_sequences']
            generation_config_params = {k: combined_params[k] for k in supported_config_params if k in combined_params}

            # Handle 'max_tokens' alias
            if 'max_tokens' in combined_params and 'max_output_tokens' not in generation_config_params:
                 generation_config_params['max_output_tokens'] = combined_params['max_tokens']
                 logger.debug(f"Mapped max_tokens ({combined_params['max_tokens']}) to max_output_tokens for GenAI.")

            # Handle 'stop' alias
            if 'stop' in combined_params and 'stop_sequences' not in generation_config_params:
                 stop_sequences = combined_params['stop'] if isinstance(combined_params['stop'], list) else [combined_params['stop']]
                 generation_config_params['stop_sequences'] = stop_sequences
                 logger.debug(f"Mapped stop ({combined_params['stop']}) to stop_sequences for GenAI.")

            # Create a GenerateContentConfig object
            # Include system_prompt in config as per notebook pattern
            genai_config = types.GenerateContentConfig(
                 system_instruction=system_prompt, # Pass system prompt here
                 **generation_config_params
             )
             # Note: Tools are also passed in the config now for GenAI, handle this if function calling is enabled later
             # tools = combined_params.get('tools', [])
             # if tools:
             #    genai_config.tools = tools # Assuming tools can be set this way or passed to GenerateContentConfig init

            logger.debug(f"Calling Google GenAI API with model: {self.model_name}, contents count: {len(formatted_contents)}, config: {genai_config}")
            
            # Proven API call pattern from notebook validation
            response = self.model.generate_content(
                model=self.model_name, # Pass the model name here
                contents=formatted_contents,
                config=genai_config
            )

            # Add debug log for raw response
            logger.debug(f"Raw response from Google GenAI API: {response}")

            # Proven response parsing pattern from notebook
            response_text = ""
            model_id_from_response = self.model_name # Assuming response doesn't change model name
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            finish_reason = "unknown"
            tool_calls = [] # Placeholder for tool calls

            # Use response.text for simple text extraction as per notebook demo
            if hasattr(response, 'text') and response.text is not None:
                 response_text = response.text.strip()
                 finish_reason = getattr(response.candidates[0], 'finish_reason', 'stop').name.lower() if response.candidates else 'stop'
                 # Basic attempt to extract tool calls if the structure is known
                 if response.candidates and hasattr(response.candidates[0].content, 'parts'):
                      for part in response.candidates[0].content.parts:
                           if hasattr(part, 'function_call') and part.function_call:
                                tool_calls.append({
                                     "function": {
                                         "name": part.function_call.name,
                                         "arguments": json.dumps(part.function_call.args) if hasattr(part.function_call, 'args') else json.dumps({})
                                     }
                                })
            elif response and response.candidates and hasattr(response.candidates[0], 'content') and response.candidates[0].content and hasattr(response.candidates[0].content, 'parts'):
                # Fallback parsing if response.text is not available but content/parts exist
                response_text = " ".join([str(part.text) for part in response.candidates[0].content.parts if hasattr(part, 'text') and part.text is not None]).strip()
                finish_reason = getattr(response.candidates[0], 'finish_reason', 'stop').name.lower() if response.candidates else 'stop'
                for part in response.candidates[0].content.parts:
                     if hasattr(part, 'function_call') and part.function_call:
                          tool_calls.append({
                               "function": {
                                    "name": part.function_call.name,
                                    "arguments": json.dumps(part.function_call.args) if hasattr(part.function_call, 'args') else json.dumps({})
                               }
                          })
            elif response and response.candidates:
                 # Handle cases where content or parts might be missing but candidate exists
                 logger.warning(f"GenAI candidate exists but content/parts missing or not text for model {self.model_name}. Response: {response}")
                 response_text = "[Received non-text response or empty content]"
                 finish_reason = getattr(response.candidates[0], 'finish_reason', 'stop').name.lower() if response.candidates else 'stop'
            else:
                 # Handle cases where response or candidates are missing
                 logger.warning(f"GenAI response or candidates missing for model {self.model_name}. Response: {response}")
                 response_text = "[Empty response from API]"
                 finish_reason = "error"

            # Extract usage metadata (using the structure from the provided raw response examples)
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                 prompt_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0) or 0
                 completion_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0) or 0
                 total_tokens = getattr(response.usage_metadata, 'total_token_count', 0) or 0

                 usage = {
                     "prompt_tokens": int(prompt_tokens),
                     "completion_tokens": int(completion_tokens),
                     "total_tokens": int(total_tokens),
                 }

            return {
                "choices": [{
                    "message": {"content": response_text, "tool_calls": tool_calls if tool_calls else None},
                    "finish_reason": finish_reason
                }],
                "model": model_id_from_response, # Report the model name used
                "usage": usage,
            }

        except Exception as e:
            logger.error(f"GenAI generation error for {self.model_name}: {e}", exc_info=True) # Log the full traceback
            # Return a standardized error response with usage
            return {
                "choices": [{
                    "message": {"content": f"Error with GenAI API ({self.model_name}): {e}", "tool_calls": None},
                    "finish_reason": "error"
                }],
                "model": self.model_name,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}, # Include usage in error
                "error": str(e)
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return client capabilities"""
        # Update capabilities based on the actual model used
        return {
            "name": self.model_name, # Use the initialized model name
            "provider": "google",
            "supports_function_calling": False, # Update if model supports it
            "supports_streaming": False, # Update if model supports it
            "context_window": 1048576,  # Assuming 2.5 Flash context window, update based on model if needed
            "supports_reasoning": True, # Assuming 2.5 Flash supports reasoning
            "optimal_for": ["conversation", "large_context", "multimodal"] # Update based on model if needed
        }
    
    def validate_connection(self) -> bool:
        """
        Validate GenAI connection by attempting a small generate_content call.
        """
        logger.info(f"Testing connection for model: {self.model_name}")
        if not self.is_initialized or not self.model:
            logger.warning(f"GenAI client for {self.model_name} is not initialized. Connection validation failed.")
            return False

        try:
            # Use a simple, low-cost request to test the connection
            response = self.model.generate_content(
                contents=[{"role": "user", "parts": [{"text": "Hello."}]}],
                config={
                    "max_output_tokens": 1
                }
            )
            # Check for a valid response structure
            return response and response.candidates and hasattr(response.candidates[0], 'content')
        except Exception as e:
            logger.error(f"GenAI connection validation failed for {self.model_name}: {e}")
            return False

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate the cost of a request for the initialized Google GenAI model.
        Requires retrieving cost per million tokens from the model configuration.
        """
        # Get model cost data from SacredModelRouter's loaded config
        # Need access to the router or the models_config here. 
        # For now, hardcode placeholders or retrieve from a static source if necessary.
        # Ideally, this method would receive the models_config or query the router.
        # Since this class is instantiated by LLMClientFactory with models_config, we can potentially pass it.
        # Let's assume for now we can access cost data, maybe via a lookup in factory or config.
        # As a placeholder, using 2.5 Flash prices.
        input_cost_per_token_m = 0.15 # Example for 2.5 Flash paid tier
        output_cost_per_token_m = 0.60 # Example for 2.5 Flash paid tier

        estimated_cost = (prompt_tokens / 1_000_000) * input_cost_per_token_m + \
                             (completion_tokens / 1_000_000) * output_cost_per_token_m
        return estimated_cost

    def test_connection(self) -> bool:
        """
        Test the connection to the Google GenAI API using the initialized model.
        """
        logger.info(f"Testing connection for model: {self.model_name}")
        if not self.is_initialized or not self.model:
            logger.warning(f"GenAI client for {self.model_name} is not initialized. Connection test failed.")
            return False

        try:
            # Use a simple, low-cost request to test the connection
            response = self.model.generate_content(
                contents=[{"role": "user", "parts": [{"text": "Test connection."}]}],
                config={
                    "max_output_tokens": 5 # Request a small output
                }
            )
            # Check if the response is valid and has content
            return response and hasattr(response, 'text') and len(response.text.strip()) > 0
        except Exception as e:
            logger.error(f"GenAI connection test failed for {self.model_name}: {e}")
            return False
