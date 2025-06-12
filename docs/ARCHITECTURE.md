# Kor'tana Architecture Overview

This document outlines the high-level architecture of the Kor'tana AI agent system.

## Core Components

- **FastAPI Application (`src/kortana/main.py`):** The main entry point, serving API endpoints.
- **Database (`src/kortana/services/database.py`):** Manages database connections (SQLite for now) and sessions using SQLAlchemy.
- **Alembic (`src/kortana/migrations`):** Handles database schema migrations.
- **Configuration (`src/kortana/config`):** Manages application settings using Pydantic models, loaded from `.env` and `config.yaml`.

## Modules

### 1. Memory Core (`src/kortana/modules/memory_core`)
   - **Purpose:** Stores, retrieves, and manages Kor'tana's experiences, learned information, and identity facets.
   - **`models.py`:** SQLAlchemy models (`CoreMemory`, `MemorySentiment`, `MemoryType` enum) defining the structure of memories.
   - **`schemas.py`:** Pydantic schemas for data validation and API serialization.
   - **`services.py` (`MemoryCoreService`):** Business logic for CRUD operations on memories. Integrates with `EmbeddingService` to store vector embeddings alongside memories. Includes a basic brute-force semantic search.
   - **`routers/memory_router.py`:** FastAPI endpoints for direct memory manipulation (`/memories`).

### 2. Ethical Discernment Module (EDM) (`src/kortana/modules/ethical_discernment_module`)
   - **Purpose:** Ensures Kor'tana's operations align with predefined ethical principles.
   - **`evaluators.py`:** Contains stubs for `AlgorithmicArroganceEvaluator` and `UncertaintyHandler`. These will be expanded to actively monitor and guide Kor'tana's responses.

### 3. Core Logic (`src/kortana/core`)

   #### `orchestrator.py` - The KorOrchestrator
   The `KorOrchestrator` (`src/kortana/core/orchestrator.py`) is the central processing unit of Kor'tana. It manages the primary information processing pipeline.

   **Core Information Flow:**
   The orchestrator processes a user query through the following steps:
     1. **User Query Input:** Receives the initial query.
     2. **Embedding Generation:** Uses the `EmbeddingService` to convert the query into a vector embedding.
     3. **Semantic Memory Search:** Queries the `MemoryCoreService` using the embedding to find relevant memories.
     4. **LLM Interaction (Stubbed):** Prepares a prompt (including query and retrieved context) for an external Large Language Model and simulates receiving a response.
     5. **Ethical Evaluation:** The (stubbed) LLM response is assessed by evaluators from the `EthicalDiscernmentModule` (e.g., `AlgorithmicArroganceEvaluator`, `UncertaintyHandler`).
     6. **Final Response Formulation:** Constructs Kor'tana's final, contextually-aware, and ethically-guided response.

   This flow is directly utilized by the API endpoint detailed below.

   - **`routers/core_router.py`:** FastAPI endpoint (`/core/query`) that exposes the `KorOrchestrator`'s functionality.

### 4. Services (`src/kortana/services`)
   - **`embedding_service.py` (`EmbeddingService`):** Responsible for generating vector embeddings for text using an external provider (e.g., OpenAI). This is crucial for semantic search capabilities.
   - **(Future) `llm_service.py`:** Will manage interactions with various Large Language Models.

## Data Flow for a Query

1. User sends a query to the `/core/query` API endpoint.
2. `core_router.py` passes the query to `KorOrchestrator.process_query()`.
3. `KorOrchestrator` uses `EmbeddingService` to get an embedding for the query.
4. `KorOrchestrator` calls `MemoryCoreService.search_memories_semantic()` with the query embedding.
   - `MemoryCoreService` (currently) iterates through all memories, calculates cosine similarity between the query embedding and each stored memory's embedding, and returns the top N matches.
5. `KorOrchestrator` (currently) simulates an LLM call using the query and retrieved memory context.
6. The simulated LLM response is evaluated by the `AlgorithmicArroganceEvaluator` and `UncertaintyHandler` from the EDM.
7. `KorOrchestrator` constructs and returns the final response, which includes details from each step of the process.

## Key Technologies

- Python 3.11+
- FastAPI: For building the web API.
- SQLAlchemy: For ORM and database interaction.
- Alembic: For database migrations.
- Pydantic: For data validation and settings management.
- Langchain (specifically `langchain-openai`): For interacting with OpenAI embedding models.
- Numpy: For numerical operations, particularly cosine similarity in the current semantic search implementation.
- Sentence-Transformers (optional, for local embeddings in the future).

## Future Optimizations & Considerations

- **Semantic Search:** The current brute-force semantic search in `MemoryCoreService` is inefficient. This will be replaced with a dedicated vector database (e.g., Pinecone, Weaviate, ChromaDB) or a database extension like `pgvector` for PostgreSQL for scalable and fast similarity searches.
- **LLM Integration:** The `llm_service` will be fully implemented to support various LLMs and manage prompt engineering, response parsing, and error handling.
- **Ethical Discernment Module:** The EDM stubs will be fleshed out with more sophisticated evaluation logic and intervention strategies.
- **Asynchronous Operations:** Ensure all I/O-bound operations (database calls, external API calls) are properly asynchronous to maintain API responsiveness.
