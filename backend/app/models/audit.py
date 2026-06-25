"""
ResQNet AI - Audit Log Document Model
Every AI decision, resource allocation, and significant action is logged for transparency.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AuditEntityType(str, Enum):
    INCIDENT = "incident"
    RESOURCE = "resource"
    SHELTER = "shelter"
    HOSPITAL = "hospital"
    USER = "user"
    SYSTEM = "system"


class AIDecisionLog(BaseModel):
    """Details of an AI-driven decision for auditability."""
    model: str = ""
    input_summary: str = ""
    output_summary: str = ""
    confidence: float = 0.0
    reasoning: str = ""


class AuditLogModel(BaseModel):
    """Audit log document for MongoDB."""
    action: str
    entity_type: AuditEntityType
    entity_id: str
    actor_id: Optional[str] = None
    actor_role: str = "system"
    details: Dict[str, Any] = Field(default_factory=dict)
    ai_decision: Optional[AIDecisionLog] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}
