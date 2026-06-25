"""
ResQNet AI - Hospital Document Model
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class HospitalStatus(str, Enum):
    OPERATIONAL = "operational"
    LIMITED = "limited"
    OVERWHELMED = "overwhelmed"
    EVACUATING = "evacuating"
    OFFLINE = "offline"


class HospitalModel(BaseModel):
    """Hospital document model for MongoDB."""
    hospital_id: str
    name: str
    location: dict  # GeoJSON Point
    address: str = ""
    total_beds: int = 0
    available_beds: int = 0
    icu_beds_total: int = 0
    icu_beds_available: int = 0
    er_capacity: int = 0
    er_current_load: int = 0
    specialties: List[str] = Field(default_factory=list)
    blood_bank_status: Dict[str, int] = Field(default_factory=dict)
    ambulances_available: int = 0
    status: HospitalStatus = HospitalStatus.OPERATIONAL
    contact: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}

    @property
    def bed_utilization_percent(self) -> float:
        if self.total_beds == 0:
            return 0.0
        return ((self.total_beds - self.available_beds) / self.total_beds) * 100

    @property
    def er_load_percent(self) -> float:
        if self.er_capacity == 0:
            return 0.0
        return (self.er_current_load / self.er_capacity) * 100
