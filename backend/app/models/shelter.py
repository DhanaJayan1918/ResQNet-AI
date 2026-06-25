"""
ResQNet AI - Shelter Document Model
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ShelterStatus(str, Enum):
    OPEN = "open"
    FULL = "full"
    CLOSED = "closed"
    EVACUATING = "evacuating"


class ShelterSupplies(BaseModel):
    food_days_remaining: float = 0.0
    water_days_remaining: float = 0.0
    medical_kits: int = 0
    blankets: int = 0


class ShelterModel(BaseModel):
    """Shelter document model for MongoDB."""
    shelter_id: str
    name: str
    location: dict  # GeoJSON Point
    address: str = ""
    total_capacity: int = 0
    current_occupancy: int = 0
    status: ShelterStatus = ShelterStatus.OPEN
    facilities: List[str] = Field(default_factory=list)
    contact_person: str = ""
    contact_phone: str = ""
    manager_id: Optional[str] = None
    supplies: ShelterSupplies = Field(default_factory=ShelterSupplies)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}

    @property
    def occupancy_percentage(self) -> float:
        if self.total_capacity == 0:
            return 0.0
        return (self.current_occupancy / self.total_capacity) * 100

    @property
    def available_capacity(self) -> int:
        return max(0, self.total_capacity - self.current_occupancy)
