"""V11A — Auth Provider Integration.

Provides pluggable authentication provider support so operator identities
can be verified against external identity providers (OAuth2, OIDC, API keys,
service accounts) instead of relying solely on local registration.

Each AuthProvider implements a common interface: verify_token() returns
a VerifiedCredential or None.  The AuthProviderRegistry dispatches
verification to the correct provider based on the credential type.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger("kortana.auth_provider")


# ---------------------------------------------------------------------------
# Provider types and credential schemes
# ---------------------------------------------------------------------------


class ProviderType(str, Enum):
    """Supported auth provider types."""

    LOCAL = "local"              # Internal operator registry (V10)
    API_KEY = "api_key"          # HMAC-signed API keys
    OAUTH2 = "oauth2"           # OAuth2 bearer tokens
    SERVICE_ACCOUNT = "service_account"  # Machine-to-machine credentials
    OIDC = "oidc"               # OpenID Connect


class CredentialStatus(str, Enum):
    """Lifecycle state of a credential."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


# ---------------------------------------------------------------------------
# Verified credential
# ---------------------------------------------------------------------------


@dataclass
class VerifiedCredential:
    """Result of successful credential verification.

    Bridges external auth to the internal OperatorIdentity system.
    """

    operator_id: str
    provider_type: ProviderType
    credential_id: str
    display_name: str
    role_hint: str           # suggested role from the provider
    issued_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    scopes: list[str] = field(default_factory=list)
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    verification_hash: str = ""

    def __post_init__(self) -> None:
        if not self.verification_hash:
            self.verification_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "operator_id": self.operator_id,
                "provider_type": self.provider_type.value,
                "credential_id": self.credential_id,
                "issued_at": self.issued_at.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_id": self.operator_id,
            "provider_type": self.provider_type.value,
            "credential_id": self.credential_id,
            "display_name": self.display_name,
            "role_hint": self.role_hint,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scopes": self.scopes,
            "is_expired": self.is_expired,
            "verification_hash": self.verification_hash,
        }


# ---------------------------------------------------------------------------
# Auth provider interface + implementations
# ---------------------------------------------------------------------------


class AuthProvider:
    """Base auth provider interface."""

    provider_type: ProviderType = ProviderType.LOCAL

    def verify_token(self, token: str) -> VerifiedCredential | None:
        """Verify a token and return a VerifiedCredential or None."""
        raise NotImplementedError

    def revoke(self, credential_id: str) -> bool:
        """Revoke a credential. Returns True if found and revoked."""
        return False


class LocalAuthProvider(AuthProvider):
    """Verifies credentials against the V10 operator registry."""

    provider_type = ProviderType.LOCAL

    def verify_token(self, token: str) -> VerifiedCredential | None:
        """Treat token as operator_id and verify against registry."""
        from src.kortana.services.operator_identity import get_operator_registry

        registry = get_operator_registry()
        operator = registry.get(token)
        if operator is None or not operator.active:
            return None

        return VerifiedCredential(
            operator_id=operator.operator_id,
            provider_type=ProviderType.LOCAL,
            credential_id=f"local:{operator.operator_id}",
            display_name=operator.display_name,
            role_hint=operator.role.value,
        )


class APIKeyProvider(AuthProvider):
    """HMAC-based API key authentication.

    Keys are generated as signed tokens (secret + operator_id) and
    verified by recomputing the HMAC.  Supports key rotation via
    revocation and re-issue.
    """

    provider_type = ProviderType.API_KEY

    def __init__(self, signing_secret: str | None = None) -> None:
        # Use a deterministic default for testing; production should inject a real secret
        self._secret = (signing_secret or "kortana-api-key-secret").encode()
        self._keys: dict[str, _APIKeyRecord] = {}  # credential_id → record
        self._revoked: set[str] = set()

    def issue_key(
        self,
        operator_id: str,
        display_name: str,
        role_hint: str = "operator",
        ttl_hours: int = 720,
        scopes: list[str] | None = None,
    ) -> tuple[str, VerifiedCredential]:
        """Issue a new API key for an operator.

        Returns (raw_key, credential) — raw_key is the bearer token.
        """
        key_id = f"ak_{secrets.token_hex(8)}"
        raw_token = secrets.token_hex(32)
        signature = hmac.new(
            self._secret,
            f"{key_id}:{raw_token}".encode(),
            hashlib.sha256,
        ).hexdigest()

        now = datetime.utcnow()
        credential = VerifiedCredential(
            operator_id=operator_id,
            provider_type=ProviderType.API_KEY,
            credential_id=key_id,
            display_name=display_name,
            role_hint=role_hint,
            issued_at=now,
            expires_at=now + timedelta(hours=ttl_hours),
            scopes=scopes or [],
        )

        self._keys[key_id] = _APIKeyRecord(
            key_id=key_id,
            raw_token=raw_token,
            signature=signature,
            credential=credential,
        )

        # The bearer token is key_id:raw_token
        bearer = f"{key_id}:{raw_token}"
        logger.info("API key issued: %s for %s", key_id, operator_id)
        return bearer, credential

    def verify_token(self, token: str) -> VerifiedCredential | None:
        """Verify a bearer token (key_id:raw_token)."""
        parts = token.split(":", 1)
        if len(parts) != 2:
            return None

        key_id, raw_token = parts
        if key_id in self._revoked:
            logger.warning("Rejected revoked API key: %s", key_id)
            return None

        record = self._keys.get(key_id)
        if record is None:
            return None

        # Verify HMAC
        expected = hmac.new(
            self._secret,
            f"{key_id}:{raw_token}".encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, record.signature):
            logger.warning("API key HMAC mismatch: %s", key_id)
            return None

        if record.credential.is_expired:
            logger.warning("API key expired: %s", key_id)
            return None

        return record.credential

    def revoke(self, credential_id: str) -> bool:
        if credential_id in self._keys:
            self._revoked.add(credential_id)
            logger.info("API key revoked: %s", credential_id)
            return True
        return False

    @property
    def active_key_count(self) -> int:
        return len(self._keys) - len(self._revoked)


@dataclass
class _APIKeyRecord:
    """Internal record for an issued API key."""
    key_id: str
    raw_token: str
    signature: str
    credential: VerifiedCredential


class ServiceAccountProvider(AuthProvider):
    """Service account provider for machine-to-machine auth.

    Service accounts are pre-registered with a shared secret
    and verified via HMAC.
    """

    provider_type = ProviderType.SERVICE_ACCOUNT

    def __init__(self) -> None:
        self._accounts: dict[str, _ServiceAccountRecord] = {}
        self._revoked: set[str] = set()

    def register(
        self,
        account_id: str,
        display_name: str,
        role_hint: str = "operator",
        scopes: list[str] | None = None,
    ) -> tuple[str, VerifiedCredential]:
        """Register a new service account. Returns (secret, credential)."""
        secret = secrets.token_hex(32)
        credential = VerifiedCredential(
            operator_id=account_id,
            provider_type=ProviderType.SERVICE_ACCOUNT,
            credential_id=f"sa:{account_id}",
            display_name=display_name,
            role_hint=role_hint,
            scopes=scopes or [],
        )
        self._accounts[account_id] = _ServiceAccountRecord(
            account_id=account_id,
            secret_hash=hashlib.sha256(secret.encode()).hexdigest(),
            credential=credential,
        )
        logger.info("Service account registered: %s", account_id)
        return secret, credential

    def verify_token(self, token: str) -> VerifiedCredential | None:
        """Verify a service account token (account_id:secret)."""
        parts = token.split(":", 1)
        if len(parts) != 2:
            return None

        account_id, secret = parts
        if account_id in self._revoked:
            return None

        record = self._accounts.get(account_id)
        if record is None:
            return None

        provided_hash = hashlib.sha256(secret.encode()).hexdigest()
        if not hmac.compare_digest(provided_hash, record.secret_hash):
            logger.warning("Service account auth failed: %s", account_id)
            return None

        return record.credential

    def revoke(self, credential_id: str) -> bool:
        account_id = credential_id.replace("sa:", "")
        if account_id in self._accounts:
            self._revoked.add(account_id)
            return True
        return False


@dataclass
class _ServiceAccountRecord:
    """Internal record for a service account."""
    account_id: str
    secret_hash: str
    credential: VerifiedCredential


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------


class AuthProviderRegistry:
    """Dispatches credential verification to the correct provider.

    Providers are registered by type.  verify() tries each provider
    in priority order (local first, then API key, etc.).
    """

    def __init__(self) -> None:
        self._providers: dict[ProviderType, AuthProvider] = {}

    def register_provider(self, provider: AuthProvider) -> None:
        self._providers[provider.provider_type] = provider
        logger.info("Auth provider registered: %s", provider.provider_type.value)

    def get_provider(self, provider_type: ProviderType) -> AuthProvider | None:
        return self._providers.get(provider_type)

    def verify(
        self,
        token: str,
        provider_type: ProviderType | None = None,
    ) -> VerifiedCredential | None:
        """Verify a token against providers.

        If provider_type is given, only that provider is tried.
        Otherwise, all providers are tried in registration order.
        """
        if provider_type:
            provider = self._providers.get(provider_type)
            if provider:
                return provider.verify_token(token)
            return None

        # Try all providers
        for ptype in [ProviderType.LOCAL, ProviderType.API_KEY,
                      ProviderType.SERVICE_ACCOUNT, ProviderType.OAUTH2,
                      ProviderType.OIDC]:
            provider = self._providers.get(ptype)
            if provider:
                result = provider.verify_token(token)
                if result is not None:
                    return result
        return None

    def revoke(self, provider_type: ProviderType, credential_id: str) -> bool:
        provider = self._providers.get(provider_type)
        if provider:
            return provider.revoke(credential_id)
        return False

    @property
    def provider_types(self) -> list[str]:
        return [p.value for p in self._providers]

    @property
    def count(self) -> int:
        return len(self._providers)


# Module-level singleton
_registry = AuthProviderRegistry()
_registry.register_provider(LocalAuthProvider())
_registry.register_provider(APIKeyProvider())
_registry.register_provider(ServiceAccountProvider())


def get_auth_provider_registry() -> AuthProviderRegistry:
    """Return the module-level auth provider registry."""
    return _registry
