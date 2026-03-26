import os
import logging

REQUIRED_SCOPES = ['repo', 'workflow']

def validate_env():
    token = os.getenv("GITHUB_PAT")
    if not token:
        raise EnvironmentError("GITHUB_PAT not set in environment.")
    logging.info(f"Configuration verified. Required scopes: {REQUIRED_SCOPES}")

validate_env()