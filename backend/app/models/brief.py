"""
ResQNet AI - Command Brief Document Model
AI-generated operational briefings for emergency coordinators.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BriefTimeRange(BaseModel):
    from_time: datetime
    to_time: datetime


class CommandBriefModel(BaseModel):
    """Command brief document model for MongoDB."""
    brief_id: str
    generated_by: str  # user_id or "system"
    time_range: BriefTimeRange
    situation_overview: str = ""
    priority_incidents: List[str] = Field(default_factory=list)  # incident_ids
    recommended_actions: List[Dict[str, Any]] = Field(default_factory=list)
    resource_deployment: Dict[str, Any] = Field(default_factory=dict)
    risks: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    raw_markdown: str = ""
    pdf_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
