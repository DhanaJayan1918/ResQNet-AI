"""
ResQNet AI - Priority Scoring Engine
Computes a multi-criteria priority score (0-100) for incidents by incorporating
AI analysis, vulnerable populations, and environmental constraints.
Provides rank-recalculation across all active incidents.
"""

import logging
import math
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.db.mongodb import get_database
from app.models.incident import Priority, PriorityFactors, AIAnalysis, ImpactEstimate
from app.models.incident import Severity, Urgency

logger = logging.getLogger(__name__)


async def calculate_priority(
    analysis: AIAnalysis,
    impact: Optional[ImpactEstimate] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Priority:
    """
    Compute a priority score from 0.0 to 100.0.
    Weights:
      - Severity: max 30.0 points
      - Urgency: max 30.0 points
      - People Affected: max 15.0 points
      - Vulnerabilities: max 15.0 points
      - Environmental Load (Hospital/Shelter/Resource scarcity): max 10.0 points
    """
    db = get_database()

    # 1. Severity Score (max 30)
    severity_map = {
        Severity.LOW: 5.0,
        Severity.MODERATE: 12.0,
        Severity.HIGH: 20.0,
        Severity.CRITICAL: 26.0,
        Severity.CATASTROPHIC: 30.0,
    }
    sev_points = severity_map.get(analysis.severity, 12.0)

    # 2. Urgency Score (max 30)
    urgency_map = {
        Urgency.LOW: 5.0,
        Urgency.MEDIUM: 12.0,
        Urgency.HIGH: 22.0,
        Urgency.IMMEDIATE: 30.0,
    }
    urg_points = urgency_map.get(analysis.urgency, 12.0)

    # 3. People Affected Score (max 15)
    # Logarithmic scaling: log10(affected + 1) * 4.5, capped at 15.0
    affected_count = max(0, analysis.people_affected)
    affected_points = min(15.0, math.log10(affected_count + 1) * 4.5)

    # 4. Vulnerability Score (max 15)
    # 1.5 points per vulnerable person (children, elderly, disabled, pregnant, chronic), capped at 15.0
    vuln_count = analysis.vulnerable_populations.total
    vuln_points = min(15.0, vuln_count * 1.5)

    # 5. Dynamic Environmental Constraints (max 10)
    hospital_load = 0.0
    shelter_load = 0.0
    resource_scarcity = 0.0
    accessibility_score = 0.0 # Standard terrain accessibility, default 0

    try:
        # Check Hospital Load (max 3.5 points)
        # Query if any hospitals are overwhelmed
        hospital_cursor = db.hospitals.find({"status": "overwhelmed"})
        overwhelmed_hospitals = await hospital_cursor.to_list(length=5)
        if overwhelmed_hospitals:
            hospital_load = 3.5
        else:
            # Query if average available beds is low
            all_hospitals = await db.hospitals.find({}).to_list(length=10)
            if all_hospitals:
                total_beds = sum(h.get("total_beds", 0) for h in all_hospitals)
                avail_beds = sum(h.get("available_beds", 0) for h in all_hospitals)
                if total_beds > 0 and (avail_beds / total_beds) < 0.15:
                    hospital_load = 2.0

        # Check Shelter Load (max 3.5 points)
        # Query if shelters are close to full capacity (> 85%)
        shelter_cursor = db.shelters.find({"occupancy_percentage": {"$gte": 85.0}})
        full_shelters = await shelter_cursor.to_list(length=5)
        if full_shelters:
            shelter_load = 3.5

        # Check Resource Scarcity (max 3.0 points)
        # If the incident requires critical resources, check their availability status
        if analysis.resource_requirements:
            required_types = [r.resource_type for r in analysis.resource_requirements]
            # Count how many available resources of these types exist
            avail_resources = await db.resources.count_documents({
                "type": {"$in": required_types},
                "status": "available"
            })
            if avail_resources == 0:
                resource_scarcity = 3.0
            elif avail_resources < len(analysis.resource_requirements):
                resource_scarcity = 1.5

    except Exception as e:
        logger.warning(f"Error querying environment metrics for priority scoring: {e}")

    # Compile scores
    env_points = min(10.0, hospital_load + shelter_load + resource_scarcity)
    
    total_score = round(sev_points + urg_points + affected_points + vuln_points + env_points, 1)
    total_score = max(0.0, min(100.0, total_score))

    factors = PriorityFactors(
        severity_score=round(sev_points, 1),
        urgency_score=round(urg_points, 1),
        people_affected_score=round(affected_points, 1),
        vulnerability_score=round(vuln_points, 1),
        resource_scarcity_score=round(resource_scarcity, 1),
        accessibility_score=round(accessibility_score, 1),
        shelter_load_score=round(shelter_load, 1),
        hospital_load_score=round(hospital_load, 1)
    )

    explanation = (
        f"Base priorities: Severity={analysis.severity} ({factors.severity_score}), "
        f"Urgency={analysis.urgency} ({factors.urgency_score}), Affected={analysis.people_affected} ({factors.people_affected_score}). "
        f"Context loads: Hospital={factors.hospital_load_score}, Shelter={factors.shelter_load_score}, Scarcity={factors.resource_scarcity_score}."
    )

    return Priority(
        score=total_score,
        rank=0,
        factors=factors,
        explanation=explanation,
        calculated_at=datetime.utcnow()
    )


async def recalculate_active_ranks() -> None:
    """
    Query all active incidents, sort them by priority score descending,
    and update their rank fields in MongoDB.
    """
    db = get_database()
    
    # Fetch active reports (not resolved, closed, or duplicate) sorted by score descending
    query = {"status": {"$nin": ["resolved", "closed", "duplicate"]}}
    cursor = db.incidents.find(query).sort("priority.score", -1)
    active_incidents = await cursor.to_list(length=1000)

    logger.info(f"Recalculating priority ranks for {len(active_incidents)} active incidents.")

    for index, doc in enumerate(active_incidents):
        rank = index + 1
        await db.incidents.update_one(
            {"_id": doc["_id"]},
            {"$set": {"priority.rank": rank}}
        )
