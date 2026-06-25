"""
ResQNet AI - Audit Logging Service
Logs all significant actions and AI decisions for transparency and compliance.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from app.db.mongodb import get_database
from app.models.audit import AuditLogModel, AuditEntityType, AIDecisionLog
import logging

logger = logging.getLogger(__name__)


async def log_action(
    action: str,
    entity_type: AuditEntityType,
    entity_id: str,
    actor_id: Optional[str] = None,
    actor_role: str = "system",
    details: Optional[Dict[str, Any]] = None,
    ai_decision: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Log an action to the audit trail.
    Returns the audit log document ID.
    """
    db = get_database()

    audit_entry = AuditLogModel(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        actor_role=actor_role,
        details=details or {},
        ai_decision=AIDecisionLog(**ai_decision) if ai_decision else None,
        timestamp=datetime.utcnow(),
    )

    result = await db.audit_logs.insert_one(audit_entry.model_dump())
    logger.debug(f"Audit log: {action} on {entity_type}:{entity_id}")
    return str(result.inserted_id)


async def log_ai_decision(
    action: str,
    entity_type: AuditEntityType,
    entity_id: str,
    model: str,
    input_summary: str,
    output_summary: str,
    confidence: float,
    reasoning: str,
    actor_id: Optional[str] = None,
) -> str:
    """Convenience wrapper for logging AI decisions."""
    return await log_action(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        actor_role="ai_agent",
        ai_decision={
            "model": model,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "confidence": confidence,
            "reasoning": reasoning,
        },
    )


async def get_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
) -> list:
    """Retrieve audit logs with optional filtering."""
    db = get_database()
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id

    cursor = db.audit_logs.find(query).sort("timestamp", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(length=limit)

    # Convert ObjectId to string
    for log in logs:
        log["_id"] = str(log["_id"])

    return logs
