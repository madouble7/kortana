"""
Tests for authentication module
"""

from datetime import timedelta

import pytest
from src.kortana.auth import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)


@pytest.mark.unit
class TestPasswordHashing:
    """Password hashing tests"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "securepassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "securepassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "securepassword123"
        wrong_password = "wrongpassword456"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_same_password_different_hash(self):
        """Test that same password produces different hashes"""
        password = "securepassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


@pytest.mark.unit
class TestTokenGeneration:
    """JWT token generation tests"""

    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_with_expiration(self):
        """Test token creation with custom expiration"""
        data = {"sub": "testuser"}
        expires = timedelta(hours=24)
        token = create_access_token(data, expires)

        assert token is not None

    def test_decode_valid_token(self, test_token):
        """Test decoding valid token"""
        decoded = decode_token(test_token)

        assert decoded is not None
        assert decoded.user_id is not None

    def test_decode_invalid_token(self):
        """Test decoding invalid token"""
        invalid_token = "invalid.token.here"

        with pytest.raises(Exception):  # Should raise HTTPException
            decode_token(invalid_token)

    def test_token_contains_scopes(self):
        """Test that token contains scopes"""
        data = {"sub": "testuser", "scopes": ["read", "write"]}
        token = create_access_token(data)
        decoded = decode_token(token)

        assert decoded.scopes is not None


@pytest.mark.unit
class TestAuthDependencies:
    """Authentication dependency tests"""

    def test_oauth2_scheme_exists(self):
        """Test OAuth2 scheme is configured"""
        from src.kortana.auth import oauth2_scheme

        assert oauth2_scheme is not None

    def test_password_context_exists(self):
        """Test password context is configured"""
        from src.kortana.auth import pwd_context

        assert pwd_context is not None
        schemes = pwd_context.schemes()
        assert "pbkdf2_sha256" in schemes

    def test_full_auth_cycle(self):
        """Test complete authentication cycle"""
        # Create password hash
        original_password = "mypassword123"
        hashed = get_password_hash(original_password)

        # Verify password
        assert verify_password(original_password, hashed)

        # Create token
        token = create_access_token({"sub": "testuser"})

        # Decode token
        decoded = decode_token(token)
        assert decoded.user_id == "testuser"

    def test_user_login_simulation(self):
        """Simulate user login process"""
        username = "testuser"
        password = "securepass123"

        # Registration: store hashed password
        stored_hash = get_password_hash(password)

        # Login: verify password
        login_password = "securepass123"
        is_valid = verify_password(login_password, stored_hash)

        assert is_valid

        # Issue token
        if is_valid:
            token = create_access_token({"sub": username})
            assert token is not None
