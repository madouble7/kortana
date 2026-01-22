import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from kortana.config.schema import KortanaConfig
from kortana.llm_clients.factory import LLMClientFactory
from src.kortana.core import prompts
from src.kortana.modules.ethical_discernment_module.evaluators import (
    AlgorithmicArroganceEvaluator,
    UncertaintyHandler,
)
from src.kortana.modules.memory_core.services import MemoryCoreService


class KorOrchestrator:
    def __init__(self, db: Session, config: KortanaConfig | None = None):
        self.db = db
        self.memory_service = MemoryCoreService(db)
        self.arrogance_evaluator = AlgorithmicArroganceEvaluator()
        self.uncertainty_handler = UncertaintyHandler()

        # Load model configuration from the config file
        self.config = config
        models_config = self._load_models_config()

        # Initialize the LLM client factory with KortanaConfig
        config_obj = KortanaConfig(models=models_config)
        self.llm_factory = LLMClientFactory(config_obj)

        # Get the default LLM client (will be used for core reasoning)
        self.default_model_id = models_config.get("default", {}).get(
            "model", "gpt-4.1-nano"
        )

    def _load_models_config(self) -> dict:
        """Load the models configuration from models_config.json"""
        # Try to find the models_config.json file
        config_paths = [
            Path("config/models_config.json"),
            Path("../config/models_config.json"),
            Path(__file__).parent.parent.parent.parent
            / "config"
            / "models_config.json",
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Error loading models config from {config_path}: {e}")

        # Return a minimal default configuration if no config is found
        return {
            "models": {
                "gpt-4.1-nano": {
                    "provider": "openai",
                    "api_key_env": "OPENAI_API_KEY",
                    "model_name": "gpt-4.1-nano",
                }
            },
            "default": {"model": "gpt-4.1-nano"},
        }

    async def process_query(self, query: str, language: str | None = None) -> dict[str, Any]:
        """
        The main thinking loop for Kor'tana, now with a live LLM call.
        Supports multilingual responses via the language parameter.
        
        Args:
            query: The user's query
            language: Optional ISO 639-1 language code for the response
        """
        # Validate and normalize language if provided
        from src.kortana.utils.language_utils import (
            get_system_prompt_for_language,
            validate_language_code,
        )
        
        target_language = validate_language_code(language) if language else "en"
        language_instruction = get_system_prompt_for_language(target_language)
        
        # 1. Search memory for relevant context (no change here)
        relevant_memories = self.memory_service.search_memories_semantic(query, top_k=3)

        # 2. Build the prompt for the LLM
        prompt_for_llm = prompts.build_core_query_prompt(query, relevant_memories)

        # 3. Get the appropriate LLM client and call it
        print(
            f"--- Sending Prompt to LLM ---\n{prompt_for_llm}\n-------------------------------"
        )  # Log the prompt

        llm_client = self.llm_factory.get_client(self.default_model_id)
        if not llm_client:
            error_message = (
                f"Failed to initialize LLM client for model {self.default_model_id}"
            )
            print(f"--- LLM Client Error ---\n{error_message}")
            return {
                "original_query": query,
                "prompt_sent_to_llm": prompt_for_llm,
                "error": "Failed to initialize LLM service.",
                "error_detail": error_message,
                "final_kortana_response": "I'm having trouble connecting to my reasoning core right now. Please try again in a moment.",
            }

        # Call the LLM client with the prompt
        # Build system prompt with language instruction if needed
        base_system_prompt = "You are responding as Kor'tana, a unique AI with a developing identity."
        system_prompt = f"{base_system_prompt} {language_instruction}".strip()
        
        llm_result = await llm_client.generate_response(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": prompt_for_llm}],
        )

        # Extract the content and metadata from the result
        llm_response_content = llm_result.get("content")
        llm_response_metadata = {
            "model": llm_result.get("model_id_used", self.default_model_id),
            "usage": llm_result.get("usage", {}),
        }

        # Handle case where LLM call fails
        if not llm_response_content:
            error_message = llm_result.get("error", "Unknown error from LLM service.")
            print(f"--- LLM Service Error ---\n{error_message}")  # Log the error
            return {
                "original_query": query,
                "prompt_sent_to_llm": prompt_for_llm,
                "error": "Failed to get response from reasoning core.",
                "error_detail": error_message,
                "final_kortana_response": "I'm having trouble connecting to my reasoning core right now. Please try again in a moment.",
            }

        print(
            f"--- Raw LLM Response ---\nContent: {llm_response_content}\nMetadata: {llm_response_metadata}"
        )  # Log the raw response

        # 4. Evaluate the LLM response for ethical alignment
        evaluation = await self.arrogance_evaluator.evaluate_response(
            response_text=llm_response_content,
            llm_metadata=llm_response_metadata,
            original_query_context=query,
        )
        print(f"--- Ethical Evaluation ---\n{evaluation}")  # Log evaluation

        # 5. Form Kor'tana's final response
        final_response = await self.uncertainty_handler.manage_uncertainty(
            original_query=query,
            llm_response=llm_response_content,
            evaluation_results=evaluation,
        )
        print(
            f"--- Final Kor'tana Response ---\n{final_response}"
        )  # Log final response

        # Return the structured response for debugging and visibility
        return {
            "original_query": query,
            "language": target_language,
            "context_from_memory": [mem["memory"].content for mem in relevant_memories],
            "prompt_sent_to_llm": prompt_for_llm,
            "raw_llm_response": llm_response_content,
            "llm_metadata": llm_response_metadata,
            "ethical_evaluation": evaluation,
            "final_kortana_response": final_response,
        }
