"""
ResQNet AI - Incident Document Model
Core model representing emergency incidents with AI analysis, priority scoring,
impact estimation, and response tracking.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class IncidentType(str, Enum):
    FLOOD = "flood"
    EARTHQUAKE = "earthquake"
    WILDFIRE = "wildfire"
    MEDICAL = "medical"
    INFRASTRUCTURE = "infrastructure"
    SHELTER_OVERLOAD = "shelter_overload"
    POWER_OUTAGE = "power_outage"
    EVACUATION = "evacuation"
    CHEMICAL = "chemical"
    COLLAPSE = "collapse"
    LANDSLIDE = "landslide"
    CYCLONE = "cyclone"
    OTHER = "other"


class IncidentStatus(str, Enum):
    NEW = "new"
    PROCESSING = "processing"
    VERIFIED = "verified"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DUPLICATE = "duplicate"


class Severity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    CATASTROPHIC = "catastrophic"


class Urgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    IMMEDIATE = "immediate"


class SourceType(str, Enum):
    CITIZEN = "citizen"
    FIELD_OFFICER = "field_officer"
    HOSPITAL = "hospital"
    SHELTER = "shelter"
    NGO = "ngo"
    IOT_SENSOR = "iot_sensor"
    API = "api"
    CSV_IMPORT = "csv_import"


class SubmissionChannel(str, Enum):
    WEB = "web"
    MOBILE = "mobile"
    API = "api"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class ResourceUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    IMMEDIATE = "immediate"


class AssignmentStatus(str, Enum):
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    RETURNING = "returning"


# ---- Nested Models ----

class GeoJSONPoint(BaseModel):
    """GeoJSON Point for location data."""
    type: str = "Point"
    coordinates: List[float] = Field(
        ..., description="[longitude, latitude]", min_length=2, max_length=2
    )


class IncidentLocation(BaseModel):
    """Location details for an incident."""
    type: str = "Point"
    coordinates: List[float] = Field(
        ..., description="[longitude, latitude]"
    )
    address: Optional[str] = None
    landmark: Optional[str] = None
    region: Optional[str] = None
    accuracy_meters: Optional[float] = None


class IncidentSource(BaseModel):
    """Source information for the report."""
    type: SourceType = SourceType.CITIZEN
    reporter_id: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_contact: Optional[str] = None
    submission_channel: SubmissionChannel = SubmissionChannel.WEB


class RawReport(BaseModel):
    """Raw report data as submitted."""
    text: str
    images: List[str] = Field(default_factory=list)
    audio_transcript: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VulnerablePopulations(BaseModel):
    """Breakdown of vulnerable populations affected."""
    children: int = 0
    elderly: int = 0
    disabled: int = 0
    pregnant: int = 0
    chronic_illness: int = 0

    @property
    def total(self) -> int:
        return self.children + self.elderly + self.disabled + self.pregnant + self.chronic_illness


class ResourceRequirement(BaseModel):
    """A specific resource need identified by AI."""
    resource_type: str
    quantity: int = 1
    urgency: ResourceUrgency = ResourceUrgency.MEDIUM


class AIAnalysis(BaseModel):
    """AI-generated analysis of the incident."""
    incident_type: IncidentType = IncidentType.OTHER
    severity: Severity = Severity.MODERATE
    urgency: Urgency = Urgency.MEDIUM
    people_affected: int = 0
    vulnerable_populations: VulnerablePopulations = Field(default_factory=VulnerablePopulations)
    resource_requirements: List[ResourceRequirement] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str = ""
    processed_at: Optional[datetime] = None

    model_config = {"use_enum_values": True}


class ImpactEstimate(BaseModel):
    """Estimated impact of the incident."""
    medical_demand: int = 0
    shelter_demand: int = 0
    food_water_demand: int = 0
    rescue_demand: int = 0
    infrastructure_damage_score: float = Field(default=0.0, ge=0.0, le=10.0)
    estimated_duration_hours: float = 0.0
    economic_impact_estimate: Optional[float] = None


class PriorityFactors(BaseModel):
    """Individual factors contributing to priority score."""
    severity_score: float = 0.0
    urgency_score: float = 0.0
    people_affected_score: float = 0.0
    vulnerability_score: float = 0.0
    resource_scarcity_score: float = 0.0
    accessibility_score: float = 0.0
    shelter_load_score: float = 0.0
    hospital_load_score: float = 0.0


class Priority(BaseModel):
    """Computed priority information."""
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    rank: int = 0
    factors: PriorityFactors = Field(default_factory=PriorityFactors)
    explanation: str = ""
    calculated_at: Optional[datetime] = None


class AssignedResource(BaseModel):
    """A resource assigned to this incident."""
    resource_id: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    eta_minutes: float = 0.0
    status: AssignmentStatus = AssignmentStatus.DISPATCHED

    model_config = {"use_enum_values": True}


class ResponsePlan(BaseModel):
    """AI-generated response plan."""
    recommended_actions: List[str] = Field(default_factory=list)
    resource_assignments: List[Dict[str, Any]] = Field(default_factory=list)
    expected_impact: str = ""
    alternatives: List[str] = Field(default_factory=list)
    explanation: str = ""
    generated_at: Optional[datetime] = None


class TimelineEvent(BaseModel):
    """An event in the incident timeline."""
    event: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str = "system"
    details: Optional[str] = None


# ---- Main Incident Model ----

class IncidentModel(BaseModel):
    """Complete incident document model for MongoDB."""
    incident_id: str
    status: IncidentStatus = IncidentStatus.NEW
    source: IncidentSource = Field(default_factory=IncidentSource)
    raw_report: RawReport
    location: IncidentLocation
    ai_analysis: AIAnalysis = Field(default_factory=AIAnalysis)
    impact_estimate: ImpactEstimate = Field(default_factory=ImpactEstimate)
    priority: Priority = Field(default_factory=Priority)
    duplicate_group_id: Optional[str] = None
    assigned_resources: List[AssignedResource] = Field(default_factory=list)
    response_plan: ResponsePlan = Field(default_factory=ResponsePlan)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}
