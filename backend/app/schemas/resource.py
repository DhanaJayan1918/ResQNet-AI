"""
ResQNet AI - Resource Schemas
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.resource import ResourceType, ResourceStatus


class CreateResourceRequest(BaseModel):
    """Register a new resource."""
    type: ResourceType
    name: str = Field(..., min_length=2, max_length=200)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    capacity_total: int = Field(default=1, ge=0)
    capacity_unit: str = "units"
    capabilities: List[str] = Field(default_factory=list)
    organization: str = ""
    contact: Optional[str] = None


class UpdateResourceRequest(BaseModel):
    """Update resource status or location."""
    status: Optional[ResourceStatus] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    current_load: Optional[int] = Field(default=None, ge=0)
    assigned_incident_id: Optional[str] = None


class ResourceSummaryResponse(BaseModel):
    """Resource list item."""
    id: str
    resource_id: str
    type: str
    name: str
    status: str
    location: Dict[str, Any]
    capacity_total: int
    capacity_available: int
    organization: str
    assigned_incident_id: Optional[str]


class ResourceInventoryResponse(BaseModel):
    """Aggregated resource inventory summary."""
    total_resources: int
    available: int
    assigned: int
    in_transit: int
    on_scene: int
    maintenance: int
    offline: int
    by_type: Dict[str, Dict[str, int]]
