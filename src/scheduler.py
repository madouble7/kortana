class Scheduler:
    def __init__(self):
        pass

    def schedule(self, invitee: str, when: str, subject: str):
        # Simulate a successful scheduling response
        return {
            "status": "success",
            "invitee": invitee,
            "time": when,
            "subject": subject,
            "message": "This is a mock response. No real meeting was scheduled.",
        }
