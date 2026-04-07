"""
Authentication Router for Kor'tana Backend

Provides JWT-based authentication with:
- User registration and login
- Token generation and refresh
- Password hashing with bcrypt
- Protected route access

Author: Kor'tana Security Team
Date: January 14, 2026
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

# Import unified authentication utilities
from src.kortana.auth import (
    Token,
    TokenData,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    decode_token,
    get_current_active_user,
    get_password_hash,
    get_user_by_email,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


# ==================== Pydantic Models ====================


class UserCreate(BaseModel):
    """Request model for user registration"""

    email: EmailStr
    password: str
    confirm_password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securePassword123!",
                "confirm_password": "securePassword123!",
            }
        }


class UserLogin(BaseModel):
    """Request model for user login"""

    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {"email": "user@example.com", "password": "securePassword123!"}
        }


class UserResponse(BaseModel):
    """Response model for user data"""

    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "role": "user",
                "is_active": True,
                "created_at": "2026-01-14T21:00:00Z",
            }
        }


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh operations"""

    refresh_token: str


class MessageResponse(BaseModel):
    """Generic message response"""

    message: str


# ==================== API Endpoints ====================


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate) -> UserResponse:
    """
    Register a new user using unified auth system
    """
    db_user = create_user(user_data)

    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        role=db_user.role,
        is_active=db_user.is_active,
        created_at=db_user.created_at,
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """
    Authenticate user and return access/refresh tokens using unified auth system
    """
    # OAuth2PasswordRequestForm uses 'username' field for email
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated"
        )

    # Create tokens using unified functions
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role}
    )

    refresh_token = create_refresh_token(data={"sub": user.id, "email": user.email})

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest) -> Token:
    """
    Refresh access token using refresh token via unified auth system
    """
    # Use unified decode_token
    token_data = decode_token(request.refresh_token)

    if token_data.token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user to verify active status
    user = get_user_by_email(token_data.email)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new tokens using unified functions
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role}
    )

    new_refresh_token = create_refresh_token(data={"sub": user.id, "email": user.email})

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: TokenData = Depends(get_current_active_user),
) -> UserResponse:
    """
    Get current authenticated user's information
    """
    if current_user.email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )

    user = get_user_by_email(current_user.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Explicitly map to UserResponse for type safety
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: TokenData = Depends(get_current_active_user),
) -> MessageResponse:
    """
    Logout current user
    """
    # In production: Add token to blacklist in Redis
    return MessageResponse(message="Successfully logged out")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    current_password: str,
    new_password: str,
    confirm_password: str,
    current_user: TokenData = Depends(get_current_active_user),
) -> MessageResponse:
    """
    Change user password using unified password utilities
    """
    if current_user.email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )

    user = get_user_by_email(current_user.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify current password using unified verify_password
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password
    if new_password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="New passwords do not match"
        )

    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )

    # Update password using unified get_password_hash
    user["hashed_password"] = get_password_hash(new_password)

    return MessageResponse(message="Password successfully changed")


@router.post("/deactivate", response_model=MessageResponse)
async def deactivate_account(
    current_user: TokenData = Depends(get_current_active_user),
) -> MessageResponse:
    """
    Deactivate current user account
    """
    if current_user.email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )

    user = get_user_by_email(current_user.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_active = False

    return MessageResponse(message="Account successfully deactivated")
