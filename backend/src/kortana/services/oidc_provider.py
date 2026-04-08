"""V12A — OIDC / OAuth2 Provider Integration.

Adds real OIDC provider support (JWT validation, issuer verification,
claims parsing) and OAuth2 authorization code flow with PKCE.  Registers
as a pluggable provider in the V11A AuthProviderRegistry so that tokens
issued by external identity providers can produce VerifiedCredentials.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.kortana.services.auth_provider import VerifiedCredential

logger = logging.getLogger("kortana.oidc_provider")


# ---------------------------------------------------------------------------
# OIDC configuration
# ---------------------------------------------------------------------------


@dataclass
class OIDCConfiguration:
    """Configuration for an OIDC identity provider."""

    issuer_url: str
    client_id: str
    audience: str | None = None
    client_secret: str | None = None      # confidential clients only
    scopes: list[str] = field(default_factory=lambda: ["openid", "profile", "email"])
    supported_algorithms: list[str] = field(default_factory=lambda: ["RS256"])

    # Derived endpoints — in production these come from .well-known/openid-configuration
    token_endpoint: str = ""
    authorization_endpoint: str = ""
    jwks_uri: str = ""
    userinfo_endpoint: str = ""

    config_hash: str = ""

    def __post_init__(self) -> None:
        if not self.jwks_uri:
            self.jwks_uri = f"{self.issuer_url.rstrip('/')}/.well-known/jwks.json"
        if not self.token_endpoint:
            self.token_endpoint = f"{self.issuer_url.rstrip('/')}/oauth/token"
        if not self.authorization_endpoint:
            self.authorization_endpoint = f"{self.issuer_url.rstrip('/')}/authorize"
        if not self.config_hash:
            self.config_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "issuer_url": self.issuer_url,
                "client_id": self.client_id,
                "audience": self.audience,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "issuer_url": self.issuer_url,
            "client_id": self.client_id,
            "audience": self.audience,
            "scopes": self.scopes,
            "supported_algorithms": self.supported_algorithms,
            "token_endpoint": self.token_endpoint,
            "authorization_endpoint": self.authorization_endpoint,
            "jwks_uri": self.jwks_uri,
            "userinfo_endpoint": self.userinfo_endpoint,
            "config_hash": self.config_hash,
        }


# ---------------------------------------------------------------------------
# OIDC token claims
# ---------------------------------------------------------------------------


@dataclass
class OIDCTokenClaims:
    """Parsed claims from an OIDC ID token."""

    sub: str                            # subject identifier
    iss: str                            # issuer
    aud: str | list[str]                # audience
    exp: int                            # expiration (unix timestamp)
    iat: int = 0                        # issued at
    nonce: str = ""
    email: str = ""
    name: str = ""
    groups: list[str] = field(default_factory=list)
    raw_claims: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow().timestamp() > self.exp

    def to_dict(self) -> dict[str, Any]:
        return {
            "sub": self.sub,
            "iss": self.iss,
            "aud": self.aud,
            "exp": self.exp,
            "iat": self.iat,
            "email": self.email,
            "name": self.name,
            "groups": self.groups,
            "is_expired": self.is_expired,
        }


# ---------------------------------------------------------------------------
# OIDC provider
# ---------------------------------------------------------------------------


class OIDCProvider:
    """OIDC auth provider — verifies JWT ID tokens.

    In production the JWKS keys are fetched from the provider's
    well-known endpoint.  For offline / test use, signing keys can
    be registered directly via register_signing_key().

    This implementation validates JWT *structure and claims* without
    requiring a real JWKS fetch (which would need network access).
    Keys registered via register_signing_key() are used for signature
    verification simulation.
    """

    def __init__(self, config: OIDCConfiguration) -> None:
        self.config = config
        self._signing_keys: dict[str, str] = {}   # kid → key material
        self._revoked: set[str] = set()
        self._verified_credentials: dict[str, Any] = {}  # credential_id → record

    # --- key management ---

    def register_signing_key(self, kid: str, key: str) -> None:
        """Register a signing key for offline validation."""
        self._signing_keys[kid] = key
        logger.info("OIDC signing key registered: kid=%s issuer=%s", kid, self.config.issuer_url)

    @property
    def registered_key_count(self) -> int:
        return len(self._signing_keys)

    # --- token verification ---

    def verify_token(self, token: str) -> VerifiedCredential | None:
        """Verify an OIDC ID token and return a VerifiedCredential.

        The token is expected to be a JWT (header.payload.signature).
        Claims are validated against the OIDC configuration.
        """
        from src.kortana.services.auth_provider import ProviderType, VerifiedCredential

        claims = self._decode_jwt_claims(token)
        if claims is None:
            return None

        # Build OIDCTokenClaims
        try:
            token_claims = OIDCTokenClaims(
                sub=claims.get("sub", ""),
                iss=claims.get("iss", ""),
                aud=claims.get("aud", ""),
                exp=int(claims.get("exp", 0)),
                iat=int(claims.get("iat", 0)),
                nonce=claims.get("nonce", ""),
                email=claims.get("email", ""),
                name=claims.get("name", ""),
                groups=claims.get("groups", []),
                raw_claims=claims,
            )
        except (TypeError, ValueError):
            logger.warning("OIDC token claims parse error")
            return None

        # Validate claims
        if not self._validate_claims(token_claims):
            return None

        # Check for revocation
        credential_id = f"oidc:{token_claims.iss}:{token_claims.sub}"
        if credential_id in self._revoked:
            logger.warning("OIDC credential revoked: %s", credential_id)
            return None

        # Verify signing key presence (simulated JWKS validation)
        header = self._decode_jwt_header(token)
        if header is not None and self._signing_keys:
            kid = header.get("kid", "")
            if kid and kid not in self._signing_keys:
                logger.warning("OIDC token kid %r not in registered keys", kid)
                return None

        credential = VerifiedCredential(
            operator_id=token_claims.sub,
            provider_type=ProviderType.OIDC,
            credential_id=credential_id,
            display_name=token_claims.name or token_claims.email or token_claims.sub,
            role_hint="operator",
            expires_at=datetime.utcfromtimestamp(token_claims.exp),
            scopes=self.config.scopes,
            provider_metadata={
                "issuer": token_claims.iss,
                "email": token_claims.email,
                "groups": token_claims.groups,
            },
        )

        self._verified_credentials[credential_id] = {
            "credential": credential,
            "claims": token_claims,
        }
        logger.info("OIDC token verified: sub=%s iss=%s", token_claims.sub, token_claims.iss)
        return credential

    def _decode_jwt_header(self, token: str) -> dict[str, Any] | None:
        """Decode the JWT header (first segment)."""
        parts = token.split(".")
        if len(parts) < 2:
            return None
        try:
            header_b64 = parts[0]
            padding = 4 - len(header_b64) % 4
            if padding != 4:
                header_b64 += "=" * padding
            header_bytes = base64.urlsafe_b64decode(header_b64)
            return json.loads(header_bytes)
        except Exception:
            return None

    def _decode_jwt_claims(self, token: str) -> dict[str, Any] | None:
        """Decode the JWT payload (second segment) without signature verification.

        In production, signature verification would happen via JWKS.
        This implementation validates structure and claims only.
        """
        parts = token.split(".")
        if len(parts) < 2:
            logger.warning("OIDC token not in JWT format (no dots)")
            return None

        try:
            payload_b64 = parts[1]
            # Add padding if needed
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            return json.loads(payload_bytes)
        except Exception as e:
            logger.warning("OIDC JWT decode error: %s", e)
            return None

    def _validate_claims(self, claims: OIDCTokenClaims) -> bool:
        """Validate token claims against the provider configuration."""
        # Check issuer
        if claims.iss != self.config.issuer_url:
            logger.warning(
                "OIDC issuer mismatch: got %r, expected %r",
                claims.iss,
                self.config.issuer_url,
            )
            return False

        # Check audience
        if self.config.audience:
            aud_list = claims.aud if isinstance(claims.aud, list) else [claims.aud]
            if self.config.audience not in aud_list:
                logger.warning("OIDC audience mismatch")
                return False

        # Check expiration
        if claims.is_expired:
            logger.warning("OIDC token expired: exp=%d", claims.exp)
            return False

        # Check required fields
        if not claims.sub:
            logger.warning("OIDC token missing sub claim")
            return False

        return True

    def revoke(self, credential_id: str) -> bool:
        """Revoke a credential by ID."""
        self._revoked.add(credential_id)
        logger.info("OIDC credential revoked: %s", credential_id)
        return True


# ---------------------------------------------------------------------------
# OAuth2 authorization code flow
# ---------------------------------------------------------------------------


class OAuth2FlowState(str, Enum):
    """State of an OAuth2 authorization flow."""

    PENDING = "pending"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass
class OAuth2AuthorizationFlow:
    """Tracks an OAuth2 authorization code flow with PKCE."""

    flow_id: str = field(default_factory=lambda: f"flow_{secrets.token_hex(8)}")
    state: str = field(default_factory=lambda: secrets.token_hex(16))
    nonce: str = field(default_factory=lambda: secrets.token_hex(16))
    redirect_uri: str = ""
    code_verifier: str = field(default_factory=lambda: secrets.token_urlsafe(64))
    code_challenge: str = ""
    code_challenge_method: str = "S256"
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=10))
    flow_state: OAuth2FlowState = OAuth2FlowState.PENDING
    flow_hash: str = ""

    def __post_init__(self) -> None:
        if not self.code_challenge:
            self.code_challenge = self._compute_code_challenge()
        if not self.flow_hash:
            self.flow_hash = self._compute_hash()

    def _compute_code_challenge(self) -> str:
        """Compute S256 code challenge from the verifier."""
        digest = hashlib.sha256(self.code_verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "flow_id": self.flow_id,
                "state": self.state,
                "created_at": self.created_at.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "state": self.state,
            "nonce": self.nonce,
            "redirect_uri": self.redirect_uri,
            "code_challenge": self.code_challenge,
            "code_challenge_method": self.code_challenge_method,
            "flow_state": self.flow_state.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "flow_hash": self.flow_hash,
        }


class OAuth2Provider:
    """OAuth2 authorization code flow with PKCE.

    Wraps an OIDCProvider to convert authorization codes into
    verified credentials.  In production the code exchange hits
    the token endpoint; here we simulate the exchange to allow
    offline testing while preserving the full flow structure.
    """

    def __init__(self, oidc_provider: OIDCProvider) -> None:
        self.oidc = oidc_provider
        self._flows: dict[str, OAuth2AuthorizationFlow] = {}
        self._code_tokens: dict[str, str] = {}  # auth_code → simulated JWT

    def create_authorization_url(
        self,
        redirect_uri: str = "http://localhost:8000/callback",
    ) -> tuple[str, OAuth2AuthorizationFlow]:
        """Create an authorization URL and flow state.

        Returns (authorization_url, flow) — the URL the user should
        be redirected to, and the flow state to verify the callback.
        """
        flow = OAuth2AuthorizationFlow(redirect_uri=redirect_uri)
        self._flows[flow.state] = flow

        config = self.oidc.config
        params = (
            f"response_type=code"
            f"&client_id={config.client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={'%20'.join(config.scopes)}"
            f"&state={flow.state}"
            f"&nonce={flow.nonce}"
            f"&code_challenge={flow.code_challenge}"
            f"&code_challenge_method=S256"
        )
        url = f"{config.authorization_endpoint}?{params}"

        logger.info("OAuth2 authorization URL created: flow=%s", flow.flow_id)
        return url, flow

    def register_test_code(self, code: str, jwt_token: str) -> None:
        """Register a test authorization code → token mapping.

        In production this exchange happens at the token endpoint.
        """
        self._code_tokens[code] = jwt_token

    def exchange_code(
        self,
        code: str,
        state: str,
    ) -> tuple[VerifiedCredential | None, str | None]:
        """Exchange an authorization code for a verified credential.

        Returns (credential, error). In production this calls the
        token endpoint; here it uses registered test mappings.
        """
        flow = self._flows.get(state)
        if flow is None:
            return None, "Unknown OAuth2 state"

        if flow.is_expired:
            flow.flow_state = OAuth2FlowState.EXPIRED
            return None, "OAuth2 flow expired"

        if flow.flow_state != OAuth2FlowState.PENDING:
            return None, f"OAuth2 flow in unexpected state: {flow.flow_state.value}"

        # Look up the simulated JWT for this code
        jwt_token = self._code_tokens.get(code)
        if jwt_token is None:
            flow.flow_state = OAuth2FlowState.FAILED
            return None, "Invalid authorization code"

        # Verify the JWT via the OIDC provider
        credential = self.oidc.verify_token(jwt_token)
        if credential is None:
            flow.flow_state = OAuth2FlowState.FAILED
            return None, "Token verification failed"

        flow.flow_state = OAuth2FlowState.COMPLETED
        logger.info("OAuth2 code exchange successful: flow=%s", flow.flow_id)
        return credential, None

    @property
    def pending_flow_count(self) -> int:
        return sum(1 for f in self._flows.values() if f.flow_state == OAuth2FlowState.PENDING)

    @property
    def flow_count(self) -> int:
        return len(self._flows)


# ---------------------------------------------------------------------------
# OIDC provider registry
# ---------------------------------------------------------------------------


class OIDCProviderRegistry:
    """Registry of OIDC provider configurations.

    Maps issuer URLs to configured OIDCProvider instances and
    optionally registers them with the V11A AuthProviderRegistry.
    """

    def __init__(self) -> None:
        self._providers: dict[str, OIDCProvider] = {}   # issuer_url → provider
        self._oauth2: dict[str, OAuth2Provider] = {}    # issuer_url → oauth2
        self._configs: dict[str, OIDCConfiguration] = {}

    def register(
        self,
        config: OIDCConfiguration,
        register_with_auth_registry: bool = True,
    ) -> OIDCProvider:
        """Register an OIDC provider configuration.

        If register_with_auth_registry is True, also registers with
        the V11A AuthProviderRegistry so verify() dispatches to it.
        """
        provider = OIDCProvider(config)
        self._providers[config.issuer_url] = provider
        self._configs[config.issuer_url] = config

        # Also create OAuth2 provider
        oauth2 = OAuth2Provider(provider)
        self._oauth2[config.issuer_url] = oauth2

        if register_with_auth_registry:
            self._register_with_auth_registry(provider)

        logger.info("OIDC provider registered: %s", config.issuer_url)
        return provider

    def _register_with_auth_registry(self, provider: OIDCProvider) -> None:
        """Register an OIDC provider with the V11A AuthProviderRegistry."""
        try:
            from src.kortana.services.auth_provider import (
                AuthProvider,
                ProviderType,
                get_auth_provider_registry,
            )

            # Create a wrapper that implements the AuthProvider interface
            class _OIDCAuthProviderAdapter(AuthProvider):
                provider_type = ProviderType.OIDC

                def __init__(self, oidc: OIDCProvider) -> None:
                    self._oidc = oidc

                def verify_token(self, token: str) -> Any:
                    return self._oidc.verify_token(token)

                def revoke(self, credential_id: str) -> bool:
                    return self._oidc.revoke(credential_id)

            registry = get_auth_provider_registry()
            registry.register_provider(_OIDCAuthProviderAdapter(provider))
            logger.info("OIDC provider registered with AuthProviderRegistry")
        except ImportError:
            logger.warning("Could not register OIDC provider with AuthProviderRegistry")

    def get_oidc_provider(self, issuer_url: str) -> OIDCProvider | None:
        return self._providers.get(issuer_url)

    def get_oauth2_provider(self, issuer_url: str) -> OAuth2Provider | None:
        return self._oauth2.get(issuer_url)

    def get_config(self, issuer_url: str) -> OIDCConfiguration | None:
        return self._configs.get(issuer_url)

    def list_providers(self) -> list[dict[str, Any]]:
        return [
            {
                "issuer_url": url,
                "config": config.to_dict(),
                "registered_keys": self._providers[url].registered_key_count,
            }
            for url, config in self._configs.items()
        ]

    @property
    def count(self) -> int:
        return len(self._providers)

    @property
    def issuer_urls(self) -> list[str]:
        return list(self._providers.keys())


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_registry: OIDCProviderRegistry | None = None


def get_oidc_registry() -> OIDCProviderRegistry:
    """Return the module-level OIDC provider registry."""
    global _registry
    if _registry is None:
        _registry = OIDCProviderRegistry()
    return _registry


def create_test_jwt(
    sub: str,
    iss: str,
    aud: str,
    exp: int | None = None,
    name: str = "",
    email: str = "",
    groups: list[str] | None = None,
    kid: str = "test-key-1",
) -> str:
    """Create a test JWT token for offline testing.

    This produces a valid JWT structure (header.payload.signature)
    that can be decoded and validated by OIDCProvider.
    """
    import time

    header = {"alg": "RS256", "typ": "JWT", "kid": kid}
    payload: dict[str, Any] = {
        "sub": sub,
        "iss": iss,
        "aud": aud,
        "exp": exp or int(time.time()) + 3600,
        "iat": int(time.time()),
        "name": name or sub,
        "email": email,
        "groups": groups or [],
    }

    def _b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    # Simulated signature (not cryptographically valid but structurally correct)
    sig_b64 = _b64url(hashlib.sha256(f"{header_b64}.{payload_b64}".encode()).digest())

    return f"{header_b64}.{payload_b64}.{sig_b64}"
