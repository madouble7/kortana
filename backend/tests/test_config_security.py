from backend.src.kortana.config import settings

def test_required_scopes_defined():
    assert len(settings.GITHUB_REQUIRED_SCOPES) > 0
    assert "repo" in settings.GITHUB_REQUIRED_SCOPES