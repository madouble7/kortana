import json

class DirectiveManager:
    @staticmethod
    def get_quantum_link():
        with open('src/config/directives.json', 'r') as f:
            return json.load(f).get('quantum_link')

    @staticmethod
    def validate_alignment(task):
        link = DirectiveManager.get_quantum_link()
        return 'quantum_link' in task or 'objective' in task