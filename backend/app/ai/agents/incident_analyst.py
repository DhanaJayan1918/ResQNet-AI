"""
ResQNet AI - Incident Analyst Agent
Classifies incident type, severity, urgency, estimated affected people,
vulnerable populations, and resource requirements from raw emergency texts.
"""

import logging
from datetime import datetime
import re
from typing import Optional

from app.ai.gemini_client import generate_structured_output
from app.models.incident import (
    AIAnalysis, IncidentType, Severity, Urgency,
    VulnerablePopulations, ResourceRequirement, ResourceUrgency
)

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
You are the Lead Emergency Dispatch Analyst at ResQNet AI Command Center.
Your role is to analyze incoming crisis reports (citizen posts, SMS, first responder briefs) and structure them with high precision.

You must categorize the report text into:
1. incident_type: Choose from: flood, earthquake, wildfire, medical, infrastructure, shelter_overload, power_outage, evacuation, chemical, collapse, landslide, cyclone, other.
2. severity: low, moderate, high, critical, catastrophic.
3. urgency: low, medium, high, immediate.
4. people_affected: total estimated people directly impacted or endangered.
5. vulnerable_populations: break down count of children, elderly, disabled, pregnant, or chronic illnesses.
6. resource_requirements: list required resource types (e.g. ambulance, rescue_boat, medical_team, fire_unit, volunteer_team) with quantity and urgency.
7. confidence_score: your confidence (0.0 to 1.0) based on clarity of the report.
8. reasoning: a concise explanation (1-2 sentences) of why you made these decisions.
"""

def heuristic_analyst_fallback(text: str) -> AIAnalysis:
    """
    Enhanced rule-based fallback analyzer if Gemini API key fails or hits quota limits.
    Parses key incident info using regex and text patterns.
    """
    text_lower = text.lower()
    
    # 1. Classify incident type
    incident_type = IncidentType.OTHER
    if any(k in text_lower for k in ["flood", "water rising", "submerged", "inundat", "drown"]):
        incident_type = IncidentType.FLOOD
    elif any(k in text_lower for k in ["earthquake", "tremor", "quake", "seismic"]):
        incident_type = IncidentType.EARTHQUAKE
    elif any(k in text_lower for k in ["fire", "wildfire", "smoke", "burning", "blaze"]):
        incident_type = IncidentType.WILDFIRE
    elif any(k in text_lower for k in ["medical", "injury", "bleeding", "heart attack", "stroke", "illness"]):
        incident_type = IncidentType.MEDICAL
    elif any(k in text_lower for k in ["collapse", "rubble", "crushed", "fell down", "caved in"]):
        incident_type = IncidentType.COLLAPSE
    elif any(k in text_lower for k in ["landslide", "mudslide", "rockslide"]):
        incident_type = IncidentType.LANDSLIDE
    elif any(k in text_lower for k in ["cyclone", "hurricane", "storm", "typhoon"]):
        incident_type = IncidentType.CYCLONE
    elif any(k in text_lower for k in ["power", "blackout", "electricity", "outage", "grid"]):
        incident_type = IncidentType.POWER_OUTAGE
    elif any(k in text_lower for k in ["evacuat", "leave home", "fleeing"]):
        incident_type = IncidentType.EVACUATION
    elif any(k in text_lower for k in ["chemical", "gas leak", "toxic", "poison"]):
        incident_type = IncidentType.CHEMICAL
    elif any(k in text_lower for k in ["shelter", "overcrowd", "refugees"]):
        incident_type = IncidentType.SHELTER_OVERLOAD
    elif any(k in text_lower for k in ["road block", "bridge down", "infrastructure"]):
        incident_type = IncidentType.INFRASTRUCTURE

    # 2. Extract severity and urgency
    severity = Severity.MODERATE
    urgency = Urgency.MEDIUM
    
    if any(k in text_lower for k in ["catastrophic", "devastating", "apocalypse", "total destruction"]):
        severity = Severity.CATASTROPHIC
        urgency = Urgency.IMMEDIATE
    elif any(k in text_lower for k in ["critical", "dying", "trapped", "danger", "suffocat"]):
        severity = Severity.CRITICAL
        urgency = Urgency.IMMEDIATE
    elif any(k in text_lower for k in ["severe", "injured", "heavy", "serious", "urgent"]):
        severity = Severity.HIGH
        urgency = Urgency.HIGH
    elif any(k in text_lower for k in ["mild", "minor", "small", "low", "no injuries"]):
        severity = Severity.LOW
        urgency = Urgency.LOW

    # 3. Estimate people affected via regex
    people_affected = 1
    numbers = re.findall(r'\b\d+\b', text_lower)
    if numbers:
        valid_nums = [int(n) for n in numbers if 1 <= int(n) <= 10000]
        if valid_nums:
            people_affected = max(valid_nums)
    else:
        # Check lexical numbers
        if "dozen" in text_lower:
            people_affected = 12
        elif "hundred" in text_lower:
            people_affected = 100
        elif "thousand" in text_lower:
            people_affected = 1000

    # 4. Extract vulnerable populations
    children = 0
    elderly = 0
    disabled = 0
    pregnant = 0
    chronic_illness = 0

    if any(k in text_lower for k in ["child", "kid", "baby", "infant", "school"]):
        children = max(1, int(people_affected * 0.15))
    if any(k in text_lower for k in ["elderly", "old", "senior", "grand", "aged"]):
        elderly = max(1, int(people_affected * 0.10))
    if any(k in text_lower for k in ["disabled", "wheelchair", "blind", "handicap"]):
        disabled = max(1, int(people_affected * 0.02))
    if "pregnant" in text_lower:
        pregnant = max(1, int(people_affected * 0.01))
    if any(k in text_lower for k in ["chronic", "diabet", "asthma", "heart patient", "medicat"]):
        chronic_illness = max(1, int(people_affected * 0.05))

    vulnerable = VulnerablePopulations(
        children=children,
        elderly=elderly,
        disabled=disabled,
        pregnant=pregnant,
        chronic_illness=chronic_illness
    )

    # 5. Resource requirements
    resources = []
    if incident_type == IncidentType.FLOOD:
        resources.append(ResourceRequirement(resource_type="rescue_boat", quantity=max(1, int(people_affected/10)), urgency=ResourceUrgency.IMMEDIATE))
        resources.append(ResourceRequirement(resource_type="food_supply", quantity=people_affected, urgency=ResourceUrgency.HIGH))
    elif incident_type == IncidentType.COLLAPSE:
        resources.append(ResourceRequirement(resource_type="fire_unit", quantity=1, urgency=ResourceUrgency.IMMEDIATE))
        resources.append(ResourceRequirement(resource_type="medical_team", quantity=1, urgency=ResourceUrgency.IMMEDIATE))
    elif incident_type == IncidentType.MEDICAL or vulnerable.total > 0:
        resources.append(ResourceRequirement(resource_type="medical_team", quantity=1, urgency=ResourceUrgency.IMMEDIATE))
        resources.append(ResourceRequirement(resource_type="ambulance", quantity=max(1, int(people_affected/5)), urgency=ResourceUrgency.IMMEDIATE))
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
        confidence_score=0.70,
        reasoning="Rule-based heuristic fallback (Gemini API unavailable or rate-limited).",
        processed_at=datetime.utcnow()
    )


async def analyze_incident_report(text: str) -> AIAnalysis:
    """
    Analyzes an incident report by calling Gemini with a structured schema,
    falling back to local heuristic extraction if API fails.
    """
    if not text or len(text.strip()) < 5:
        return heuristic_analyst_fallback(text or "")

    prompt = f"Analyze the following emergency report text and structure it precisely:\n\nReport Text: {text}"
    
    # Try calling Gemini
    result = await generate_structured_output(
        prompt=prompt,
        response_schema=AIAnalysis,
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.1
    )

    if result is not None:
        result.processed_at = datetime.utcnow()
        return result

    # Fallback if API fails
    logger.warning("Gemini structured output failed. Initiating heuristic fallback.")
    return heuristic_analyst_fallback(text)
