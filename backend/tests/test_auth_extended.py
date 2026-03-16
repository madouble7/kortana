"""
Tests for auth module - user creation, authentication, and token management.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from src.kortana.auth import (
    UserObject,
    authenticate_user,
    create_user,
    get_user_by_email,
    verify_password,
)


class TestUserObject:
    """Tests for UserObject wrapper class."""

    def test_init_with_kwargs(self):
        user = UserObject(id=1, email="a@b.com", role="user")
        assert user.id == 1
        assert user.email == "a@b.com"

    def test_getitem(self):
        user = UserObject(id=5, email="x@y.com")
        assert user["id"] == 5

    def test_get_with_default(self):
        user = UserObject(id=1)
        assert user.get("missing_field", "default") == "default"

    def test_setitem(self):
        user = UserObject(id=1)
        user["role"] = "admin"
        assert user.role == "admin"


class TestCreateUser:
    """Tests for create_user function."""

    def _make_user_data(self, email="test_create@example.com", password="password123"):
        data = MagicMock()
        data.email = email
        data.password = password
        data.confirm_password = password
        return data

    def test_create_user_success(self):
        # Use unique email to avoid state collision between tests
        import uuid

        email = f"create_{uuid.uuid4()}@example.com"
        data = self._make_user_data(email=email)
        user = create_user(data)
        assert user.email == email
        assert user.is_active is True
        assert user.role == "user"

    def test_create_user_password_mismatch(self):
        import uuid

        data = MagicMock()
        data.email = f"mismatch_{uuid.uuid4()}@example.com"
        data.password = "password123"
        data.confirm_password = "differentpassword"
        with pytest.raises(HTTPException) as exc_info:
            create_user(data)
        assert exc_info.value.status_code == 400
        assert "Passwords do not match" in exc_info.value.detail

    def test_create_user_short_password(self):
        import uuid

        data = MagicMock()
        data.email = f"short_{uuid.uuid4()}@example.com"
        data.password = "abc"
        data.confirm_password = "abc"
        with pytest.raises(HTTPException) as exc_info:
            create_user(data)
        assert exc_info.value.status_code == 400
        assert "8 characters" in exc_info.value.detail

    def test_create_duplicate_user(self):
        import uuid

        email = f"dup_{uuid.uuid4()}@example.com"
        data = self._make_user_data(email=email)
        create_user(data)
        with pytest.raises(HTTPException) as exc_info:
            create_user(data)
        assert exc_info.value.status_code == 400
        assert "already registered" in exc_info.value.detail

    def test_created_user_password_is_hashed(self):
        import uuid

        email = f"hash_{uuid.uuid4()}@example.com"
        data = self._make_user_data(email=email, password="plainpassword")
        user = create_user(data)
        assert user.hashed_password != "plainpassword"
        assert verify_password("plainpassword", user.hashed_password)


class TestGetUserByEmail:
    """Tests for get_user_by_email function."""

    def test_returns_none_for_unknown_email(self):
        result = get_user_by_email("nonexistent_xyz@test.com")
        assert result is None

    def test_returns_user_after_creation(self):
        import uuid

        email = f"lookup_{uuid.uuid4()}@example.com"
        data = MagicMock()
        data.email = email
        data.password = "validpassword"
        data.confirm_password = "validpassword"
        created = create_user(data)
        found = get_user_by_email(email)
        assert found is not None
        assert found.email == email


class TestAuthenticateUser:
    """Tests for authenticate_user function."""

    def _create_test_user(self, email, password="testpass999"):
        data = MagicMock()
        data.email = email
        data.password = password
        data.confirm_password = password
        return create_user(data), password

    def test_authenticate_success(self):
        import uuid

        email = f"auth_{uuid.uuid4()}@example.com"
        user, password = self._create_test_user(email=email)
        result = authenticate_user(email, password)
        assert result is not None
        assert result.email == email

    def test_authenticate_wrong_password(self):
        import uuid

        email = f"wrongpwd_{uuid.uuid4()}@example.com"
        self._create_test_user(email=email, password="rightpassword")
        result = authenticate_user(email, "wrongpassword")
        assert result is None

    def test_authenticate_nonexistent_user(self):
        result = authenticate_user("ghost_nobody@notexist.com", "whatever")
        assert result is None
