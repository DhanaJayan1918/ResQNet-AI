"""
ResQNet AI - Analytics Schemas
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DashboardOverview(BaseModel):
    """High-level stats for the command dashboard."""
    total_incidents: int
    active_incidents: int
    critical_incidents: int
    resolved_today: int
    total_resources: int
    available_resources: int
    deployed_resources: int
    total_shelters: int
    shelter_occupancy_avg: float
    total_hospitals: int
    hospital_bed_utilization_avg: float
    avg_response_time_minutes: float
    incidents_last_24h: int


class IncidentTrendData(BaseModel):
    """Incident count trends over time."""
    labels: List[str]  # time labels
    total: List[int]
    by_type: Dict[str, List[int]]
    by_severity: Dict[str, List[int]]


class ResourceUtilizationData(BaseModel):
    """Resource usage analytics."""
    by_type: Dict[str, Dict[str, int]]
    utilization_timeline: List[Dict[str, Any]]


class HeatmapPoint(BaseModel):
    """A point for the incident heatmap."""
    latitude: float
    longitude: float
    intensity: float


class HeatmapData(BaseModel):
    """Heatmap data for geographic incident visualization."""
    points: List[HeatmapPoint]
    max_intensity: float
