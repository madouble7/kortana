def generate_response(content, task_id):
    metadata = {"context": "quantum_link", "node_id": task_id, "alignment": "proactive"}
    response = {"content": content, "system_metadata": metadata}
    return response