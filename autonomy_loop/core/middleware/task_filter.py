import json

def evaluate_task_alignment(task_data):
    with open('core/config/directives.json', 'r') as f:
        config = json.load(f)
    
    params = config['quantum_link']['parameters']
    task_intent = task_data.get('intent', '')
    
    alignment_score = sum(1 for param in params if param in task_intent.lower())
    
    if alignment_score >= 1:
        return True
    return False