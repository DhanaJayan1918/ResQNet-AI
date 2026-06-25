"""
ResQNet AI - Authentication Service
Handles user registration, login, JWT token management, and password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import uuid

import bcrypt
from jose import jwt, JWTError, ExpiredSignatureError

from app.config import get_settings
from app.db.mongodb import get_database
from app.db.redis_client import blacklist_token, is_token_blacklisted
from app.models.user import UserModel, UserRole
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse,
)
import logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: str, role: str) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token (longer-lived)."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token. Raises on failure."""
    settings = get_settings()
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


async def register_user(request: RegisterRequest) -> UserResponse:
    """Register a new user."""
    db = get_database()

    # Check if email already exists
    existing = await db.users.find_one({"email": request.email})
    if existing:
        raise ValueError("Email already registered")

    # Create user document
    user = UserModel(
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role=request.role,
        phone=request.phone,
        organization=request.organization,
    )

    result = await db.users.insert_one(user.model_dump())
    user_id = str(result.inserted_id)

    logger.info(f"User registered: {request.email} (role: {request.role})")

    return UserResponse(
        id=user_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        phone=user.phone,
        organization=user.organization,
        is_active=user.is_active,
        permissions=user.permissions,
        created_at=user.created_at,
        last_login=user.last_login,
    )


async def login_user(request: LoginRequest) -> TokenResponse:
    """Authenticate user and return JWT tokens."""
    db = get_database()
    settings = get_settings()

    # Find user
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise ValueError("Invalid email or password")

    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        raise ValueError("Invalid email or password")

    # Check active status
    if not user.get("is_active", True):
        raise ValueError("Account is deactivated")

    user_id = str(user["_id"])
    role = user["role"]

    # Generate tokens
    access_token = create_access_token(user_id, role)
    refresh_token = create_refresh_token(user_id)

    # Update last login
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}},
    )

    logger.info(f"User logged in: {request.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh_access_token(refresh_token: str) -> TokenResponse:
    """Generate a new access token using a valid refresh token."""
    settings = get_settings()

    try:
        payload = decode_token(refresh_token)
    except ExpiredSignatureError:
        raise ValueError("Refresh token expired")
    except JWTError:
        raise ValueError("Invalid refresh token")

    if payload.get("type") != "refresh":
        raise ValueError("Invalid token type")

    # Check if token is blacklisted
    jti = payload.get("jti", "")
    if await is_token_blacklisted(jti):
        raise ValueError("Token has been revoked")

    user_id = payload["sub"]

    # Fetch user to get current role
    db = get_database()
    from bson import ObjectId
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError("User not found")

    # Generate new access token
    access_token = create_access_token(user_id, user["role"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,  # Return same refresh token
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def logout_user(token: str) -> None:
    """Blacklist the current access token."""
    try:
        payload = decode_token(token)
        jti = payload.get("jti", "")
        exp = payload.get("exp", 0)
        # Calculate remaining TTL
        remaining = max(0, int(exp - datetime.now(timezone.utc).timestamp()))
        await blacklist_token(jti, remaining)
        logger.info(f"Token blacklisted: {jti[:8]}...")
    except JWTError:
        pass  # Token already invalid, no need to blacklist


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user by ID."""
    db = get_database()
    from bson import ObjectId
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        return user
    except Exception:
        return None
