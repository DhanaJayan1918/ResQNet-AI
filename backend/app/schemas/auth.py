"""
ResQNet AI - Authentication Schemas
Request/response DTOs for auth endpoints.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole


class RegisterRequest(BaseModel):
    """New user registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None
    organization: Optional[str] = None
    role: UserRole = UserRole.CITIZEN


class LoginRequest(BaseModel):
    """Login credentials."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class UserResponse(BaseModel):
    """User profile response (excludes password hash)."""
    id: str
    email: str
    full_name: str
    role: str
    phone: Optional[str] = None
    organization: Optional[str] = None
    is_active: bool = True
    permissions: List[str] = []
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    """Update user profile."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    organization: Optional[str] = None
