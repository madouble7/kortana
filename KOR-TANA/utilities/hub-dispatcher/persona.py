class Persona:
    """Simple persona for Kortana-like assistant."""

    def __init__(self, name: str = "Kortana", description: str = "A helpful assistant"):
        self.name = name
        self.description = description

    def greet(self) -> str:
        return f"Hello — I'm {self.name}. {self.description}. How can I help?"

    def speak(self, message: str) -> str:
        return f"{self.name}: {message}"
