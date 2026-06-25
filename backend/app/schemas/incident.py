"""
ResQNet AI - Incident Schemas
Request/response DTOs for incident endpoints.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.incident import (
    IncidentType, IncidentStatus, Severity, Urgency,
    SourceType, SubmissionChannel,
)


class CreateIncidentRequest(BaseModel):
    """Submit a new incident report."""
    text: str = Field(..., min_length=10, max_length=5000, description="Incident description")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    landmark: Optional[str] = None
    images: List[str] = Field(default_factory=list, description="Image file paths/URLs")
    source_type: SourceType = SourceType.CITIZEN
    submission_channel: SubmissionChannel = SubmissionChannel.WEB
    reporter_name: Optional[str] = None
    reporter_contact: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateIncidentRequest(BaseModel):
    """Update an incident's status or details."""
    status: Optional[IncidentStatus] = None
    notes: Optional[str] = None


class IncidentFilterParams(BaseModel):
    """Filter parameters for incident listing."""
    status: Optional[IncidentStatus] = None
    incident_type: Optional[IncidentType] = None
    severity: Optional[Severity] = None
    urgency: Optional[Urgency] = None
    min_priority: Optional[float] = None
    max_priority: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None  # For geo-proximity queries
    source_type: Optional[SourceType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    def to_mongo_filter(self) -> dict:
        """Convert filter params to MongoDB query filter."""
        query = {}
        if self.status:
            query["status"] = self.status.value
        if self.incident_type:
            query["ai_analysis.incident_type"] = self.incident_type.value
        if self.severity:
            query["ai_analysis.severity"] = self.severity.value
        if self.urgency:
            query["ai_analysis.urgency"] = self.urgency.value
        if self.min_priority is not None:
            query.setdefault("priority.score", {})["$gte"] = self.min_priority
        if self.max_priority is not None:
            query.setdefault("priority.score", {})["$lte"] = self.max_priority
        if self.source_type:
            query["source.type"] = self.source_type.value
        if self.date_from:
            query.setdefault("created_at", {})["$gte"] = self.date_from
        if self.date_to:
            query.setdefault("created_at", {})["$lte"] = self.date_to

        # Geospatial filter
        if self.latitude is not None and self.longitude is not None and self.radius_km:
            query["location"] = {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [self.longitude, self.latitude],
                    },
                    "$maxDistance": self.radius_km * 1000,  # Convert km to meters
                }
            }

        return query


class IncidentSummaryResponse(BaseModel):
    """Abbreviated incident info for lists."""
    id: str
    incident_id: str
    status: str
    incident_type: str
    severity: str
    urgency: str
    priority_score: float
    people_affected: int
    location: Dict[str, Any]
    address: Optional[str]
    text_preview: str
    created_at: datetime
    updated_at: datetime


class IncidentDetailResponse(BaseModel):
    """Full incident details."""
    id: str
    incident_id: str
    status: str
    source: Dict[str, Any]
    raw_report: Dict[str, Any]
    location: Dict[str, Any]
    ai_analysis: Dict[str, Any]
    impact_estimate: Dict[str, Any]
    priority: Dict[str, Any]
    duplicate_group_id: Optional[str]
    assigned_resources: List[Dict[str, Any]]
    response_plan: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class BulkImportRequest(BaseModel):
    """Bulk import incident reports."""
    incidents: List[CreateIncidentRequest]


class MergeIncidentsRequest(BaseModel):
    """Merge duplicate incidents into a primary."""
    primary_incident_id: str
    duplicate_incident_ids: List[str]
