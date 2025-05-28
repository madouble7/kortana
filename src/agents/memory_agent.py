from typing import List, Dict
from datetime import datetime
from pinecone import Pinecone
import os

class MemoryAgent:
    def __init__(self, pinecone_api_key: str, pinecone_env: str, index_name: str = "kortana-memories"):
        if not pinecone_api_key or not pinecone_env:
            raise ValueError("Pinecone API key and environment must be set. Please set PINECONE_API_KEY and PINECONE_ENV in your .env file.")
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index_name = index_name
        # Use integrated embedding model
        if not self.pc.has_index(index_name):
            self.pc.create_index_for_model(
                name=index_name,
                cloud="aws",
                region=pinecone_env,  # e.g., "us-east-1"
                embed={
                    "model": "llama-text-embed-v2",
                    "field_map": {"text": "chunk_text"}
                }
            )
        self.index = self.pc.Index(index_name)

    def plan(self, text: str) -> List[Dict]:
        """
        Split `text` into chunks, summarize + extract metadata for each.
        Returns a list of dicts: {chunk, summary, timestamp, tags}
        """
        # You can still use your LLM for summarization if desired, or just chunk
        chunks = [text[i : i + 1500] for i in range(0, len(text), 1500)]
        plans = []
        for chunk in chunks:
            # If you want to use an LLM for summary/meta, add that logic here
            summary = chunk[:100]  # Placeholder: first 100 chars as summary
            meta = ""
            plans.append({
                "chunk": chunk,
                "summary": summary,
                "meta": meta,
                "created_at": datetime.utcnow().isoformat()
            })
        return plans

    def execute(self, plans: List[Dict]):
        """Upsert each plan into Pinecone index using integrated embedding."""
        records = [
            {
                "_id": str(i),
                "chunk_text": p["chunk"],
                "summary": p["summary"],
                "meta": p["meta"],
                "created_at": p["created_at"]
            }
            for i, p in enumerate(plans)
        ]
        self.index.upsert_records("default", records)

    def verify(self, query: str) -> List[Dict]:
        """Run a semantic search in Pinecone and return the top 3 matches."""
        results = self.index.search(
            namespace="default",
            query={
                "top_k": 3,
                "inputs": {"text": query}
            }
        )
        return results['result']['hits']
