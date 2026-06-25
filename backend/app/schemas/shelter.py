"""
ResQNet AI - Shelter Schemas
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class UpdateShelterRequest(BaseModel):
    """Update shelter status/occupancy."""
    current_occupancy: Optional[int] = Field(default=None, ge=0)
    status: Optional[str] = None
    food_days_remaining: Optional[float] = None
    water_days_remaining: Optional[float] = None
    medical_kits: Optional[int] = None
    blankets: Optional[int] = None


class ShelterResponse(BaseModel):
    """Shelter details."""
    id: str
    shelter_id: str
    name: str
    address: str
    location: dict
    total_capacity: int
    current_occupancy: int
    occupancy_percentage: float
    available_capacity: int
    status: str
    facilities: List[str]
    contact_person: str
    supplies: dict
