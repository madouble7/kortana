"""
Unified Authentication System for Kor'tana Backend
Consolidated JWT-based authentication with comprehensive user management
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt as jose_jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

# Configuration - use environment variables for security
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-with-secret-key-from-env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ==================== Pydantic Models ====================

class Token(BaseModel):
    """Response model for token endpoints"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Data extracted from JWT token"""
    user_id: Optional[int] = None
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    scopes: list = []

class UserResponse(BaseModel):
    """Response model for user data"""
    id: int
    email: str
    username: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserInDB(UserResponse):
    """User model for internal database operations"""
    hashed_password: str

# ==================== Password Utilities ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password for storing"""
    return pwd_context.hash(password)

# ==================== JWT Token Functions ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Payload data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token with longer expiration

    Args:
        data: Payload data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        TokenData with decoded user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id: int = payload.get("sub")
        email: str = payload.get("email")
        username: str = payload.get("username")
        role: str = payload.get("role", "user")

        if user_id is None:
            raise credentials_exception

        return TokenData(
            user_id=user_id,
            email=email,
            username=username,
            role=role,
            scopes=payload.get("scopes", [])
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
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
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
        )
