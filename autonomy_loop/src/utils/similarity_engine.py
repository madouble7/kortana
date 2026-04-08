import hashlib

def generate_task_hash(task_description):
    return hashlib.sha256(task_description.lower().strip().encode('utf-8')).hexdigest()

def get_similarity_score(desc_a, desc_b):
    tokens_a = set(desc_a.lower().split())
    tokens_b = set(desc_b.lower().split())
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / len(union) if union else 0.0