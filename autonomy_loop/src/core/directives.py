class GardenerDirective:
    def __init__(self, purpose, milestone):
        self.purpose = purpose
        self.milestone = milestone

    def validate_alignment(self, task_context):
        return {
            "aligned": True,
            "directive": self.purpose,
            "milestone": self.milestone
        }