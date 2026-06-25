"""
ResQNet AI - Impact Estimator Agent
Estimates medical, shelter, food/water, and rescue demands, along with infrastructure
damage score and estimated duration from report details.
"""

import logging
from typing import Optional

from app.ai.gemini_client import generate_structured_output
from app.models.incident import (
    ImpactEstimate, AIAnalysis, IncidentType, Severity, Urgency
)

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
You are the Chief Impact Assessment Officer at ResQNet AI.
Your task is to estimate the demand for resources and structural/duration impact based on an emergency report and its initial AI analysis.

Output a structured JSON response matching the following keys:
1. medical_demand: Estimated number of people needing immediate medical care.
2. shelter_demand: Estimated number of people needing temporary shelter.
3. food_water_demand: Estimated number of people needing emergency rations/drinking water.
4. rescue_demand: Estimated number of people needing active physical rescue.
5. infrastructure_damage_score: A float from 0.0 (none) to 10.0 (total destruction of bridges/roads/grid).
6. estimated_duration_hours: A float representing estimated response/recovery duration in hours.
7. economic_impact_estimate: Optional estimated cost of damage/response in USD (e.g. 50000.0), or null if unknown.
"""


def heuristic_impact_fallback(analysis: AIAnalysis) -> ImpactEstimate:
    """
    Mathematical fallback model for impact estimation if Gemini API fails.
    Calculates demands based on incident type, severity, and people affected.
    """
    people_affected = max(1, analysis.people_affected)
    vuln = analysis.vulnerable_populations
    
    # 1. Medical demand
    med_demand = 0
    if analysis.incident_type == IncidentType.MEDICAL:
        med_demand = max(1, people_affected)
    else:
        # Base on chronic illnesses and elderly/children
        med_demand = int(vuln.chronic_illness * 1.5 + vuln.elderly * 0.5 + vuln.disabled * 1.0)
        if analysis.severity in [Severity.CRITICAL, Severity.CATASTROPHIC]:
            med_demand = max(med_demand, int(people_affected * 0.2))

    # 2. Shelter demand
    shelter_demand = 0
    if analysis.incident_type in [
        IncidentType.FLOOD, IncidentType.EARTHQUAKE, IncidentType.EVACUATION,
        IncidentType.COLLAPSE, IncidentType.LANDSLIDE, IncidentType.CYCLONE
    ]:
        shelter_demand = people_affected
    elif analysis.severity in [Severity.HIGH, Severity.CRITICAL, Severity.CATASTROPHIC]:
        shelter_demand = int(people_affected * 0.5)

    # 3. Food and water demand
    food_water_demand = shelter_demand

    # 4. Rescue demand
    rescue_demand = 0
    if analysis.urgency in [Urgency.IMMEDIATE, Urgency.HIGH] or analysis.incident_type in [
        IncidentType.COLLAPSE, IncidentType.FLOOD, IncidentType.LANDSLIDE
    ]:
        if analysis.severity in [Severity.CRITICAL, Severity.CATASTROPHIC]:
            rescue_demand = people_affected
        else:
            rescue_demand = max(1, int(people_affected * 0.3))

    # 5. Infrastructure damage score
    infra_score = 0.0
    if analysis.incident_type in [IncidentType.EARTHQUAKE, IncidentType.COLLAPSE, IncidentType.LANDSLIDE, IncidentType.INFRASTRUCTURE]:
        infra_map = {
            Severity.LOW: 1.5,
            Severity.MODERATE: 4.0,
            Severity.HIGH: 6.5,
            Severity.CRITICAL: 8.5,
            Severity.CATASTROPHIC: 10.0
        }
        infra_score = infra_map.get(analysis.severity, 4.0)
    else:
        infra_map = {
            Severity.LOW: 0.5,
            Severity.MODERATE: 2.0,
            Severity.HIGH: 4.5,
            Severity.CRITICAL: 6.5,
            Severity.CATASTROPHIC: 8.0
        }
        infra_score = infra_map.get(analysis.severity, 2.0)

    # 6. Estimated duration in hours
    duration_map = {
        Severity.LOW: 6.0,
        Severity.MODERATE: 18.0,
        Severity.HIGH: 36.0,
        Severity.CRITICAL: 72.0,
        Severity.CATASTROPHIC: 120.0
    }
    duration = duration_map.get(analysis.severity, 24.0)
    if analysis.incident_type == IncidentType.EARTHQUAKE or analysis.incident_type == IncidentType.CYCLONE:
        duration *= 1.5

    # 7. Economic impact estimate
    economic_impact = float(people_affected * 1000.0)
    if infra_score >= 7.0:
        economic_impact += 50000.0

    return ImpactEstimate(
        medical_demand=med_demand,
        shelter_demand=shelter_demand,
        food_water_demand=food_water_demand,
        rescue_demand=rescue_demand,
        infrastructure_damage_score=round(infra_score, 1),
        estimated_duration_hours=round(duration, 1),
        economic_impact_estimate=economic_impact
    )


async def estimate_incident_impact(
    text: str,
    analysis: AIAnalysis
) -> ImpactEstimate:
    """
    Calls Gemini structured outputs to estimate impact, falling back
    to heuristic calculations if Gemini fails.
    """
    prompt = (
        f"Estimate the incident impact metrics for the following report:\n\n"
        f"Report Text: {text}\n"
        f"AI Analysis - Type: {analysis.incident_type}, Severity: {analysis.severity}, "
        f"Urgency: {analysis.urgency}, People Affected: {analysis.people_affected}, "
        f"Vulnerable Populations Total: {analysis.vulnerable_populations.total}"
    )

    result = await generate_structured_output(
        prompt=prompt,
        response_schema=ImpactEstimate,
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.1
    )

    if result is not None:
        return result

    # Fallback to local heuristic estimator
    logger.warning("Gemini impact estimation failed. Initiating heuristic fallback.")
    return heuristic_impact_fallback(analysis)
