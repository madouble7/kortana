class PreExecutionCheck:
    def validate(self, task, context, historical_data):
        if context.get('alignment') != 'high':
            raise ValueError('task does not align with gardener mission')
        return True