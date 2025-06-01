# Project Kor'tana: Codebase Map

This document provides an automatically generated overview of the key source directories in the Kor'tana project, including file summaries, main components, and flagged items.

## Summary

- Total Files Scanned: [Calculating...]
- Test Coverage: [Cannot be automatically calculated without running tests]
- Flagged Items (TODOs/FIXMEs): [Calculating...]
- Potential Broken Imports: [Cannot be definitively determined without running code; imports will be listed where easily visible.]

---

## Directory: `src/`

### File: `agents_sdk_integration.py`

- **Purpose:** Integrates with OpenAI Agents SDK (currently using fallback implementations) to provide autonomous agent capabilities with Sacred Covenant compliance.
- **Main Components:**
  - Classes: `Agent` (Fallback), `Runner` (Fallback), `SacredCovenantGuardrail`, `KortanaAgentsSDK`
  - Functions: `tool` (decorator), `analyze_codebase`, `generate_code_fix`, `apply_code_fix`, `run_tests`, `_create_detection_agent`, `_create_planning_agent`, `_create_coding_agent`, `_create_testing_agent`, `autonomous_repair_cycle`, `create_kortana_agents_sdk`
- **Flagged Items:** None explicitly visible in the scanned portion.
- **Imports:** `logging`, `datetime`, `typing`, `.covenant_enforcer`, `os` (within function). Notes presence of try-except for `openai`, indicating potential broken import or incomplete integration.

### File: `agents_sdk_integration_clean.py`

- **Purpose:** Appears to be a duplicate or cleaned-up version of `agents_sdk_integration.py`, integrating with OpenAI Agents SDK (using fallback implementations).
- **Main Components:** Same as `agents_sdk_integration.py` (Classes: `Agent`, `Runner`, `SacredCovenantGuardrail`, `KortanaAgentsSDK`; Functions: `tool`, `analyze_codebase`, `generate_code_fix`, `apply_code_fix`, `run_tests`, `_create_detection_agent`, `_create_planning_agent`, `_create_coding_agent`, `_create_testing_agent`, `autonomous_repair_cycle`, `create_kortana_agents_sdk`).
- **Flagged Items:** Appears to be a duplicate file that should be reviewed for redundancy.
- **Imports:** Same as `agents_sdk_integration.py` (`logging`, `datetime`, `typing`, `.covenant_enforcer`, `os` (within function)).

### File: `agents_sdk_integration_corrupted.py`

- **Purpose:** Appears to be a variant or potentially incomplete version of `agents_sdk_integration.py`, integrating with OpenAI Agents SDK (using fallback implementations).
- **Main Components:** Similar to `agents_sdk_integration.py` (Classes: `Agent`, `Runner`, `SacredCovenantGuardrail`, `KortanaAgentsSDK`; Functions: `tool`, `analyze_codebase`, `generate_code_fix`, `apply_code_fix`, `run_tests`, `_create_detection_agent`, `_create_planning_agent`, `_create_coding_agent`, `_create_testing_agent`, `autonomous_repair_cycle`, `create_kortana_agents_sdk`).
- **Flagged Items:** Appears to be a variant or duplicate file that should be reviewed for redundancy/differences.
- **Imports:** Same as `agents_sdk_integration.py` (`logging`, `datetime`, `typing`, `.covenant_enforcer`, `os` (within function)).

### File: `brain.py`

- **Purpose:** Contains the core `ChatEngine` class, managing Kor'tana's conversational logic, LLM client interaction, memory, modes, task classification, and integration with autonomous agents.
- **Main Components:**
  - Classes: `ChatEngine`
  - Functions: `gentle_log_init`, `_load_json_config`, `_append_to_memory_journal`, `_log_reasoning_content`, `add_user_message`, `add_assistant_message`, `set_mode`, `_shape_response_by_mode`, `build_system_prompt`, `summarize_context`, `_check_and_trigger_summarization`, `detect_mode`, `_get_llm_client_for_model`, `_get_llm_client_for_mode`, `_classify_task`, `_measure_and_package_performance`, `get_response`, `_get_available_functions`, `_handle_function_calls`, `new_session_logic`, `new_session`, `_determine_model_id_for_request` (deprecated), `get_optimized_context`, `_run_daily_planning_cycle`, `_run_periodic_monitoring`, `start_autonomous_scheduler`, `shutdown_autonomous_scheduler`, `get_ade_goals`, `store_project_memory`, `save_decision`, `save_implementation_note`, `save_project_insight`, `generate_response`.
- **Flagged Items:** Contains placeholder comments (`# Placeholder`) and commented-out code indicating ongoing development or planned features. Imports `apscheduler` which was noted in a previous user message as having a minor stub warning.
- **Imports:** `json`, `logging`, `os`, `time`, `uuid`, `datetime`, `timezone`, `typing`, `apscheduler.schedulers.background.BackgroundScheduler`, `dotenv`, `.autonomous_agents`, `.core.memory`, `.covenant_enforcer`, `.llm_clients.factory`, `.memory_manager`, `.model_router`, `.sacred_trinity_router`, `.strategic_config`, `.utils`.

### File: `model_router.py`

- **Purpose:** Implements the `SacredModelRouter` for selecting the best LLM model based on task category, constraints, and strategic guidance.
- **Main Components:**
  - Enums: `ModelArchetype`
  - Dataclasses: `AugmentedModelConfig`
  - Classes: `SacredModelRouter`
  - Functions: `_load_models_config`, `get_model_config`, `select_model_with_sacred_guidance`, `calculate_combined_score`, `get_routing_stats`, `get_model_sacred_alignment`.
- **Flagged Items:** Contains placeholder logic and comments indicating ongoing development.
- **Imports:** `json`, `logging`, `os`, `random`, `time`, `dataclasses`, `enum`, `typing`, `src.strategic_config`.

### File: `agent_manager.py`

- **Purpose:** Initializes and manages various agents (e.g., MemoryAgent) and provides a method to run them.
- **Main Components:**
  - Classes: `AgentManager`
  - Functions: `__init__`, `run`
- **Flagged Items:** Requires `PINECONE_API_KEY` and `PINECONE_ENV` environment variables; raises ValueError if not set.
- **Imports:** `os`, `agents.memory_agent`.

### File: `trinity_evaluator.py`

- **Purpose:** Evaluates LLM responses based on Sacred Trinity principles (Wisdom, Compassion, Truth) and ranks models based on performance.
- **Main Components:**
  - Classes: `SacredTrinityEvaluator`
  - Functions: `__init__`, `wisdom_score`, `compassion_score`, `truth_score`, `evaluate_response`, `run_evaluation`, `export_results`, `update_config`.
- **Flagged Items:** Contains placeholder logic (`# Placeholder`) for scoring methods, integrating performance metrics, and model ranking.
- **Imports:** `logging`, `typing`, `json`, `os`.

### File: `covenant_enforcer.py`

- **Purpose:** Implements the `CovenantEnforcer` class to load `covenant.yaml` and enforce Sacred Covenant rules and Sacred Trinity principles by verifying actions and checking outputs.
- **Main Components:**
  - Classes: `CovenantEnforcer`
  - Functions: `__init__`, `_load_soulprint`, `_load_sacred_trinity_config`, `verify_action`, `request_human_oversight`, `check_output`, `_check_soulprint_alignment`, `_mentions_covenant_compliance`, `_check_trinity_alignment`, `_log_audit_event`.
- **Flagged Items:** Contains `TODO` comments and placeholder logic for implementing the actual covenant rule checks and Sacred Trinity alignment assessment.
- **Imports:** `yaml`, `json`, `logging`, `os`, `re`, `datetime`, `timezone`, `typing`. (Notes commented-out imports for `SacredTrinityRouter` and config paths).

### File: `memory_manager.py`

- **Purpose:** Manages Kor'tana's memory, including logging interactions to a journal file (`memory.jsonl`) and integrating with a vector database (Pinecone) for search.
- **Main Components:**
  - Classes: `MemoryManager`
  - Functions: `__init__`, `add_interaction`, `add`, `query`, `search`, `get_recent_memories`
- **Flagged Items:** Requires `PINECONE_API_KEY`; uses 'quickstart' Pinecone index (potentially temporary); uses deprecated LangChain imports; notes potential optimization for embedding generation and search relevance; contains commented-out example usage.
- **Imports:** `json`, `os`, `sys`, `datetime`, `timezone`, `typing`, `pathlib`, `langchain_openai.OpenAIEmbeddings` (or `langchain_community.embeddings`), `langchain_pinecone.Pinecone` (or `langchain_community.vectorstores`), `pinecone.Pinecone`, `pinecone.ServerlessSpec`, `logging`, `warnings`.

### File: `utils.py`

- **Purpose:** Provides shared utility functions for tasks like timestamp formatting, configuration handling, file operations, and placeholder logic for text analysis.
- **Main Components:**
  - Functions: `format_timestamp`, `validate_config`, `ensure_dir_exists`, `load_json_file`, `safe_write_jsonl`, `analyze_sentiment` (placeholder), `detect_emphasis_all_caps`, `detect_keywords`, `identify_important_message_for_context` (placeholder), `load_json_config`, `load_all_configs`.
- **Flagged Items:** Contains placeholder logic (`# Placeholder`, `Mock implementation`) for text analysis functions; includes commented-out example usage.
- **Imports:** `datetime`, `os`, `json`, `logging`, `typing`, `re`, `textblob`.

### File: `sacred_trinity_router.py`

- **Purpose:** Intended to route prompts to different LLM models based on their primary Sacred Trinity intent (Wisdom, Compassion, Truth).
- **Main Components:**
  - Classes: `SacredTrinityRouter`
  - Functions: `__init__`, `_load_model_mappings`, `analyze_prompt_intent`, `select_model_for_wisdom`, `select_model_for_compassion`, `select_model_for_truth`. Includes commented-out placeholders for `_get_model_instance`, `route_prompt`, `handle_model_failure`.
- **Flagged Items:** Contains placeholder logic (`Placeholder`) and commented-out methods, indicating incomplete implementation for prompt analysis, model selection, and integration with actual model instances/routing.
- **Imports:** `logging`, `typing`. (Notes commented-out import for `BaseLLMClient`).

### File: `autonomous_development_engine.py`

- **Purpose:** Implements the `AutonomousDevelopmentEngine` (ADE) for planning and executing development tasks using available tools and ensuring Sacred Covenant compliance.
- **Main Components:**
  - Dataclasses: `DevelopmentTask`
  - Classes: `AutonomousDevelopmentEngine`
  - Functions: `__init__`, `plan_development_session`, `execute_task`, `autonomous_development_cycle`, `_reflect_on_cycle`, various `_analyze_*`, `_generate_*`, `_refactor_*`, `_create_*`, `_document_*`, `_enhance_*`, `_implement_*` tool functions (many are placeholders), `emergency_self_repair`, `_covenant_approve_task`, `_log_to_memory`, `create_ade`, `MockMemoryManager`, `run_cli_command`.
- **Flagged Items:** Contains numerous placeholder tool functions (`# Implement actual logic`) and mock classes/functions, indicating significant ongoing development and incomplete features. Relies on an OpenAI client (`gpt-4.1-nano`) which may require specific setup.
- **Imports:** `json`, `logging`, `os`, `asyncio`, `datetime`, `timezone`, `typing`, `dataclasses`. (Notes imports of potentially missing `openai` due to function call structure, though not explicitly in imports).

### File: `strategic_config.py`

- **Purpose:** Implements the `UltimateLivingSacredConfig` class for managing strategic configuration, performance tracking, (placeholder) Sacred Trinity optimization, and providing task guidance for model selection.
- **Main Components:**
  - Enums: `TaskCategory`
  - Dataclasses: `PerformanceMetric`, `SacredPrinciple`
  - Classes: `UltimateLivingSacredConfig`
  - Functions: `__init__`, `_load_performance_history`, `_save_performance_history`, `update_performance_data`, `optimize_sacred_trinity` (placeholder), `get_task_guidance`, `get_model_sacred_scores`, `get_model_archetype_fits`.
- **Flagged Items:** Contains placeholder logic for `optimize_sacred_trinity`; notes initial scores are stored internally due to past file edit issues; includes commented-out history window limiting and example usage.
- **Imports:** `json`, `os`, `time`, `numpy`, `datetime`, `typing`, `dataclasses`, `enum`, `logging`.

### File: `model_resolver.py`

- **Purpose:** Implements the `ModelResolver` class for resolving model aliases and verifying required models for the autonomous repair system, including an XAI integration test.
- **Main Components:**
  - Classes: `ModelResolver`
  - Functions: `__init__`, `_load_config`, `resolve_model_id`, `get_model_config`, `get_available_models`, `verify_autonomous_models`, `test_xai_integration`.
- **Flagged Items:** Requires specific models and potentially API keys for verification and testing (e.g., `grok-3-mini-reasoning`, XAI API key).
- **Imports:** `json`, `logging`, `typing`. (Notes import of `os` inside a function and a commented-out import for `llm_clients.xai_client`).

### File: `model_optimizer.py`

- **Purpose:** Implements the `ModelOptimizer` for selecting models based on conversation context, cost efficiency, usage patterns, and (simulated) external model performance data.
- **Main Components:**
  - Dataclasses: `ModelPerformance`, `ConversationContext`
  - Classes: `ModelOptimizer`
  - Functions: `__init__`, `_load_config`, `select_optimal_model`, `estimate_cost`, `_is_budget_exceeded`, `_get_budget_model`, `track_usage`, `get_optimization_recommendations`, `generate_daily_report`.
- **Flagged Items:** Uses simulated/hardcoded external data (from `llm-stats.com`); includes example usage in `if __name__ == "__main__":` block.
- **Imports:** `json`, `logging`, `typing`, `dataclasses`, `datetime`, `timedelta`.

### File: `api_server.py`

- **Purpose:** Sets up a FastAPI web server to provide API endpoints for interacting with Kor'tana's `ChatEngine`, including chat, health checks, mode management, and potential WebSocket and ADE trigger endpoints.
- **Main Components:**
  - Classes: `MessageRequest`, `MessageResponse`, `CsrfSettings`
  - Functions: `chat_endpoint`, `kortana_chat_alias`, `health_check`, `get_mode`, `set_mode`, `openai_compatible_chat`, `chat_sse`, `trigger_ade`, `login`, `websocket_endpoint`.
  - FastAPI instance: `app`
  - Limiter instance: `limiter`
  - Singleton `ChatEngine` instance: `engine`
- **Flagged Items:** CSRF protection import is commented out, indicating it might not be active or fully integrated; dummy authentication logic in `/login` needs replacement; placeholder logic in `chat_sse`. Logs raw request body and parsed payload at INFO level, which might be overly verbose or sensitive.
- **Imports:** `logging`, `json`, `fastapi`, `fastapi.middleware.cors.CORSMiddleware`, `pydantic`, `typing`, `uvicorn`, `os`, `sys`, `datetime`, `sse_starlette.sse.EventSourceResponse`, `fastapi.responses.JSONResponse`, `bleach`, `fastapi_csrf_protect.CsrfProtect` (commented out), `slowapi.Limiter`, `slowapi.util.get_remote_address`, `slowapi.errors.RateLimitExceeded`, `.brain`.

### File: `ade_coordinator.py`

- **Purpose:** Coordinates the `AutonomousDevelopmentEngine` with existing agents within the `ChatEngine` to manage and execute autonomous development goals.
- **Main Components:**
  - Classes: `ADECoordinator`
  - Functions: `__init__`, `start_autonomous_session`, `add_development_goal`.
- **Flagged Items:** Relies on attributes of the `ChatEngine` instance (e.g., `llm_clients`, `covenant_enforcer`, `memory_manager`, existing ADE agent instances) which implies a tight coupling and potential dependencies on `ChatEngine`'s internal structure.
- **Imports:** `asyncio`, `logging`, `datetime`, `timezone`, `typing`, `autonomous_development_engine`, `autonomous_agents`.

### File: `dev_agent.py`

- **Purpose:** Appears to be an older or simplified implementation of a development agent using LangChain with a specific OpenAI model and basic tools.
- **Main Components:**
  - Function: `execute_dev_task`
  - LangChain agent initialization: `dev_agent`
  - Tools list: `tools`
- **Flagged Items:** Contains a `TODO` comment regarding tool integration; relies on `XAI_API_KEY`; potentially superseded by `autonomous_development_engine.py`; uses `langchain_openai` which might require specific setup.
- **Imports:** `os`, `langchain.agents`, `langchain_openai.OpenAI`.

### File: `dev_text_completion.py`

- **Purpose:** A simple script for manually testing text completion and image analysis using the OpenAI client.
- **Main Components:** Directly uses `OpenAIClient`, takes user input for prompts and image URLs.
- **Flagged Items:** Requires `OPENAI_API_KEY`; appears to be a temporary development/testing script.
- **Imports:** `os`, `llm_clients.openai_client`, `dotenv`.

### File: `__init__.py`

- **Purpose:** Marks the `src` directory as a Python package.
- **Main Components:** None (contains only comments).
- **Flagged Items:** None.
- **Imports:** None.

### File: `covenant.py`

- **Purpose:** Implements the `CovenantEnforcer` class to load and enforce Sacred Covenant rules, core Soulprint values, and memory principles by validating outputs, memory writes, and autonomous actions, and by logging events and oversight requests.
- **Main Components:**
  - Classes: `CovenantEnforcer`
  - Functions: `__init__`, `_load_core_values`, `_log_audit_event`, `check_output`, `_check_soulprint_alignment`, `_mentions_covenant_compliance`, `check_memory_write`, `check_autonomous_action`, `verify_action`, `request_human_oversight`, `_check_sovereignty_rules`, `_check_symbiosis_protocols`, `_check_integrity_rules`, `_aligns_with_core_values`, `_assess_concern_severity`, `_requires_immediate_attention`, `get_audit_trail`, `get_oversight_queue`, `approve_action`.
- **Flagged Items:** Assumes `covenant.yaml`, `persona.json`, and `memory.md` exist in the project root; contains detailed logic for various covenant checks, some of which may rely on specific formatting or content in the configuration files.
- **Imports:** `os`, `yaml`, `json`, `re`, `datetime`, `typing`.

### File: `project_memory.jsonl`

- **Purpose:** A data file used to store Kor'tana's memory entries (decisions, context summaries, etc.) in JSON Lines format.
- **Main Components:** Contains individual JSON objects per line, representing memory entries.
- **Flagged Items:** Contains example entries and comments describing the format.
- **Imports:** N/A (data file).

## Directory: `src/llm_clients/`

### File: `__init__.py`

- **Purpose:** Marks the `llm_clients` directory as a Python package and potentially handles imports for the package.
- **Main Components:** Imports various client classes.
- **Flagged Items:** None.
- **Imports:** `._init_clients`, `.base_client`, `.openai_client`, `.gemini_client`, `.google_client`, `.openrouter_client`, `.xai_client`, `.llama_client`, `.grok_client`, `.factory`.

### File: `openai_client.py`

- **Purpose:** Implements a client for interacting with the OpenAI API using the official SDK, providing `BaseLLMClient` compatibility and supporting features like function calling, streaming, cost estimation, and connection validation.
- **Main Components:**
  - Classes: `OpenAIClient` (inherits `BaseLLMClient`), `ChatNamespace`, `ChatCompletions`.
  - Methods for response generation, capabilities, validation, cost estimation.
- **Flagged Items:** Requires `OPENAI_API_KEY`; includes estimated pricing data that may need updating; includes internal classes (`ChatNamespace`, `ChatCompletions`) that seem intended for compatibility with ADE calling patterns.
- **Imports:** `json`, `logging`, `os`, `typing`, `openai`, `openai.types.chat.ChatCompletionUserMessageParam`, `.base_client`.

### File: `genai_client.py`

- **Purpose:** Implements a client for interacting with Google Gemini models using the `google.generativeai` library, providing `BaseLLMClient` compatibility.
- **Main Components:**
  - Classes: `GoogleGenAIClient` (inherits `BaseLLMClient`).
  - Methods for initialization, API key handling, model validation, listing models, response generation (with `generation_config`), capabilities, connection validation, cost estimation.
- **Flagged Items:** Requires `GOOGLE_API_KEY`; includes basic cost estimation that needs updating; logs detailed initialization and request info.
- **Imports:** `logging`, `os`, `subprocess`, `typing`, `google.generativeai`, `google.generativeai.types.GenerationConfig`, `.base_client`.

### File: `factory.py`

- **Purpose:** Implements the `LLMClientFactory` for creating instances of various LLM clients based on model configuration, centralizing client creation and API key handling.
- **Main Components:**
  - Classes: `LLMClientFactory`.
  - Static methods: `create_client`, `get_client_for_model`, `get_default_client`, `get_ade_client`, `validate_configuration`.
  - Dictionary: `MODEL_CLIENTS` (maps model IDs to client classes).
- **Flagged Items:** Requires configuration in `models_config.json` and corresponding API keys in environment variables; `MODEL_CLIENTS` mapping needs to be kept up-to-date with available clients and models.
- **Imports:** `logging`, `os`, `typing`, `.base_client`, `.genai_client`, `.openai_client`, `.openrouter_client`, `.xai_client`.

### File: `base_client.py`

- **Purpose:** Defines the abstract base class `BaseLLMClient`, establishing a standard interface for all LLM provider implementations in Kor'tana.
- **Main Components:**
  - Abstract Class: `BaseLLMClient`.
  - Abstract Methods: `generate_response`, `get_capabilities`, `test_connection`, `estimate_cost`.
  - Concrete Methods: `__init__`, `generate_response_with_retry`.
  - Optional Methods: `supports_function_calling`, `supports_streaming`, `get_model_info`.
- **Flagged Items:** Implementations of abstract methods are required in derived classes; `generate_response_with_retry` provides a basic retry mechanism but might need more sophisticated error handling.
- **Imports:** `logging`, `time`, `abc`, `typing`.

### File: `openrouter_client.py`

- **Purpose:** Implements a client for the OpenRouter API, which acts as an OpenAI-compatible proxy service to access various models.
- **Main Components:**
  - Classes: `OpenRouterClient` (inherits `BaseLLMClient`).
  - Methods for initialization, response generation, capabilities, cost estimation, connection testing.
- **Flagged Items:** Requires OpenRouter API key; uses `httpx` for the underlying client; cost estimation relies on values passed during initialization; contains internal poetic/flavor text.
- **Imports:** `openai`, `httpx`, `logging`, `typing`, `.base_client`.

### File: `gemini_client.py`

- **Purpose:** Implements a client for interacting with Google Gemini models using the `google.generativeai` library, providing `BaseLLMClient` compatibility. Appears very similar to `gemini_client_fixed.py` and has overlapping functionality with `genai_client.py`.
- **Main Components:**
  - Classes: `GoogleGenAIClient` (inherits `BaseLLMClient`).
  - Methods for initialization, response generation, streaming, capabilities, connection testing, model info.
- **Flagged Items:** Requires `GOOGLE_API_KEY`; potential duplicate or superseded file.
- **Imports:** `logging`, `os`, `time`, `typing`, `google.generativeai`, `.base_client`.

### File: `google_client.py`

- **Purpose:** Implements a client for interacting with Google Gemini models using the `google.generativeai` library, optimized for Flash models and potentially free tier usage with built-in rate limiting. Provides `BaseLLMClient` compatibility.
- **Main Components:**
  - Classes: `GoogleGeminiClient` (inherits `BaseLLMClient`).
  - Methods for initialization, rate limiting, response generation, capabilities, connection testing, cost estimation (flagged as free tier).
- **Flagged Items:** Requires `GOOGLE_API_KEY`; includes hardcoded RPM limits for specific models; implements rate limiting logic; potential duplication or overlap with `gemini_client.py`, `gemini_client_fixed.py`, and `genai_client.py`.
- **Imports:** `json`, `logging`, `os`, `time`, `typing`, `google.generativeai`, `google.generativeai.types`, `.base_client`.

### File: `xai_client.py`

- **Purpose:** Implements a client for XAI (Grok) models, using an OpenAI-compatible structure, specialized for autonomous development and reasoning tasks.
- **Main Components:**
  - Classes: `XAIClient` (inherits `BaseLLMClient`).
  - Methods for initialization, response generation, capabilities, connection validation, cost estimation.
- **Flagged Items:** Requires `XAI_API_KEY`; uses the `openai` library internally; includes estimated pricing based on OpenRouter; contains debug logging.
- **Imports:** `logging`, `os`, `json`, `typing`, `.base_client`.

### File: `llama_client.py`

- **Purpose:** Provides a placeholder client for interacting with Llama-based models.
- **Main Components:**
  - Classes: `LlamaClient` (inherits `BaseLLMClient`).
- **Flagged Items:** Contains placeholder comments; specific implementation logic is missing.
- **Imports:** `.base_client`.

### File: `grok_client.py`

- **Purpose:** Implements a client for xAI's Grok models using an OpenAI-compatible structure, noted for reasoning capabilities.
- **Main Components:**
  - Classes: `GrokClient` (inherits `BaseLLMClient`).
  - Methods for initialization, response generation (attempts to capture `reasoning_content`), capabilities, cost estimation (placeholder), connection testing.
- **Flagged Items:** Potential overlap with `xai_client.py`; cost estimation is a placeholder; context window size might need adjustment based on actual model; attempts to handle a specific `reasoning_content` field.
- **Imports:** `.base_client`, `openai`, `httpx`, `logging`, `typing`.

### File: `xai_grok_client.py`

- **Purpose:** Appears to be an early or incomplete client implementation for XAI Grok models.
- **Main Components:**
  - Classes: `XAIGrokClient`.
  - Methods: `__init__`, `authenticate` (simulated), `send_message` (placeholder), `get_completion` (attempts API call with uninitialized client).
- **Flagged Items:** Contains simulated and placeholder logic; attempts to use an uninitialized client in `get_completion`; potential overlap/superseded by `xai_client.py` and `grok_client.py`.
- **Imports:** `logging`, `time`, `typing`.

## Directory: `src/core/`

### File: `memory.py`

- **Purpose:** Provides functions for loading, saving, and retrieving memory entries from `project_memory.jsonl`, supporting different memory entry types.
- **Main Components:**
  - Functions: `load_memory`, `save_memory`, `save_decision`, `save_context_summary`, `save_implementation_note`, `save_project_insight`, `get_memory_by_type`, `get_recent_memories_by_type`.
  - Constant: `MEMORY_FILE`.
- **Flagged Items:** Hardcoded path for `project_memory.jsonl` relative to the file's location, which might be fragile; includes commented-out example usage.
- **Imports:** `json`, `os`, `sys`, `datetime`, `timezone`, `typing`.

## Directory: `kortana.core/`

### File: `memory.md`

- **Purpose:** [Analyzing...]
- **Main Components:** [Analyzing...]
- **Flagged Items:** [Analyzing...]
- **Imports:** N/A (markdown file).
