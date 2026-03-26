import os
import requests

class AuthScopeInsufficientError(Exception):
    pass

def validate_git_permissions():
    """Verify that current auth scope permits repository manipulation."""
    token = os.getenv("KORTANA_PAT")
    if not token:
        raise AuthScopeInsufficientError("KORTANA_PAT not configured.")
        
    response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"token {token}"}
    )
    scopes = response.headers.get("X-OAuth-Scopes", "").split(", ")
    
    if "repo" not in scopes and "workflow" not in scopes:
        raise AuthScopeInsufficientError("Critical: PAT lacks write access to repository.")
    return True