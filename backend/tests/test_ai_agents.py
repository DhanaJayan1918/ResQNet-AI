"""
ResQNet AI - AI Processing Pipeline Unit Tests
Verifies the Incident Analyst, Duplicate Detector, Impact Estimator,
Priority Engine, and RAG Engine under successful and fallback scenarios.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.models.incident import (
    AIAnalysis, IncidentType, Severity, Urgency,
    VulnerablePopulations, ResourceRequirement, ResourceUrgency,
    ImpactEstimate, Priority
)
from app.ai.agents.incident_analyst import (
    analyze_incident_report, heuristic_analyst_fallback
)
from app.ai.agents.duplicate_detector import (
    find_duplicate_incident, calculate_tfidf_similarity
)
from app.ai.agents.impact_estimator import (
    estimate_incident_impact, heuristic_impact_fallback
)
from app.ai.priority_engine import calculate_priority, recalculate_active_ranks
from app.ai.rag_engine import retrieve_relevant_sops, load_sop_files, initialize_sop_db
from app.db.mongodb import get_database


# ==============================================================================
# 1. Incident Analyst Agent Tests
# ==============================================================================

def test_heuristic_analyst_fallback():
    """Verify regex and rule-based fallback classifications for different report texts."""
    # Test Flood
    res_flood = heuristic_analyst_fallback("There is a severe flood here, water is rising fast and people are trapped on roofs.")
    assert res_flood.incident_type == IncidentType.FLOOD
    assert res_flood.severity == Severity.CRITICAL
    assert res_flood.urgency == Urgency.IMMEDIATE
    assert any(r.resource_type == "rescue_boat" for r in res_flood.resource_requirements)

    # Test Collapse with numbers
    res_collapse = heuristic_analyst_fallback("Building collapse at 12 Main St! 25 construction workers are trapped under rubble!")
    assert res_collapse.incident_type == IncidentType.COLLAPSE
    assert res_collapse.people_affected == 25
    assert res_collapse.vulnerable_populations.children > 0 or res_collapse.vulnerable_populations.total >= 0

    # Test Medical
    res_med = heuristic_analyst_fallback("An elderly lady is having a severe heart attack and is bleeding.")
    assert res_med.incident_type == IncidentType.MEDICAL
    assert res_med.vulnerable_populations.elderly >= 1


@pytest.mark.asyncio
@patch("app.ai.agents.incident_analyst.generate_structured_output")
async def test_analyze_incident_report_success(mock_gen):
    """Test successful analyst structured output parsing (mocking Gemini API response)."""
    mock_analysis = AIAnalysis(
        incident_type=IncidentType.WILDFIRE,
        severity=Severity.HIGH,
        urgency=Urgency.HIGH,
        people_affected=150,
        vulnerable_populations=VulnerablePopulations(children=12, elderly=8),
        resource_requirements=[ResourceRequirement(resource_type="fire_unit", quantity=3, urgency=ResourceUrgency.HIGH)],
        confidence_score=0.95,
        reasoning="Severe forest fire encroaching residential zone.",
        processed_at=datetime.utcnow()
    )
    mock_gen.return_value = mock_analysis

    res = await analyze_incident_report("Wildfire spreading rapidly near homes, evacuations in progress.")
    assert res.incident_type == IncidentType.WILDFIRE
    assert res.people_affected == 150
    assert res.confidence_score == 0.95
    assert mock_gen.called


@pytest.mark.asyncio
@patch("app.ai.agents.incident_analyst.generate_structured_output")
async def test_analyze_incident_report_api_failure(mock_gen):
    """Test graceful fallback to heuristics when Gemini API fails."""
    mock_gen.return_value = None  # Simulate API error/timeout
    
    res = await analyze_incident_report("Severe flooding and water logging in low lying area.")
    assert res.incident_type == IncidentType.FLOOD
    assert "heuristic fallback" in res.reasoning.lower()


# ==============================================================================
# 2. Duplicate Detector Agent Tests
# ==============================================================================

def test_calculate_tfidf_similarity():
    """Verify TF-IDF cosine similarity calculations."""
    text1 = "Severe flooding in Velachery area, road is submerged"
    text2 = "Velachery area has severe flooding and the road is submerged"
    text3 = "Fire in a chemical warehouse causing gas leak"
    
    sim1 = calculate_tfidf_similarity(text1, text2)
    sim2 = calculate_tfidf_similarity(text1, text3)
    
    assert sim1 > sim2
    assert sim1 > 0.5


@pytest.mark.asyncio
async def test_find_duplicate_incident_no_match(init_databases):
    """Test that unique report coordinates do not trigger duplicate detection."""
    db = get_database()
    
    # Insert a report in Velachery (Chennai)
    await db.incidents.insert_one({
        "incident_id": "RESQ-20260625-1001",
        "status": "new",
        "raw_report": {"text": "Flooding on Velachery Main Road"},
        "location": {"type": "Point", "coordinates": [80.2244, 12.9789]}, # Velachery
        "created_at": datetime.utcnow()
    })
    
    # Try searching for duplicate at a distant coordinate (e.g. Tambaram, 15km away)
    dup = await find_duplicate_incident(
        text="Flooding on Tambaram Road",
        latitude=12.9229,  # Tambaram
        longitude=80.1275,
        max_distance_km=1.0
    )
    assert dup is None


@pytest.mark.asyncio
async def test_find_duplicate_incident_match(init_databases):
    """Test spatiotemporal match triggers duplicate flag linking report to primary."""
    db = get_database()
    
    # Insert primary report
    await db.incidents.insert_one({
        "incident_id": "RESQ-20260625-1002",
        "status": "new",
        "raw_report": {"text": "Huge tree collapsed on building, people are trapped."},
        "location": {"type": "Point", "coordinates": [80.2001, 13.0001]},
        "created_at": datetime.utcnow()
    })
    
    # Search for duplicate at very close coordinates and similar text
    dup = await find_duplicate_incident(
        text="A huge tree collapsed on a building, and people are trapped.",
        latitude=13.0002,
        longitude=80.2002,
        max_distance_km=1.0,
        similarity_threshold=0.45
    )
    assert dup == "RESQ-20260625-1002"


# ==============================================================================
# 3. Impact Estimator Agent Tests
# ==============================================================================

def test_heuristic_impact_fallback():
    """Verify impact metrics calculations for vulnerable counts and durations."""
    analysis = AIAnalysis(
        incident_type=IncidentType.FLOOD,
        severity=Severity.HIGH,
        urgency=Urgency.HIGH,
        people_affected=100,
        vulnerable_populations=VulnerablePopulations(children=15, elderly=10, chronic_illness=5),
        confidence_score=0.85
    )
    
    impact = heuristic_impact_fallback(analysis)
    assert impact.shelter_demand == 100
    assert impact.food_water_demand == 100
    assert impact.medical_demand >= 5
    assert impact.infrastructure_damage_score > 0.0
    assert impact.estimated_duration_hours >= 36.0


# ==============================================================================
# 4. Priority Scoring Engine Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_calculate_priority_score_ranges(init_databases):
    """Verify priority score caps, weights, and environmental load factors."""
    analysis = AIAnalysis(
        incident_type=IncidentType.COLLAPSE,
        severity=Severity.CATASTROPHIC,
        urgency=Urgency.IMMEDIATE,
        people_affected=500,
        vulnerable_populations=VulnerablePopulations(children=50, elderly=30),
        confidence_score=0.90
    )
    
    priority = await calculate_priority(analysis)
    # Catastrophic severity + immediate urgency + large population should yield a very high score
    assert priority.score >= 80.0
    assert priority.factors.severity_score == 30.0
    assert priority.factors.urgency_score == 30.0


@pytest.mark.asyncio
async def test_recalculate_ranks(init_databases):
    """Verify active incidents are sorted and sequentially ranked 1, 2, 3..."""
    db = get_database()
    
    # Insert three active incidents with different priority scores
    await db.incidents.insert_many([
        {
            "incident_id": "INC-01",
            "status": "new",
            "priority": {"score": 45.0, "rank": 0},
            "created_at": datetime.utcnow()
        },
        {
            "incident_id": "INC-02",
            "status": "assigned",
            "priority": {"score": 90.0, "rank": 0},
            "created_at": datetime.utcnow()
        },
        {
            "incident_id": "INC-03",
            "status": "new",
            "priority": {"score": 75.0, "rank": 0},
            "created_at": datetime.utcnow()
        }
    ])
    
    await recalculate_active_ranks()
    
    inc2 = await db.incidents.find_one({"incident_id": "INC-02"})
    inc3 = await db.incidents.find_one({"incident_id": "INC-03"})
    inc1 = await db.incidents.find_one({"incident_id": "INC-01"})
    
    assert inc2["priority"]["rank"] == 1
    assert inc3["priority"]["rank"] == 2
    assert inc1["priority"]["rank"] == 3


# ==============================================================================
# 5. RAG Engine Tests
# ==============================================================================

def test_rag_sop_loading():
    """Verify RAG chunks are correctly parsed and loaded from markdown files."""
    chunks = load_sop_files()
    assert len(chunks) > 0
    assert any(c["category"] == "flood" for c in chunks)


def test_retrieve_relevant_sops_fallback():
    """Verify TF-IDF keyphrase retrieval returns correct top relevant SOP."""
    # Ensure default SOP files are initialized
    initialize_sop_db()
    
    res = retrieve_relevant_sops("How to deploy rescue boats and rescue people from floods", limit=2)
    assert len(res) > 0
    assert "flood" in res[0]["category"]
    assert res[0]["score"] > 0.0
