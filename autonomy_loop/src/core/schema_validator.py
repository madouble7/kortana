class SchemaValidator:
    def validate(self, task):
        required_fields = ['objective_id', 'quantum_link_reference']
        if 'directive' not in task:
            return False
        return all(field in task['directive'] for field in required_fields)