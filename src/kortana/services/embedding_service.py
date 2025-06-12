from langchain_openai import OpenAIEmbeddings

from kortana.config.settings import settings


class EmbeddingService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY must be set in the environment to use EmbeddingService."
            )

        # Choose your model. "text-embedding-3-small" is cost-effective and performs well.
        self.client = OpenAIEmbeddings(
            model="text-embedding-3-small", openai_api_key=settings.OPENAI_API_KEY
        )
        print("EmbeddingService initialized with OpenAI text-embedding-3-small.")

    def get_embedding_for_text(self, text: str) -> list[float]:
        """Generates a vector embedding for a single piece of text."""
        if not text or not text.strip():
            return []  # Or raise an error
        return self.client.embed_query(text)

    def get_embeddings_for_texts(self, texts: list[str]) -> list[list[float]]:
        """Generates vector embeddings for a batch of texts."""
        # Filter out empty strings to avoid errors with the API
        non_empty_texts = [text for text in texts if text and text.strip()]
        if not non_empty_texts:
            return []
        return self.client.embed_documents(non_empty_texts)


# Singleton instance for easy access across the application
embedding_service = EmbeddingService()

# Example for direct testing
if __name__ == "__main__":
    # More robust testing block from the blueprint
    if embedding_service:
        test_text = "Kor'tana is remembering."
        try:
            embedding = embedding_service.get_embedding_for_text(test_text)
            if embedding:
                print(f"Generated embedding for '{test_text}'")
                print(f"Vector dimension: {len(embedding)}")
                print(f"First 5 dimensions: {embedding[:5]}")
            else:
                print(f"Could not generate embedding for '{test_text}'.")
        except Exception as e:
            print(f"Error during embedding generation: {e}")
    else:
        # This case might occur if OPENAI_API_KEY is not set and the class instantiation fails.
        # The current EmbeddingService class raises ValueError, so this 'else' might not be hit
        # if the script exits. However, if instantiation was try-excepted and set to None, this would be relevant.
        print(
            "EmbeddingService not available for testing. Ensure OPENAI_API_KEY is set."
        )
