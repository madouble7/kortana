import json
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    from langchain_community.embeddings import OpenAIEmbeddings
    import warnings
    warnings.warn("OpenAIEmbeddings from langchain_community is deprecated. Please install langchain-openai.")
try:
    from langchain_pinecone import Pinecone
except ImportError:
    from langchain_community.vectorstores import Pinecone
    import warnings
    warnings.warn("Pinecone from langchain_community is deprecated. Please install langchain-pinecone.")
from pinecone import Pinecone as PineconeClient, ServerlessSpec
import logging

logger = logging.getLogger(__name__)

# Adjust the MEMORY_JOURNAL_PATH to be relative to the project root
MEMORY_JOURNAL_PATH = Path(__file__).parent.parent / 'data' / 'memory.jsonl' # Corrected path

# Ensure the data directory exists
os.makedirs(MEMORY_JOURNAL_PATH.parent, exist_ok=True)

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
            logger.info(f"Pinecone vectorstore initialized with index '{index_name}'.")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone vectorstore: {e}")
            self.index = None

    def add_interaction(self, user_input: str, assistant_response: str, metadata: Optional[Dict[str, Any]] = None):
        """Logs a user-assistant interaction to the memory journal with metadata."""
        timestamp = datetime.now(timezone.utc).isoformat()
        user_entry = {"role": "user", "content": user_input, "timestamp_utc": timestamp, "metadata": metadata or {}}
        assistant_entry = {"role": "assistant", "content": assistant_response, "timestamp_utc": timestamp, "metadata": metadata or {}}

        try:
            with open(MEMORY_JOURNAL_PATH, 'a', encoding='utf-8') as f:
                json.dump(user_entry, f)
                f.write('\n')
                json.dump(assistant_entry, f)
                f.write('\n')
            logger.debug("Interaction logged to memory journal with metadata.")
        except IOError as e:
            logger.error(f"Error writing to memory journal {MEMORY_JOURNAL_PATH}: {e}")

    def add(self, id: str, text: str, metadata: dict):
        if not self.index:
            logger.warning("Pinecone index is not initialized. Skipping add (vector store). ")
            return
        try:
            # Ensure metadata is JSON serializable if necessary, though Pinecone handles dict
            # Embeddings might need to be generated here or passed in
            # Assuming text is the content to be embedded
            embedding = OpenAIEmbeddings().embed_query(text) # This can be costly, optimize later
            self.index.add_texts([text], ids=[id], metadatas=[metadata])
            logger.debug(f"Added text with ID {id} to Pinecone index.")
        except Exception as e:
            logger.error(f"Error adding text to Pinecone index: {e}")

    def query(self, text: str, k: int = 5):
        """Queries the vector database (Pinecone) for similar texts."""
        if not self.index:
            logger.warning("Pinecone index is not initialized. Returning empty result (vector store query).")
            return []
        try:
            results = self.index.similarity_search_with_score(text, k=k)
            logger.debug(f"Pinecone query returned {len(results)} results.")
            return results
        except Exception as e:
            logger.error(f"Error querying Pinecone index: {e}")
            return []

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search recent memories (from memory.jsonl) for those containing the query string (case-insensitive)."""
        logger.debug(f"Searching recent memories for query: '{query}'")
        try:
            # Increased limit for internal search to find more potential matches before filtering
            memories = self.get_recent_memories(limit=100)
            relevant = [m for m in memories if m.get('content') and query.lower() in m.get('content', '').lower()]
            # Sort by relevance (simple string contains match, could be improved)
            # For simplicity, just taking the first 'limit' matches found
            logger.debug(f"Found {len(relevant)} relevant memories, returning top {limit}.")
            return relevant[:limit]
        except Exception as e:
            logger.error(f"Memory search error: {e}")
            return []

    def get_recent_memories(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Read the last N user/assistant messages from memory.jsonl."""
        logger.debug(f"Getting last {limit} memories from journal.")
        if not MEMORY_JOURNAL_PATH.exists():
            logger.warning(f"Memory journal file not found: {MEMORY_JOURNAL_PATH}")
            return []

        lines = []
        try:
            # Read lines efficiently from the end of a potentially large file
            with open(MEMORY_JOURNAL_PATH, 'rb') as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                read_size = min(file_size, 8192) # Read last 8KB initially
                f.seek(file_size - read_size, os.SEEK_SET)

                data = f.read().decode('utf-8')
                lines = data.splitlines()

                # If we didn't read enough lines, read more
                while len(lines) < limit * 2 and read_size < file_size:
                     read_size = min(file_size, read_size * 2) # Double read size
                     f.seek(file_size - read_size, os.SEEK_SET)
                     data = f.read().decode('utf-8')
                     lines = data.splitlines()

            # Process lines from the end
            memories = []
            # Iterate through lines in reverse to get the most recent
            for line in reversed(lines):
                 line = line.strip()
                 if not line: # Skip empty lines
                      continue
                 try:
                      entry = json.loads(line)
                      # Filter for user/assistant roles for conversational history
                      if entry.get('role') in ('user', 'assistant'):
                           memories.append(entry)
                      # Stop once we have the desired number of conversational turns
                      if len(memories) >= limit:
                           break
                 except json.JSONDecodeError as e:
                      logger.error(f"Error decoding JSON in {MEMORY_JOURNAL_PATH}: {e} - Line: {line[:100]}...")
                      continue # Skip problematic line

            # Reverse to get chronological order
            return list(reversed(memories))

        except Exception as e:
            logger.error(f"Error reading memory journal file {MEMORY_JOURNAL_PATH}: {e}")
            return []

# Example usage (for testing):
# if __name__ == "__main__":
#     # Create a dummy memory manager
#     # manager = MemoryManager()

#     # Add a sample interaction with Trinity metadata
#     # sample_metadata = {"trinity_intent": "wisdom", "selected_model": "gpt-4"}
#     # manager.add_interaction("What is the meaning of life?", "That is a profound question.", sample_metadata)

#     # Get recent memories
#     # recent = manager.get_recent_memories(limit=10)
#     # print("Recent Memories:", recent)

#     # Search memories
#     # search_results = manager.search("meaning of life")
#     # print("Search Results:", search_results)
