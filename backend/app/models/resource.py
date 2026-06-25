"""
ResQNet AI - Resource Document Model
Represents deployable emergency resources (vehicles, teams, supplies, facilities).
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ResourceType(str, Enum):
    AMBULANCE = "ambulance"
    RESCUE_BOAT = "rescue_boat"
    MEDICAL_TEAM = "medical_team"
    VOLUNTEER_TEAM = "volunteer_team"
    FOOD_SUPPLY = "food_supply"
    WATER_SUPPLY = "water_supply"
    MEDICAL_KIT = "medical_kit"
    SHELTER = "shelter"
    GENERATOR = "generator"
    POLICE_UNIT = "police_unit"
    FIRE_UNIT = "fire_unit"
    HELICOPTER = "helicopter"
    DRONE = "drone"


class ResourceStatus(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    ON_SCENE = "on_scene"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class GeoJSONPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(
        ..., description="[longitude, latitude]", min_length=2, max_length=2
    )


class ResourceLocation(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(..., description="[longitude, latitude]")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ResourceCapacity(BaseModel):
    total: int = 0
    current_load: int = 0
    unit: str = "units"  # people, kg, liters, units

    @property
    def available_capacity(self) -> int:
        return max(0, self.total - self.current_load)

    @property
    def utilization_percent(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.current_load / self.total) * 100


class DeploymentRecord(BaseModel):
    incident_id: str
    deployed_at: datetime = Field(default_factory=datetime.utcnow)
    returned_at: Optional[datetime] = None
    outcome: Optional[str] = None


class ResourceModel(BaseModel):
    """Complete resource document model for MongoDB."""
    resource_id: str
    type: ResourceType
    name: str
    status: ResourceStatus = ResourceStatus.AVAILABLE
    location: ResourceLocation
    capacity: ResourceCapacity = Field(default_factory=ResourceCapacity)
    capabilities: List[str] = Field(default_factory=list)
    assigned_incident_id: Optional[str] = None
    base_location: ResourceLocation
    organization: str = ""
    contact: Optional[str] = None
    deployment_history: List[DeploymentRecord] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}
