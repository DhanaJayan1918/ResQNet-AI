"""
ResQNet AI - Hospital Schemas
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class UpdateHospitalRequest(BaseModel):
    """Update hospital capacity/status."""
    available_beds: Optional[int] = Field(default=None, ge=0)
    icu_beds_available: Optional[int] = Field(default=None, ge=0)
    er_current_load: Optional[int] = Field(default=None, ge=0)
    ambulances_available: Optional[int] = Field(default=None, ge=0)
    status: Optional[str] = None


class HospitalResponse(BaseModel):
    """Hospital details."""
    id: str
    hospital_id: str
    name: str
    address: str
    location: dict
    total_beds: int
    available_beds: int
    icu_beds_total: int
    icu_beds_available: int
    er_capacity: int
    er_current_load: int
    er_load_percent: float
    bed_utilization_percent: float
    specialties: List[str]
    ambulances_available: int
    status: str
