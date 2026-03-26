import os

class AuthManager:
    @staticmethod
    def validate_scopes(auth_instance, required={'repo', 'workflow'}):
        scopes = auth_instance.get_oauth_scopes()
        if not required.issubset(set(scopes)):
            raise PermissionError(f"Insufficient PAT Scopes. Required: {required}")
        return True

    @staticmethod
    def get_token():
        return os.getenv('KORTANA_PAT')