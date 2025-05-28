# src/llm_clients/grok_client.py
"""Grok client implementation for Kor'tana."""

from .base_client import BaseLLMClient
import openai  # Assuming xAI API is OpenAI compatible [2]
import httpx
import logging
from typing import List, Dict, Any, Optional

class GrokClient(BaseLLMClient):
    """Client for xAI's Grok models. [3]

    Grok provides Kor'tana with strong reasoning capabilities[4]
    poetic expression, and depth of thought.
    """

    def __init__(self, api_key: str, model_name: str, base_url: str, default_params: Dict):
        """Initialize the Grok client.

        Args:
            api_key: xAI API key
            model_name: Specific Grok model name
            base_url: API endpoint URL
            default_params: Default parameters for API calls
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.default_params = default_params

        # Set up HTTP client and OpenAI client
        http_client = httpx.Client(timeout=60.0)  # Increased timeout for reliability
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)
        logging.info(f"GrokClient initialized for {model_name}")

    def generate_response(self, system_prompt: str, messages: List) -> Dict[str, Any]:
        """Generate a response from Grok.

        Handles Grok-specific parameters like reasoning_effort. [1]
        """
        reasoning_effort_to_use = self.default_params.get("reasoning_effort", "high")

        api_params = {
            "model": self.model_name,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "temperature": self.default_params.get("temperature", 0.7),
            "max_tokens": self.default_params.get("max_tokens", 1024)
        }

        extra_body_params = {
            "reasoning_effort": reasoning_effort_to_use
        }
        api_params["extra_body"] = extra_body_params # For OpenAI compatible clients that support extra_body

        try:
            completion = self.client.chat.completions.create(**api_params)
            # Debug log for structure
            logging.debug(f"GrokClient completion.choices: {completion.choices}")
            content = completion.choices[0].message.content or ""
            # Attempt to get reasoning_content if the API provides it in a compatible way [1]
            reasoning_raw = getattr(completion.choices[0].message, 'reasoning_content', None)
            if not reasoning_raw and hasattr(completion.choices[0].message, 'reasoning_content'):
                reasoning_raw = completion.choices[0].message.get('reasoning_content')
            elif not reasoning_raw and hasattr(completion, '_dict') and 'reasoning_content' in completion._dict.get('choices', [{}])[0].get('message', {}):
                reasoning_raw = completion._dict['choices'][0]['message']['reasoning_content']

            reasoning = str(reasoning_raw) if reasoning_raw is not None else None
            usage = completion.usage.model_dump() if completion.usage else {}

            logging.info(f"Grok call successful. Usage: {usage}")
            if reasoning: 
                logging.info(f"Grok Reasoning excerpt: {reasoning[:200]}...")

            return {
                "content": content.strip(), 
                "reasoning_content": reasoning, 
                "usage": usage, 
                "error": None, 
                "model_id_used": self.model_name
            }
        except Exception as e:
            logging.error(f"GrokClient API error: {e}", exc_info=True)
            return {
                "content": f"Error with Grok: {e}", 
                "reasoning_content": None, 
                "usage": {}, 
                "error": str(e), 
                "model_id_used": self.model_name
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """Return Grok-specific capabilities."""
        return {
            "name": self.model_name,
            "provider": "xai_grok",
            "context_window": 8192,  # Adjust based on actual model, Grok-3 Mini is 131k [4]
            "supports_reasoning": True, # Grok-3 Mini supports reasoning_content [1]
            "strengths": ["reasoning", "poetic expression", "depth of thought"],
            "suited_modes": ["presence", "fire"] # Example, adjust as per persona design
        }
