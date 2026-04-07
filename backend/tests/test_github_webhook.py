import hashlib
import hmac
import json
from unittest.mock import patch

import httpx
import pytest
from src.kortana.main import app


@pytest.mark.asyncio
async def test_github_webhook_missing_signature():
    with patch("src.kortana.routers.github.get_settings") as mock_settings:
        mock_settings.return_value.GITHUB_WEBHOOK_SECRET = "secret"
        # No signature sent
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/github/webhook", json={})
        assert response.status_code == 401
        assert response.json()["detail"] == "Missing signature"


@pytest.mark.asyncio
async def test_github_webhook_invalid_signature():
    with patch("src.kortana.routers.github.get_settings") as mock_settings:
        mock_settings.return_value.GITHUB_WEBHOOK_SECRET = "secret"
        headers = {"X-Hub-Signature-256": "sha256=invalid"}
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/github/webhook", json={}, headers=headers
            )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid signature"


@pytest.mark.asyncio
async def test_github_webhook_valid_signature_ignored_event():
    with patch("src.kortana.routers.github.get_settings") as mock_settings:
        mock_settings.return_value.GITHUB_WEBHOOK_SECRET = "secret"
        payload = {"action": "created"}
        body = json.dumps(payload).encode()
        signature = (
            "sha256=" + hmac.new("secret".encode(), body, hashlib.sha256).hexdigest()
        )
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "push",
        }
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/github/webhook", content=body, headers=headers
            )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"


@pytest.mark.asyncio
async def test_github_webhook_valid_event():
    with patch("src.kortana.routers.github.get_settings") as mock_settings:
        mock_settings.return_value.GITHUB_WEBHOOK_SECRET = "secret"
        payload = {
            "action": "created",
            "issue": {"number": 42},
            "repository": {"full_name": "KOR-TANA/kortana"},
            "comment": {"id": 123, "body": "/approve", "user": {"login": "human"}},
        }
        body = json.dumps(payload).encode()
        signature = (
            "sha256=" + hmac.new("secret".encode(), body, hashlib.sha256).hexdigest()
        )
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "issue_comment",
            "X-GitHub-Delivery": "delivery-123",
        }
        with patch(
            "src.kortana.routers.github.BackgroundTasks.add_task"
        ) as mock_bg_add:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/github/webhook", content=body, headers=headers
                )
            assert response.status_code == 200
            assert response.json()["status"] == "accepted"
            mock_bg_add.assert_called_once()
