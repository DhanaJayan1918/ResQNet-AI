"""
ResQNet AI - JWT Authentication Middleware
Provides dependency injection for protected routes with role-based access control.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, ExpiredSignatureError

from app.services.auth_service import decode_token, get_user_by_id
from app.db.redis_client import is_token_blacklisted
from app.models.user import UserRole, has_minimum_role
import logging

logger = logging.getLogger(__name__)

# Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Extract and validate the current user from the JWT bearer token.
    Returns the user document dict with '_id' as string.
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Check if token is blacklisted
    jti = payload.get("jti", "")
    if await is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    # Fetch user
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Convert ObjectId to string for serialization
    user["_id"] = str(user["_id"])
    return user


def require_role(minimum_role: UserRole):
    """
    Dependency factory that enforces a minimum role level.
    Usage: current_user = Depends(require_role(UserRole.COORDINATOR))
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        user_role = current_user.get("role", "citizen")
        if not has_minimum_role(user_role, minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {minimum_role.value} or higher",
            )
        return current_user

    return role_checker


# Pre-built dependency shortcuts for common role requirements
require_citizen = require_role(UserRole.CITIZEN)
require_volunteer = require_role(UserRole.VOLUNTEER)
require_field_officer = require_role(UserRole.FIELD_OFFICER)
require_coordinator = require_role(UserRole.COORDINATOR)
require_gov_admin = require_role(UserRole.GOV_ADMIN)
require_super_admin = require_role(UserRole.SUPER_ADMIN)
