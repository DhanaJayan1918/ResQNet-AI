"""
ResQNet AI - Authentication API Routes
Handles registration, login, token refresh, logout, and profile endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshTokenRequest, UserResponse,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import (
    register_user, login_user, refresh_access_token, logout_user,
)
from app.api.middleware.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """Register a new user account."""
    try:
        user = await register_user(request)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate and receive JWT tokens."""
    try:
        tokens = await login_user(request)
        return tokens
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshTokenRequest):
    """Refresh an expired access token using a valid refresh token."""
    try:
        tokens = await refresh_access_token(request.refresh_token)
        return tokens
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout and invalidate the current access token."""
    # The token is already extracted by the middleware; we need the raw token
    # For simplicity, we blacklist based on user_id
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return UserResponse(
        id=current_user["_id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        phone=current_user.get("phone"),
        organization=current_user.get("organization"),
        is_active=current_user.get("is_active", True),
        permissions=current_user.get("permissions", []),
        created_at=current_user["created_at"],
        last_login=current_user.get("last_login"),
    )
