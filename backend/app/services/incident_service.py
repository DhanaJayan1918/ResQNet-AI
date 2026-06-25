"""
ResQNet AI - Incident Service
Handles all business logic, validation, DB query construction, and workflow state changes.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.db.mongodb import get_database
from app.models.incident import (
    IncidentModel, IncidentStatus, IncidentLocation, IncidentSource,
    RawReport, AIAnalysis, ImpactEstimate, Priority, PriorityFactors,
    TimelineEvent, VulnerablePopulations, ResourceRequirement,
    ResourceUrgency, Severity, Urgency, IncidentType, ResponsePlan,
)
from app.schemas.incident import (
    CreateIncidentRequest, UpdateIncidentRequest, BulkImportRequest,
    MergeIncidentsRequest,
)
from app.utils.id_generator import generate_incident_id
from app.services.audit_service import log_action
from app.models.audit import AuditEntityType

# AI Agents & Processing Pipeline
from app.ai.agents.incident_analyst import analyze_incident_report
from app.ai.agents.duplicate_detector import find_duplicate_incident, save_report_embedding
from app.ai.agents.impact_estimator import estimate_incident_impact
from app.ai.priority_engine import calculate_priority, recalculate_active_ranks
from app.ai.rag_engine import retrieve_relevant_sops

import logging
import re

logger = logging.getLogger(__name__)


def mock_ai_analyze(text: str) -> AIAnalysis:
    """
    A robust mock AI analyzer for Phase 2 that parses key information from text.
    Will be replaced by the actual Gemini AI agents in Phase 3.
    """
    text_lower = text.lower()
    
    # 1. Determine incident type
    incident_type = IncidentType.OTHER
    if "flood" in text_lower or "water rising" in text_lower or "submerged" in text_lower:
        incident_type = IncidentType.FLOOD
    elif "earthquake" in text_lower or "tremor" in text_lower or "quake" in text_lower:
        incident_type = IncidentType.EARTHQUAKE
    elif "fire" in text_lower or "wildfire" in text_lower or "smoke" in text_lower:
        incident_type = IncidentType.WILDFIRE
    elif "medical" in text_lower or "injury" in text_lower or "disease" in text_lower or "hospital" in text_lower or "pain" in text_lower:
        incident_type = IncidentType.MEDICAL
    elif "collapse" in text_lower or "collapsed" in text_lower or "rubble" in text_lower:
        incident_type = IncidentType.COLLAPSE
    elif "power" in text_lower or "outage" in text_lower or "electricity" in text_lower or "blackout" in text_lower:
        incident_type = IncidentType.POWER_OUTAGE
    elif "evacuation" in text_lower or "evacuate" in text_lower:
        incident_type = IncidentType.EVACUATION
    elif "chemical" in text_lower or "gas leak" in text_lower or "toxic" in text_lower:
        incident_type = IncidentType.CHEMICAL
    elif "landslide" in text_lower or "mudslide" in text_lower:
        incident_type = IncidentType.LANDSLIDE
    elif "cyclone" in text_lower or "hurricane" in text_lower or "storm" in text_lower:
        incident_type = IncidentType.CYCLONE

    # 2. Extract severity and urgency
    severity = Severity.MODERATE
    urgency = Urgency.MEDIUM
    
    if any(k in text_lower for k in ["catastrophic", "devastating", "apocalypse"]):
        severity = Severity.CATASTROPHIC
        urgency = Urgency.IMMEDIATE
    elif any(k in text_lower for k in ["critical", "dying", "trapped", "danger"]):
        severity = Severity.CRITICAL
        urgency = Urgency.IMMEDIATE
    elif any(k in text_lower for k in ["severe", "injured", "heavy", "serious"]):
        severity = Severity.HIGH
        urgency = Urgency.HIGH
    elif any(k in text_lower for k in ["mild", "minor", "small", "low"]):
        severity = Severity.LOW
        urgency = Urgency.LOW

    # 3. Estimate people affected (simple regex search for numbers)
    people_affected = 5
    numbers = re.findall(r'\b\d+\b', text_lower)
    if numbers:
        # Avoid picking up years or giant numbers
        valid_nums = [int(n) for n in numbers if 1 <= int(n) <= 10000]
        if valid_nums:
            people_affected = max(valid_nums)

    # 4. Estimate vulnerable populations
    children = int(people_affected * 0.15) if "children" in text_lower or "child" in text_lower or "school" in text_lower else 0
    elderly = int(people_affected * 0.10) if "elderly" in text_lower or "old" in text_lower or "senior" in text_lower else 0
    disabled = int(people_affected * 0.02) if "disabled" in text_lower or "wheelchair" in text_lower else 0
    pregnant = int(people_affected * 0.01) if "pregnant" in text_lower else 0
    chronic_illness = int(people_affected * 0.05) if "chronic" in text_lower or "disease" in text_lower or "medicine" in text_lower or "medication" in text_lower else 0

    vulnerable = VulnerablePopulations(
        children=max(0, children),
        elderly=max(0, elderly),
        disabled=max(0, disabled),
        pregnant=max(0, pregnant),
        chronic_illness=max(0, chronic_illness)
    )

    # 5. Determine resource requirements based on type
    resources = []
    if incident_type == IncidentType.FLOOD:
        resources.append(ResourceRequirement(resource_type="rescue_boat", quantity=2, urgency=ResourceUrgency.IMMEDIATE))
        resources.append(ResourceRequirement(resource_type="food_supply", quantity=people_affected, urgency=ResourceUrgency.HIGH))
    elif incident_type == IncidentType.COLLAPSE:
        resources.append(ResourceRequirement(resource_type="fire_unit", quantity=1, urgency=ResourceUrgency.IMMEDIATE))
        resources.append(ResourceRequirement(resource_type="medical_team", quantity=1, urgency=ResourceUrgency.IMMEDIATE))
    elif incident_type == IncidentType.MEDICAL or vulnerable.chronic_illness > 0:
        resources.append(ResourceRequirement(resource_type="medical_team", quantity=1, urgency=ResourceUrgency.IMMEDIATE))
        resources.append(ResourceRequirement(resource_type="ambulance", quantity=1, urgency=ResourceUrgency.IMMEDIATE))
    elif incident_type == IncidentType.WILDFIRE:
        resources.append(ResourceRequirement(resource_type="fire_unit", quantity=2, urgency=ResourceUrgency.IMMEDIATE))
    else:
        resources.append(ResourceRequirement(resource_type="volunteer_team", quantity=1, urgency=ResourceUrgency.MEDIUM))

    return AIAnalysis(
        incident_type=incident_type,
        severity=severity,
        urgency=urgency,
        people_affected=people_affected,
        vulnerable_populations=vulnerable,
        resource_requirements=resources,
        confidence_score=0.80,
        reasoning="Phase 2 Rule-based mock analysis",
        processed_at=datetime.utcnow()
    )


def calculate_priority_score(analysis: AIAnalysis) -> Priority:
    """
    Compute a priority score from 0 to 100 based on severity, urgency, and vulnerability.
    """
    # Map severity to base points
    severity_map = {
        Severity.LOW: 10.0,
        Severity.MODERATE: 30.0,
        Severity.HIGH: 50.0,
        Severity.CRITICAL: 80.0,
        Severity.CATASTROPHIC: 100.0,
    }
    sev_score = severity_map.get(analysis.severity, 30.0)

    # Map urgency to base points
    urgency_map = {
        Urgency.LOW: 10.0,
        Urgency.MEDIUM: 30.0,
        Urgency.HIGH: 60.0,
        Urgency.IMMEDIATE: 100.0,
    }
    urg_score = urgency_map.get(analysis.urgency, 30.0)

    # People affected score (logarithmic scale up to 20 pts)
    affected_val = min(analysis.people_affected, 1000)
    affected_score = 0.0
    if affected_val > 0:
        import math
        affected_score = min(20.0, math.log10(affected_val + 1) * 6.67)

    # Vulnerability score (up to 20 pts)
    vuln_count = analysis.vulnerable_populations.total
    vuln_score = min(20.0, vuln_count * 2.0)

    # Combine weights
    # Severity: 35%, Urgency: 35%, Affected: 15%, Vulnerability: 15%
    total_score = (sev_score * 0.35) + (urg_score * 0.35) + (affected_score) + (vuln_score)
    total_score = round(max(0.0, min(100.0, total_score)), 1)

    factors = PriorityFactors(
        severity_score=round(sev_score * 0.35, 1),
        urgency_score=round(urg_score * 0.35, 1),
        people_affected_score=round(affected_score, 1),
        vulnerability_score=round(vuln_score, 1),
        resource_scarcity_score=0.0,
        accessibility_score=0.0,
        shelter_load_score=0.0,
        hospital_load_score=0.0
    )

    return Priority(
        score=total_score,
        rank=0,
        factors=factors,
        explanation=f"Calculated base score: {total_score}. Severity: {analysis.severity}, Urgency: {analysis.urgency}.",
        calculated_at=datetime.utcnow()
    )


async def create_incident(
    request: CreateIncidentRequest,
    actor_id: Optional[str] = None,
    actor_role: str = "citizen"
) -> dict:
    """Create a new incident report, run real AI analysis, score it, and save to DB."""
    db = get_database()

    incident_id = generate_incident_id()

    # 1. Run Duplicate Detector spatiotemporal check
    duplicate_of = await find_duplicate_incident(
        text=request.text,
        latitude=request.latitude,
        longitude=request.longitude
    )

    duplicate_group_id = None
    status = IncidentStatus.NEW

    if duplicate_of:
        # Fetch primary to get/generate duplicate group id
        primary_doc = await db.incidents.find_one({"incident_id": duplicate_of})
        if primary_doc:
            duplicate_group_id = primary_doc.get("duplicate_group_id") or f"GRP-{primary_doc['incident_id']}"
            # Ensure primary has it set in MongoDB
            if not primary_doc.get("duplicate_group_id"):
                await db.incidents.update_one(
                    {"incident_id": primary_doc["incident_id"]},
                    {"$set": {"duplicate_group_id": duplicate_group_id}}
                )
            status = IncidentStatus.DUPLICATE

    # 2. AI Analysis (Analyst Agent)
    ai_analysis = await analyze_incident_report(request.text)

    # 3. Impact Estimation (Impact Estimator Agent)
    impact_estimate = await estimate_incident_impact(request.text, ai_analysis)

    # 4. Priority Score Calculation (Priority Engine)
    priority = await calculate_priority(
        analysis=ai_analysis,
        impact=impact_estimate,
        latitude=request.latitude,
        longitude=request.longitude
    )

    # 5. Retrieve SOPs via RAG and populate recommended actions
    sops = retrieve_relevant_sops(request.text, limit=3)
    recommended_actions = [
        f"[{sop['title']}] {sop['content'].split('.')[0]}."
        for sop in sops
    ]

    location = IncidentLocation(
        coordinates=[request.longitude, request.latitude],
        address=request.address,
        landmark=request.landmark,
    )

    source = IncidentSource(
        type=request.source_type,
        reporter_id=actor_id,
        reporter_name=request.reporter_name,
        reporter_contact=request.reporter_contact,
        submission_channel=request.submission_channel
    )

    raw_report = RawReport(
        text=request.text,
        images=request.images,
        metadata=request.metadata
    )

    timeline = [
        TimelineEvent(
            event="Report submitted",
            actor=actor_role,
            details="Incident report ingested into ResQNet command center."
        ),
        TimelineEvent(
            event="AI analysis completed",
            actor="system",
            details=f"Classified as {ai_analysis.incident_type} ({ai_analysis.severity})."
        ),
        TimelineEvent(
            event="Priority score calculated",
            actor="system",
            details=f"Score: {priority.score}/100"
        )
    ]

    if duplicate_of:
        timeline.append(
            TimelineEvent(
                event="Duplicate detected",
                actor="system",
                details=f"Linked to primary incident {duplicate_of} under group {duplicate_group_id}."
            )
        )

    incident_doc = IncidentModel(
        incident_id=incident_id,
        status=status,
        source=source,
        raw_report=raw_report,
        location=location,
        ai_analysis=ai_analysis,
        impact_estimate=impact_estimate,
        priority=priority,
        duplicate_group_id=duplicate_group_id,
        response_plan=ResponsePlan(
            recommended_actions=recommended_actions,
            generated_at=datetime.utcnow()
        ),
        timeline=timeline,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    doc = incident_doc.model_dump()
    result = await db.incidents.insert_one(doc)
    doc["id"] = str(result.inserted_id)

    # 6. Save embedding to ChromaDB
    await save_report_embedding(incident_id, request.text)

    # 7. Recalculate ranks for all active incidents
    await recalculate_active_ranks()

    # Log to audit trail
    await log_action(
        action="create",
        entity_type=AuditEntityType.INCIDENT,
        entity_id=incident_id,
        actor_id=actor_id,
        actor_role=actor_role,
        details={"incident_id": incident_id, "type": ai_analysis.incident_type, "severity": ai_analysis.severity}
    )

    return doc


async def get_incidents(
    query_filter: dict,
    limit: int = 50,
    skip: int = 0
) -> List[dict]:
    """Retrieve filtered, paginated incidents from MongoDB."""
    db = get_database()
    cursor = db.incidents.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    
    for doc in docs:
        doc["id"] = str(doc["_id"])
        
    return docs


async def get_total_incidents_count(query_filter: dict) -> int:
    """Retrieve count of filtered incidents from MongoDB."""
    db = get_database()
    return await db.incidents.count_documents(query_filter)


async def get_incident_by_id(incident_id: str) -> Optional[dict]:
    """Fetch an incident by its custom incident_id (or its MongoDB ObjectId string)."""
    db = get_database()
    
    # Try custom incident_id first
    doc = await db.incidents.find_one({"incident_id": incident_id})
    if not doc:
        # Try finding by MongoDB ObjectId
        try:
            doc = await db.incidents.find_one({"_id": ObjectId(incident_id)})
        except Exception:
            return None
            
    if doc:
        doc["id"] = str(doc["_id"])
    return doc


async def update_incident(
    incident_id: str,
    request: UpdateIncidentRequest,
    actor_id: str,
    actor_name: str,
    actor_role: str
) -> Optional[dict]:
    """Update status and add custom coordinator notes to timeline."""
    db = get_database()
    
    incident = await get_incident_by_id(incident_id)
    if not incident:
        return None

    update_fields = {}
    timeline_events = []
    
    if request.status is not None:
        update_fields["status"] = request.status.value
        timeline_events.append(TimelineEvent(
            event=f"Status updated to {request.status.value}",
            actor=actor_name,
            details=f"Status changed from {incident['status']} to {request.status.value}."
        ))

    if request.notes:
        timeline_events.append(TimelineEvent(
            event="Coordinator note added",
            actor=actor_name,
            details=request.notes
        ))

    if timeline_events:
        update_fields["updated_at"] = datetime.utcnow()
        await db.incidents.update_one(
            {"incident_id": incident["incident_id"]},
            {
                "$set": update_fields,
                "$push": {"timeline": {"$each": [e.model_dump() for e in timeline_events]}}
            }
        )
        
        # Log to audit trail
        await log_action(
            action="update",
            entity_type=AuditEntityType.INCIDENT,
            entity_id=incident["incident_id"],
            actor_id=actor_id,
            actor_role=actor_role,
            details={"updated_fields": list(update_fields.keys()), "notes_added": bool(request.notes)}
        )

        # Get updated document
        incident = await get_incident_by_id(incident["incident_id"])
        
    return incident


async def reprocess_incident_ai(incident_id: str, actor_id: str, actor_role: str) -> Optional[dict]:
    """Manually trigger AI re-analysis on raw report text (re-running classification & priority)."""
    db = get_database()
    
    incident = await get_incident_by_id(incident_id)
    if not incident:
        return None
        
    raw_text = incident["raw_report"]["text"]

    # 1. Re-run AI analysis
    ai_analysis = await analyze_incident_report(raw_text)

    # 2. Re-run Impact Estimation
    impact_estimate = await estimate_incident_impact(raw_text, ai_analysis)

    # 3. Re-run Priority calculation
    coords = incident["location"]["coordinates"]
    priority = await calculate_priority(
        analysis=ai_analysis,
        impact=impact_estimate,
        latitude=coords[1],
        longitude=coords[0]
    )

    # 4. Re-run RAG SOP recommended actions
    sops = retrieve_relevant_sops(raw_text, limit=3)
    recommended_actions = [
        f"[{sop['title']}] {sop['content'].split('.')[0]}."
        for sop in sops
    ]

    timeline_event = TimelineEvent(
        event="AI re-analysis executed",
        actor="system",
        details=f"Reprocessed by coordinator action. New score: {priority.score}/100."
    )
    
    await db.incidents.update_one(
        {"incident_id": incident["incident_id"]},
        {
            "$set": {
                "ai_analysis": ai_analysis.model_dump(),
                "impact_estimate": impact_estimate.model_dump(),
                "priority": priority.model_dump(),
                "response_plan": ResponsePlan(
                    recommended_actions=recommended_actions,
                    generated_at=datetime.utcnow()
                ).model_dump(),
                "updated_at": datetime.utcnow()
            },
            "$push": {"timeline": timeline_event.model_dump()}
        }
    )
    
    # 5. Save embedding
    await save_report_embedding(incident["incident_id"], raw_text)

    # 6. Recalculate ranks across all active incidents
    await recalculate_active_ranks()

    # Log to audit trail
    await log_action(
        action="reprocess_ai",
        entity_type=AuditEntityType.INCIDENT,
        entity_id=incident["incident_id"],
        actor_id=actor_id,
        actor_role=actor_role,
        details={"new_priority_score": priority.score}
    )
    
    return await get_incident_by_id(incident["incident_id"])


async def get_priority_queue(limit: int = 50, skip: int = 0) -> List[dict]:
    """Retrieve active incidents (not closed/resolved/duplicate) sorted by priority score descending."""
    db = get_database()
    cursor = db.incidents.find(
        {"status": {"$nin": [IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value, IncidentStatus.DUPLICATE.value]}}
    ).sort("priority.score", -1).skip(skip).limit(limit)
    
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["id"] = str(doc["_id"])
    return docs


async def get_priority_queue_count() -> int:
    """Retrieve count of active incidents in priority queue."""
    db = get_database()
    return await db.incidents.count_documents(
        {"status": {"$nin": [IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value, IncidentStatus.DUPLICATE.value]}}
    )


async def bulk_import_incidents(
    request: BulkImportRequest,
    actor_id: str,
    actor_role: str
) -> List[dict]:
    """Bulk import list of incidents, process each, and save to DB."""
    imported_docs = []
    
    # Process each report sequentially to ensure ID generation and AI scoring
    for inc_req in request.incidents:
        doc = await create_incident(
            request=inc_req,
            actor_id=actor_id,
            actor_role=actor_role
        )
        imported_docs.append(doc)
        
    return imported_docs


async def merge_duplicate_incidents(
    request: MergeIncidentsRequest,
    actor_id: str,
    actor_role: str,
    actor_name: str
) -> Optional[dict]:
    """Merge duplicate incidents into a primary incident."""
    db = get_database()
    
    primary = await get_incident_by_id(request.primary_incident_id)
    if not primary:
        return None
        
    duplicate_group_id = primary["duplicate_group_id"] or f"GRP-{primary['incident_id']}"
    
    # Ensure primary has the duplicate_group_id set
    await db.incidents.update_one(
        {"incident_id": primary["incident_id"]},
        {
            "$set": {
                "duplicate_group_id": duplicate_group_id,
                "updated_at": datetime.utcnow()
            },
            "$push": {
                "timeline": TimelineEvent(
                    event="Merged duplicates",
                    actor=actor_name,
                    details=f"Merged {len(request.duplicate_incident_ids)} duplicate reports into this primary incident."
                ).model_dump()
            }
        }
    )
    
    # Update all duplicate incidents
    for dup_id in request.duplicate_incident_ids:
        dup = await get_incident_by_id(dup_id)
        if not dup or dup["incident_id"] == primary["incident_id"]:
            continue
            
        await db.incidents.update_one(
            {"incident_id": dup["incident_id"]},
            {
                "$set": {
                    "status": IncidentStatus.DUPLICATE.value,
                    "duplicate_group_id": duplicate_group_id,
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "timeline": TimelineEvent(
                        event="Marked as duplicate",
                        actor=actor_name,
                        details=f"Marked as duplicate of primary incident {primary['incident_id']}."
                    ).model_dump()
                }
            }
        )
        
        # Log to audit trail for each duplicate merged
        await log_action(
            action="merge_duplicate",
            entity_type=AuditEntityType.INCIDENT,
            entity_id=dup["incident_id"],
            actor_id=actor_id,
            actor_role=actor_role,
            details={"primary_incident_id": primary["incident_id"]}
        )

    # Log to audit trail for the primary
    await log_action(
        action="merge_primary",
        entity_type=AuditEntityType.INCIDENT,
        entity_id=primary["incident_id"],
        actor_id=actor_id,
        actor_role=actor_role,
        details={"duplicate_incident_ids": request.duplicate_incident_ids}
    )

    return await get_incident_by_id(primary["incident_id"])
