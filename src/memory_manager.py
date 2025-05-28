try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    from langchain_community.embeddings import OpenAIEmbeddings
    import warnings
    warnings.warn("OpenAIEmbeddings from langchain_community is deprecated. Please install langchain-openai.")
from langchain_pinecone import Pinecone
from pinecone import Pinecone as PineconeClient, ServerlessSpec
import os
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        self.pc = PineconeClient(api_key=os.getenv("PINECONE_API_KEY"))
        # Use the correct region for your Pinecone project (free plan: us-east1-gcp)
        # Use the existing 'quickstart' index to unblock development
        index_name = "quickstart"  # Change to your preferred index name later
        region = "us-east1-gcp"
        try:
            # Check if index exists, create if missing
            if index_name not in [idx.name for idx in self.pc.list_indexes()]:
                self.pc.create_index(
                    name=index_name,
                    dimension=1536,  # adjust if your embedding size is different
                    metric='euclidean',
                    spec=ServerlessSpec(cloud="gcp", region=region)
                )
                logger.info(f"Created Pinecone index '{index_name}' in region '{region}'.")
        except Exception as e:
            logger.error(f"Failed to create or connect to Pinecone index: {e}")
        try:
            # Get the actual Index object (Pinecone v3+)
            index = self.pc.Index(index_name)
            self.index = Pinecone(
                index=index,
                embedding=OpenAIEmbeddings(model="text-embedding-ada-002"),
                text_key="text"  # Required for latest LangChain Pinecone integration
            )
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone vectorstore: {e}")
            self.index = None

    def add(self, id: str, text: str, metadata: dict):
        if not self.index:
            logger.warning("Pinecone index is not initialized. Skipping add.")
            return
        emb = OpenAIEmbeddings().embed_query(text)
        self.index.add_texts([text], ids=[id], metadatas=[metadata])

    def query(self, text: str, k: int = 5):
        if not self.index:
            logger.warning("Pinecone index is not initialized. Returning empty result.")
            return []
        return self.index.similarity_search_with_score(text, k=k)

    def search(self, query, limit=5):
        """Search recent memories for those containing the query string (case-insensitive)."""
        try:
            memories = self.get_recent_memories(limit=50)
            relevant = [m for m in memories if m.get('content') and query.lower() in m.get('content', '').lower()]
            return relevant[:limit]
        except Exception as e:
            print(f"Memory search error: {e}")
            return []

    def get_recent_memories(self, limit=50):
        """Read the last N user/assistant messages from memory.jsonl."""
        memory_path = Path(__file__).parent.parent / 'data' / 'memory.jsonl'
        if not memory_path.exists():
            return []
        lines = memory_path.read_text(encoding='utf-8').splitlines()
        memories = []
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                if entry.get('role') in ('user', 'assistant'):
                    memories.append(entry)
                if len(memories) >= limit:
                    break
            except Exception:
                continue
        return list(reversed(memories)) 