import os

class Config:
    """Configuration settings for the heartbeat service."""
    
    # Environment variables
    TOKEN_REFRESH_INTERVAL = int(os.getenv("TOKEN_REFRESH_INTERVAL", 300))  # Default to 5 minutes
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # Default log level
    KORTANA_API_URL = os.getenv("KORTANA_API_URL", "https://api.kortana.example.com")  # Default API URL

    # Other constants
    SERVICE_NAME = "Kor'tana Heartbeat Service"
    VERSION = "1.0.0"