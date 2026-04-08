"""
Tests for the auth router endpoints.
"""

import uuid


def make_email():
    return f"test_{uuid.uuid4().hex[:12]}@example.com"


class TestRegisterEndpoint:
    """Tests for POST /api/auth/register"""

    def test_register_success(self, client):
        email = make_email()
        response = client.post(
            "/api/auth/auth/register",
            json={
                "email": email,
                "password": "StrongPass1!",
                "confirm_password": "StrongPass1!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == email
        assert data["is_active"] is True
        assert data["role"] == "user"
        assert "id" in data

    def test_register_password_mismatch(self, client):
        response = client.post(
            "/api/auth/auth/register",
            json={
                "email": make_email(),
                "password": "StrongPass1!",
                "confirm_password": "Different1!",
            },
        )
        assert response.status_code == 400
        assert "Passwords do not match" in response.json()["detail"]

    def test_register_short_password(self, client):
        response = client.post(
            "/api/auth/auth/register",
            json={"email": make_email(), "password": "abc", "confirm_password": "abc"},
        )
        assert response.status_code == 400
        assert "8 characters" in response.json()["detail"]

    def test_register_duplicate_email(self, client):
        email = make_email()
        payload = {
            "email": email,
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
        }
        client.post("/api/auth/auth/register", json=payload)
        response = client.post("/api/auth/auth/register", json=payload)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        response = client.post(
            "/api/auth/auth/register",
            json={
                "email": "not-an-email",
                "password": "StrongPass1!",
                "confirm_password": "StrongPass1!",
            },
        )
        assert response.status_code == 422  # Pydantic email validation


class TestLoginEndpoint:
    """Tests for POST /api/auth/login"""

    def _register_user(self, client, password="StrongPass1!"):
        email = make_email()
        client.post(
            "/api/auth/auth/register",
            json={"email": email, "password": password, "confirm_password": password},
        )
        return email

    def test_login_success(self, client):
        email = self._register_user(client)
        response = client.post(
            "/api/auth/auth/login",
            data={"username": email, "password": "StrongPass1!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        email = self._register_user(client)
        response = client.post(
            "/api/auth/auth/login",
            data={"username": email, "password": "WrongPass999!"},
        )
        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/auth/auth/login",
            data={"username": "nobody_xyz@nowhere.test", "password": "SomePass1!"},
        )
        assert response.status_code == 401

    def test_login_deactivated_user(self, client):
        """Deactivated user should be rejected at login."""
        from src.kortana.auth import get_user_by_email

        email = self._register_user(client)
        user = get_user_by_email(email)
        user.is_active = False
        response = client.post(
            "/api/auth/auth/login",
            data={"username": email, "password": "StrongPass1!"},
        )
        assert response.status_code in (401, 403)
        # Restore
        user.is_active = True


class TestRefreshEndpoint:
    """Tests for POST /api/auth/refresh"""

    def _login(self, client, email=None, password="StrongPass1!"):
        if email is None:
            email = make_email()
        client.post(
            "/api/auth/auth/register",
            json={"email": email, "password": password, "confirm_password": password},
        )
        resp = client.post(
            "/api/auth/auth/login", data={"username": email, "password": password}
        )
        return resp.json()

    def test_refresh_success(self, client):
        tokens = self._login(client)
        response = client.post(
            "/api/auth/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_refresh_with_access_token_rejected(self, client):
        """Submitting an access_token as a refresh_token should fail."""
        tokens = self._login(client)
        response = client.post(
            "/api/auth/auth/refresh", json={"refresh_token": tokens["access_token"]}
        )
        assert response.status_code in (401, 400)

    def test_refresh_with_garbage_token(self, client):
        response = client.post(
            "/api/auth/auth/refresh", json={"refresh_token": "this.is.garbage"}
        )
        assert response.status_code in (401, 400)


class TestMeEndpoint:
    """Tests for GET /api/auth/me"""

    def _get_auth_headers(self, client):
        email = make_email()
        client.post(
            "/api/auth/auth/register",
            json={
                "email": email,
                "password": "StrongPass1!",
                "confirm_password": "StrongPass1!",
            },
        )
        resp = client.post(
            "/api/auth/auth/login", data={"username": email, "password": "StrongPass1!"}
        )
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}, email

    def test_me_success(self, client):
        headers, email = self._get_auth_headers(client)
        response = client.get("/api/auth/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email

    def test_me_unauthenticated(self, client):
        response = client.get("/api/auth/auth/me")
        assert response.status_code == 401

    def test_me_invalid_token(self, client):
        response = client.get(
            "/api/auth/auth/me", headers={"Authorization": "Bearer invalidtoken"}
        )
        assert response.status_code == 401


class TestLogoutEndpoint:
    """Tests for POST /api/auth/logout"""

    def test_logout_success(self, client):
        email = make_email()
        client.post(
            "/api/auth/auth/register",
            json={
                "email": email,
                "password": "StrongPass1!",
                "confirm_password": "StrongPass1!",
            },
        )
        resp = client.post(
            "/api/auth/auth/login", data={"username": email, "password": "StrongPass1!"}
        )
        token = resp.json()["access_token"]
        response = client.post(
            "/api/auth/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "logged out" in response.json()["message"]

    def test_logout_unauthenticated(self, client):
        response = client.post("/api/auth/auth/logout")
        assert response.status_code == 401


class TestChangePasswordEndpoint:
    """Tests for POST /api/auth/change-password"""

    def _login_and_get_token(self, client, email, password="StrongPass1!"):
        client.post(
            "/api/auth/auth/register",
            json={"email": email, "password": password, "confirm_password": password},
        )
        resp = client.post(
            "/api/auth/auth/login", data={"username": email, "password": password}
        )
        return resp.json()["access_token"]

    def test_change_password_success(self, client):
        email = make_email()
        token = self._login_and_get_token(client, email)
        response = client.post(
            "/api/auth/auth/change-password",
            params={
                "current_password": "StrongPass1!",
                "new_password": "NewPass8888!",
                "confirm_password": "NewPass8888!",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "Password successfully changed" in response.json()["message"]

    def test_change_password_wrong_current(self, client):
        email = make_email()
        token = self._login_and_get_token(client, email)
        response = client.post(
            "/api/auth/auth/change-password",
            params={
                "current_password": "wrong_password",
                "new_password": "NewPass8888!",
                "confirm_password": "NewPass8888!",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"]

    def test_change_password_mismatch(self, client):
        email = make_email()
        token = self._login_and_get_token(client, email)
        response = client.post(
            "/api/auth/auth/change-password",
            params={
                "current_password": "StrongPass1!",
                "new_password": "NewPass8888!",
                "confirm_password": "Different!",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400

    def test_change_password_too_short(self, client):
        email = make_email()
        token = self._login_and_get_token(client, email)
        response = client.post(
            "/api/auth/auth/change-password",
            params={
                "current_password": "StrongPass1!",
                "new_password": "abc",
                "confirm_password": "abc",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400

    def test_change_password_unauthenticated(self, client):
        response = client.post(
            "/api/auth/auth/change-password",
            params={
                "current_password": "x",
                "new_password": "y",
                "confirm_password": "y",
            },
        )
        assert response.status_code == 401


class TestDeactivateEndpoint:
    """Tests for POST /api/auth/deactivate"""

    def test_deactivate_success(self, client):
        email = make_email()
        client.post(
            "/api/auth/auth/register",
            json={
                "email": email,
                "password": "StrongPass1!",
                "confirm_password": "StrongPass1!",
            },
        )
        resp = client.post(
            "/api/auth/auth/login", data={"username": email, "password": "StrongPass1!"}
        )
        token = resp.json()["access_token"]
        response = client.post(
            "/api/auth/auth/deactivate", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "deactivated" in response.json()["message"]

    def test_deactivate_unauthenticated(self, client):
        response = client.post("/api/auth/auth/deactivate")
        assert response.status_code == 401
