from src.db.semantic_memory_interface import SemanticMemoryInterface

class PromptAssembly:
    def __init__(self, db_interface):
        self.memory = db_interface

    def semantic_memory(self, query_embedding):
        results = self.memory.get_ranked_memories(query_embedding, top_k=3)
        threshold = 0.65
        filtered_results = [r for r in results if r['score'] >= threshold]
        return " ".join([r['content'] for r in filtered_results])