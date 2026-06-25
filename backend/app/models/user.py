"""
ResQNet AI - User Document Model
Defines the User model for MongoDB storage with role-based access control.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class UserRole(str, Enum):
    """User roles with hierarchical access levels."""
    CITIZEN = "citizen"
    VOLUNTEER = "volunteer"
    HOSPITAL = "hospital"
    SHELTER_MANAGER = "shelter_manager"
    FIELD_OFFICER = "field_officer"
    COORDINATOR = "coordinator"
    GOV_ADMIN = "gov_admin"
    SUPER_ADMIN = "super_admin"


# Role hierarchy for permission checks (higher index = more access)
ROLE_HIERARCHY = {
    UserRole.CITIZEN: 0,
    UserRole.VOLUNTEER: 1,
    UserRole.HOSPITAL: 2,
    UserRole.SHELTER_MANAGER: 2,
    UserRole.FIELD_OFFICER: 3,
    UserRole.COORDINATOR: 4,
    UserRole.GOV_ADMIN: 5,
    UserRole.SUPER_ADMIN: 6,
}


class GeoJSONPolygon(BaseModel):
    """GeoJSON Polygon for assigned regions."""
    type: str = "Polygon"
    coordinates: List[List[List[float]]] = []


class UserModel(BaseModel):
    """User document model for MongoDB."""
    email: EmailStr
    password_hash: str
    full_name: str
    role: UserRole = UserRole.CITIZEN
    phone: Optional[str] = None
    organization: Optional[str] = None
    assigned_region: Optional[GeoJSONPolygon] = None
    is_active: bool = True
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    model_config = {"use_enum_values": True}


def has_minimum_role(user_role: str, minimum_role: UserRole) -> bool:
    """Check if a user's role meets the minimum required role level."""
    user_level = ROLE_HIERARCHY.get(UserRole(user_role), -1)
    required_level = ROLE_HIERARCHY.get(minimum_role, 99)
    return user_level >= required_level
