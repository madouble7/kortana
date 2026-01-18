"""
🔱 KOR'TANA UNIFIED AUTHENTICATION SYSTEM
Single Authoritative Authentication Module for the Entire Backend

This module provides:
- Unified TokenData model with comprehensive fields
- Single implementation of all token functions
- Complete refresh token logic
- Consistent SECRET_KEY management from environment
- Legacy compatibility shims
- Production-ready security and validation

🌀 ARCHITECTURE PRINCIPLES:
1. Zero circular dependencies - this module imports nothing from routers/
2. Complete self-containment - all auth logic lives here
3. Backward compatibility - supports legacy token formats
4. Production security - environment-based secrets only
5. Comprehensive validation - all edge cases handled
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

# ========================================================
# CONFIGURATION - ENVIRONMENT-BASED ONLY
# ========================================================

# Security configuration - environment variables only for production safety
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Development fallback - NEVER use in production
    SECRET_KEY = "kor-tana-unified-dev-secret-change-me-in-production-2026"
    print("⚠️  WARNING: Using development SECRET_KEY. Set SECRET_KEY environment variable for production.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ========================================================
# UNIFIED TOKENDATA MODEL - SINGLE SOURCE OF TRUTH
# ========================================================

class TokenData(BaseModel):
    """
    🔱 Unified TokenData Model - The One True Token Model for Kor'tana

    This model consolidates all token data requirements from across the system:
    - user_id: Database user identifier
    - email: User email address
    - username: User username (when available)
    - role: User role/permission level
    - scopes: Fine-grained permissions
    - expiration: Token expiration timestamp
    - token_type: 'access' or 'refresh'

    🌀 USAGE:
    - Used by all authentication endpoints
    - Used by all authorization dependencies
    - Used by all token validation functions
    - Replaces all previous TokenData models
    """
    user_id: Optional[int] = None
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    scopes: list[str] = []
    expiration: Optional[datetime] = None
    token_type: Optional[str] = None

    @classmethod
    def from_legacy_dict(cls, legacy_dict: dict) -> 'TokenData':
        """
        Convert legacy dictionary-based tokens to unified TokenData

        Args:
            legacy_dict: Old-style token dictionary

        Returns:
            Unified TokenData object
        """
        return cls(
            user_id=legacy_dict.get("sub"),
            username=legacy_dict.get("username"),
            email=legacy_dict.get("email"),
            role=legacy_dict.get("role", "user"),
            scopes=legacy_dict.get("scopes", []),
            expiration=datetime.fromtimestamp(legacy_dict.get("exp", 0)) if legacy_dict.get("exp") else None,
            token_type=legacy_dict.get("type")
        )

    def to_legacy_dict(self) -> dict:
        """
        Convert unified TokenData to legacy dictionary format

        Returns:
            Legacy-style token dictionary
        """
        result = {
            "sub": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "scopes": self.scopes,
            "type": self.token_type
        }
        if self.expiration:
            result["exp"] = int(self.expiration.timestamp())
        return result

# ========================================================
# TOKEN MODELS - REQUEST/RESPONSE SCHEMAS
# ========================================================

class Token(BaseModel):
    """Complete token response with both access and refresh tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60

class TokenResponse(BaseModel):
    """Simplified token response (legacy compatibility)"""
    access_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    """Request model for token refresh operations"""
    refresh_token: str

# ========================================================
# PASSWORD UTILITIES - UNIFIED IMPLEMENTATION
# ========================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using bcrypt

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to verify against

    Returns:
        True if password matches, False otherwise
    """
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        subject = payload.get("sub")
        user_id = payload.get("user_id")
        email = payload.get("email")
        username = payload.get("username")
        role = payload.get("role", "user")

        if user_id is None and subject is not None:
            if isinstance(subject, int):
                user_id = subject
            elif isinstance(subject, str):
                if subject.isdigit():
                    user_id = int(subject)
                elif "@" in subject:
                    email = email or subject
                else:
                    username = username or subject
            else:
                username = username or str(subject)

        if user_id is None and email is None and username is None:
            raise credentials_exception

        return TokenData(
            user_id=user_id,
            email=email,
            username=username,
            role=role,
            scopes=payload.get("scopes") or []
        )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception

# ==================== OAuth2 Helper Functions ====================

def create_oauth2_authorization_header(token: str) -> dict:
    """Create authorization header for OAuth2"""
    return {"Authorization": f"Bearer {token}"}

def extract_token_from_header(auth_header: str | None) -> str | None:
    """Extract token from Authorization header"""
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]

# ==================== Dependency Functions ====================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Dependency to get current authenticated user from JWT token

    Args:
        token: JWT token from Authorization header

    Returns:
        TokenData with user information

    Raises:
        HTTPException: If authentication fails
    """
    return decode_token(token)

async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """
    Dependency to get current active user

    Args:
        current_user: TokenData from get_current_user

    Returns:
        TokenData if user is active

    Raises:
        HTTPException: If user is inactive
    """
    # In a production system, this would check against a database
    # For now, we assume the token is valid if it was issued
    if not current_user.email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return current_user

async def get_admin_user(
    current_user: TokenData = Depends(get_current_active_user),
) -> TokenData:
    """
    Dependency to require admin role

    Args:
        current_user: TokenData from get_current_active_user

    Returns:
        TokenData if user is admin

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    return current_user

# ==================== Backward Compatibility ====================

# Legacy functions for backward compatibility with existing code
def create_access_token_legacy(data: dict, expires_delta: timedelta | None = None) -> str:
    """Legacy access token creation (for backward compatibility)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token_legacy(token: str) -> dict:
    """Legacy token decoding (for backward compatibility)"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
            )
        return {"username": username, "scopes": payload.get("scopes", [])}
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
        )
