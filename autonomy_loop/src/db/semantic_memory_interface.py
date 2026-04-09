import math
from datetime import datetime

class SemanticMemoryInterface:
    def __init__(self, db_connection):
        self.db = db_connection

    def get_ranked_memories(self, embedding, top_k=3):
        memories = self.db.execute("SELECT id, content, embedding, created_at FROM SelfMemory")
        scored_memories = []
        now = datetime.utcnow().timestamp()
        for mem in memories:
            score = self._cosine_similarity(embedding, mem['embedding'])
            age_days = (now - mem['created_at']) / 86400
            recency_boost = 1.0 / (1.0 + math.log1p(age_days))
            final_score = score * 0.7 + recency_boost * 0.3
            scored_memories.append({'id': mem['id'], 'content': mem['content'], 'score': final_score})
        scored_memories.sort(key=lambda x: x['score'], reverse=True)
        return scored_memories[:top_k]