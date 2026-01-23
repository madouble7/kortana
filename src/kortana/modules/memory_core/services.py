import numpy as np
from sqlalchemy.orm import Session, joinedload

from kortana.services.embedding_service import embedding_service

from . import models, schemas


# A simple cosine similarity function
def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    # Handle zero vectors to avoid division by zero
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return np.dot(v1, v2) / (norm_v1 * norm_v2)


class MemoryCoreService:
    def __init__(self, db: Session):
        self.db = db

    def create_memory(
        self, memory_create: schemas.CoreMemoryCreate
    ) -> models.CoreMemory:
        """
        Creates a new memory, generates its embedding, and stores it.
        """
        # Generate embedding for the memory's content
        text_to_embed = memory_create.content
        if memory_create.title:
            # Combining title and content can create a richer embedding
            text_to_embed = f"{memory_create.title}\n\n{memory_create.content}"

        generated_embedding = embedding_service.get_embedding_for_text(text_to_embed)

        db_memory_data = memory_create.model_dump(exclude={"sentiments"})
        db_memory = models.CoreMemory(
            **db_memory_data,
            embedding=generated_embedding,  # Add the embedding
        )

        # Handle sentiments
        if memory_create.sentiments:
            for sentiment_create in memory_create.sentiments:
                models.MemorySentiment(
                    **sentiment_create.model_dump(),
                    memory=db_memory,  # Sentiment added via relationship cascade
                )

        self.db.add(db_memory)
        self.db.commit()
        self.db.refresh(db_memory)
        return db_memory

    def get_memory_by_id(self, memory_id: int) -> models.CoreMemory | None:
        """
        Retrieves a specific memory by its ID, including its sentiments.
        Updates accessed_at timestamp via SQLAlchemy's onupdate.
        """
        memory = (
            self.db.query(models.CoreMemory)
            .options(joinedload(models.CoreMemory.sentiments))
            .filter(models.CoreMemory.id == memory_id)
            .first()
        )
        return memory

    def get_all_memories(
        self, skip: int = 0, limit: int = 100
    ) -> list[models.CoreMemory]:
        """
        Retrieves a list of memories with pagination, including sentiments.
        """
        return (
            self.db.query(models.CoreMemory)
            .options(joinedload(models.CoreMemory.sentiments))
            .order_by(models.CoreMemory.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_memory(
        self, memory_id: int, memory_update: schemas.CoreMemoryUpdate
    ) -> models.CoreMemory | None:
        """
        Updates an existing memory.
        """
        db_memory = self.get_memory_by_id(memory_id)
        if not db_memory:
            return None
        update_data = memory_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_memory, key, value)
        self.db.commit()
        self.db.refresh(db_memory)
        return db_memory

    def delete_memory(self, memory_id: int) -> models.CoreMemory | None:
        """
        Deletes a memory by its ID.
        """
        db_memory = (
            self.db.query(models.CoreMemory)
            .filter(models.CoreMemory.id == memory_id)
            .first()
        )
        if not db_memory:
            return None
        self.db.delete(db_memory)
        self.db.commit()
        return db_memory

    def search_memories_semantic(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Performs a semantic search for memories based on a text query.

        Note: This is a brute-force implementation for demonstration. It's inefficient
        and will be slow with many memories. A real implementation would use a vector
        database (e.g., Pinecone, Weaviate) or a DB extension (pgvector).
        """
        print(f"Performing brute-force semantic search for query: '{query}'")
        query_embedding = embedding_service.get_embedding_for_text(query)
        if not query_embedding:
            return []

        # Fetch all memories with embeddings from the database
        # Ensure embeddings are not None
        all_memories = (
            self.db.query(models.CoreMemory)
            .filter(models.CoreMemory.embedding.isnot(None))
            .all()
        )

        if not all_memories:
            return []

        # Calculate similarity for each memory
        scored_memories = []
        for mem in all_memories:
            # Ensure mem.embedding is a list of floats before calculating similarity
            if (
                mem.embedding is not None
                and isinstance(mem.embedding, list)
                and all(isinstance(x, int | float) for x in mem.embedding)
            ):
                similarity = cosine_similarity(query_embedding, mem.embedding)
                scored_memories.append({"memory": mem, "score": similarity})

        # Sort by similarity score in descending order and take the top_k
        sorted_memories = sorted(
            scored_memories, key=lambda x: x["score"], reverse=True
        )

        return sorted_memories[:top_k]
