"""
Vector Store implementation for Kor'tana semantic search and memory retrieval.
Uses ChromaDB for vector storage and sentence-transformers for embeddings.
"""

import os
from datetime import datetime
from typing import (
    Any,  # Maintained for _embedding_model_instance until SentenceTransformer type is fully resolved by import
)

# Global cache for the SentenceTransformer class and any import error
_SENTENCE_TRANSFORMER_CLASS: Any | None = None
_SENTENCE_TRANSFORMER_IMPORT_ERROR: ImportError | None = None

try:
    import chromadb

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️ chromadb library not available. Install with: pip install chromadb")


class VectorStore:
    """
    Vector storage and semantic search for Kor'tana memory system.
    """

    def __init__(
        self,
        collection_name: str = "kortana_memories",
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.collection_name = collection_name
        self.model_name = model_name
        self._embedding_model_instance: Any | None = None
        self.client: Any | None = None  # chromadb.Client | None - Using Any for now
        self.collection: Any | None = (
            None  # chromadb.Collection | None - Using Any for now
        )

        if not CHROMADB_AVAILABLE:
            print(
                "ChromaDB not available, VectorStore initialized without client/collection."
            )
            return

        vector_store_path = "data/vector_store"
        os.makedirs(vector_store_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=vector_store_path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"description": "Kor'tana memory embeddings"}
        )

    def _get_embedding_model(self) -> Any:
        global _SENTENCE_TRANSFORMER_CLASS, _SENTENCE_TRANSFORMER_IMPORT_ERROR
        if self._embedding_model_instance is not None:
            return self._embedding_model_instance
        if (
            _SENTENCE_TRANSFORMER_CLASS is None
            and _SENTENCE_TRANSFORMER_IMPORT_ERROR is None
        ):
            try:
                from sentence_transformers import SentenceTransformer

                _SENTENCE_TRANSFORMER_CLASS = SentenceTransformer
                print(
                    "Successfully imported SentenceTransformer class for vector_store."
                )
            except ImportError as e:
                _SENTENCE_TRANSFORMER_IMPORT_ERROR = e
                print(
                    f"⚠️ Failed to import SentenceTransformer for vector_store: {e}. Install with: pip install sentence-transformers"
                )
        if _SENTENCE_TRANSFORMER_IMPORT_ERROR is not None:
            raise ImportError(
                "SentenceTransformer library not available for vector_store."
            ) from _SENTENCE_TRANSFORMER_IMPORT_ERROR
        if _SENTENCE_TRANSFORMER_CLASS is not None:
            print(
                f"Lazy loading SentenceTransformer model ('{self.model_name}') for vector_store."
            )
            self._embedding_model_instance = _SENTENCE_TRANSFORMER_CLASS(
                self.model_name
            )
            return self._embedding_model_instance
        raise RuntimeError("SentenceTransformer class could not be loaded.")

    def add_memory(
        self, memory_id: str, content: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        if not self.collection:
            print("❌ Error adding memory: VectorStore collection not initialized.")
            return False
        try:
            model = self._get_embedding_model()
            embedding = model.encode(content).tolist()
            full_metadata = {
                "timestamp": datetime.now().isoformat(),
                "content_length": len(content),
                **(metadata or {}),
            }
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[full_metadata],
                ids=[memory_id],
            )
            return True
        except Exception as e:
            print(f"❌ Error adding memory to vector store: {e}")
            return False

    def search_memories(
        self,
        query: str,
        n_results: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if not self.collection:
            print(
                "❌ Error searching memories: VectorStore collection not initialized."
            )
            return []
        try:
            model = self._get_embedding_model()
            query_embedding = model.encode(query).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=metadata_filter,
            )
            formatted_results: list[dict[str, Any]] = []
            if (
                results
                and isinstance(results.get("ids"), list)
                and results["ids"]
                and isinstance(results["ids"][0], list)
            ):
                ids_list_of_lists = results["ids"]
                if not ids_list_of_lists or not ids_list_of_lists[0]:
                    return []

                ids_actual_list = ids_list_of_lists[0]
                docs_list_of_lists = results.get("documents")
                metadatas_list_of_lists = results.get("metadatas")
                distances_list_of_lists = results.get("distances")

                docs_actual_list = (
                    docs_list_of_lists[0]
                    if docs_list_of_lists and isinstance(docs_list_of_lists[0], list)
                    else []
                )
                metadatas_actual_list = (
                    metadatas_list_of_lists[0]
                    if metadatas_list_of_lists
                    and isinstance(metadatas_list_of_lists[0], list)
                    else []
                )
                distances_actual_list = (
                    distances_list_of_lists[0]
                    if distances_list_of_lists
                    and isinstance(distances_list_of_lists[0], list)
                    else []
                )

                for i, mem_id in enumerate(ids_actual_list):
                    res_item: dict[str, Any] = {"id": mem_id}
                    if i < len(docs_actual_list):
                        res_item["content"] = docs_actual_list[i]
                    if i < len(metadatas_actual_list):
                        res_item["metadata"] = metadatas_actual_list[i]
                    if i < len(distances_actual_list):
                        res_item["distance"] = distances_actual_list[i]
                    formatted_results.append(res_item)
            return formatted_results
        except Exception as e:
            print(f"❌ Error searching memories in vector store: {e}")
            return []

    def get_collection_stats(self) -> dict[str, Any]:
        if not self.collection:
            return {"error": "VectorStore collection not initialized."}
        try:
            count = self.collection.count()
            collection_id = str(self.collection.id)
            return {"name": self.collection_name, "count": count, "id": collection_id}
        except Exception as e:
            print(f"❌ Error getting collection stats: {e}")
            return {"error": str(e)}


if __name__ == "__main__":
    import json

    print("Attempting to initialize VectorStore...")
    try:
        store = VectorStore(collection_name="test_collection_lazy_final")
        print("VectorStore initialized for testing.")

        if store.client is None or store.collection is None:
            print(
                "ChromaDB client or collection not initialized. Skipping further tests."
            )
        else:
            print(
                f"Initial stats: {json.dumps(store.get_collection_stats(), indent=2)}"
            )
            print("\nAttempting to add a memory...")
            add1 = store.add_memory(
                "lazy_final_1",
                "Memory about final lazy loading test.",
                {"tag": "final"},
            )
            add2 = store.add_memory(
                "lazy_final_2", "Another memory for the final test.", {"tag": "final"}
            )
            print(f"Memories added: {add1}, {add2}")
            print(
                f"Stats after add: {json.dumps(store.get_collection_stats(), indent=2)}"
            )
            print("\nAttempting to search memories...")
            search_res = store.search_memories("final test")
            print(f"Search results: {json.dumps(search_res, indent=2)}")
            print("\nCleaning up test_collection_lazy_final...")
            store.client.delete_collection("test_collection_lazy_final")
            print("Test collection deleted.")

    except ImportError as e:
        print(f"Import error during example usage: {e}")
    except Exception as e:
        print(f"An error occurred during example usage: {e}")
