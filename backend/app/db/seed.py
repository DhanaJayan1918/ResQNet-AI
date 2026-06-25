"""
ResQNet AI - Database Seeding Script
Populates the database with realistic sample data for development and testing.
Includes sample users, resources, shelters, hospitals, and incidents.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.mongodb import connect_mongodb, get_database, close_mongodb
from app.db.redis_client import connect_redis, close_redis
from app.services.auth_service import hash_password
from app.utils.id_generator import (
    generate_incident_id, generate_resource_id,
    generate_shelter_id, generate_hospital_id,
)


# ---- Sample Data ----

SAMPLE_USERS = [
    {
        "email": "admin@resqnet.ai",
        "password_hash": hash_password("Admin@2024"),
        "full_name": "System Administrator",
        "role": "super_admin",
        "phone": "+91-9000000001",
        "organization": "ResQNet AI",
        "is_active": True,
        "permissions": ["all"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "email": "coordinator@resqnet.ai",
        "password_hash": hash_password("Coord@2024"),
        "full_name": "Priya Sharma",
        "role": "coordinator",
        "phone": "+91-9000000002",
        "organization": "National Disaster Management Authority",
        "is_active": True,
        "permissions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "email": "fieldofficer@resqnet.ai",
        "password_hash": hash_password("Field@2024"),
        "full_name": "Rajesh Kumar",
        "role": "field_officer",
        "phone": "+91-9000000003",
        "organization": "State Emergency Response Force",
        "is_active": True,
        "permissions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "email": "hospital@resqnet.ai",
        "password_hash": hash_password("Hospital@2024"),
        "full_name": "Dr. Aisha Khan",
        "role": "hospital",
        "phone": "+91-9000000004",
        "organization": "City General Hospital",
        "is_active": True,
        "permissions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "email": "shelter@resqnet.ai",
        "password_hash": hash_password("Shelter@2024"),
        "full_name": "Vikram Singh",
        "role": "shelter_manager",
        "phone": "+91-9000000005",
        "organization": "Red Cross India",
        "is_active": True,
        "permissions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "email": "volunteer@resqnet.ai",
        "password_hash": hash_password("Volunteer@2024"),
        "full_name": "Meera Patel",
        "role": "volunteer",
        "phone": "+91-9000000006",
        "organization": "Humanitarian Aid Network",
        "is_active": True,
        "permissions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "email": "citizen@resqnet.ai",
        "password_hash": hash_password("Citizen@2024"),
        "full_name": "Arjun Nair",
        "role": "citizen",
        "phone": "+91-9000000007",
        "organization": None,
        "is_active": True,
        "permissions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
]

# Chennai area coordinates for realistic Indian context
CHENNAI_CENTER = (13.0827, 80.2707)

def random_coords(center=CHENNAI_CENTER, radius_km=30):
    """Generate random coordinates near a center point."""
    lat = center[0] + random.uniform(-radius_km/111, radius_km/111)
    lon = center[1] + random.uniform(-radius_km/111, radius_km/111)
    return [round(lon, 6), round(lat, 6)]  # GeoJSON: [lng, lat]


SAMPLE_RESOURCES = []
resource_configs = [
    ("ambulance", "Ambulance Unit", 4, "people", "City Emergency Services"),
    ("ambulance", "Advanced Life Support", 2, "people", "City Emergency Services"),
    ("rescue_boat", "Flood Rescue Boat", 8, "people", "Navy Rescue Division"),
    ("rescue_boat", "Inflatable Rescue Raft", 6, "people", "State Disaster Response"),
    ("medical_team", "Trauma Response Team", 10, "people", "AIIMS Medical Corps"),
    ("medical_team", "Field Medical Unit", 8, "people", "Red Cross Medical"),
    ("volunteer_team", "Search & Rescue Team Alpha", 15, "people", "Civil Defense"),
    ("volunteer_team", "Community Response Team", 20, "people", "Humanitarian Aid Network"),
    ("food_supply", "Mobile Kitchen Unit", 500, "people", "Army Canteen Services"),
    ("water_supply", "Water Tanker", 10000, "liters", "Municipal Water Board"),
    ("medical_kit", "Emergency Medical Supply", 100, "units", "Health Department"),
    ("generator", "Portable Generator 50KVA", 1, "units", "Power Corporation"),
    ("generator", "Mobile Power Station", 1, "units", "Power Corporation"),
    ("police_unit", "Emergency Police Patrol", 6, "people", "City Police"),
    ("fire_unit", "Fire Engine Alpha", 6, "people", "Fire & Rescue Services"),
    ("fire_unit", "Fire Engine Bravo", 6, "people", "Fire & Rescue Services"),
    ("helicopter", "Air Ambulance", 4, "people", "Air Force Medical"),
    ("drone", "Surveillance Drone", 1, "units", "Disaster Recon Unit"),
]

for rtype, name, cap, unit, org in resource_configs:
    coords = random_coords()
    SAMPLE_RESOURCES.append({
        "resource_id": generate_resource_id(rtype),
        "type": rtype,
        "name": name,
        "status": random.choice(["available", "available", "available", "assigned"]),
        "location": {"type": "Point", "coordinates": coords, "last_updated": datetime.utcnow()},
        "capacity": {"total": cap, "current_load": 0, "unit": unit},
        "capabilities": [],
        "assigned_incident_id": None,
        "base_location": {"type": "Point", "coordinates": coords, "last_updated": datetime.utcnow()},
        "organization": org,
        "contact": f"+91-90000{random.randint(10000, 99999)}",
        "deployment_history": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })


SAMPLE_SHELTERS = [
    {
        "shelter_id": generate_shelter_id(),
        "name": "Government School Relief Camp",
        "location": {"type": "Point", "coordinates": random_coords()},
        "address": "Anna Nagar, Chennai",
        "total_capacity": 500,
        "current_occupancy": 342,
        "status": "open",
        "facilities": ["medical", "food", "water", "sanitation"],
        "contact_person": "Vikram Singh",
        "contact_phone": "+91-9000000005",
        "manager_id": None,
        "supplies": {
            "food_days_remaining": 4.5,
            "water_days_remaining": 3.0,
            "medical_kits": 25,
            "blankets": 400,
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "shelter_id": generate_shelter_id(),
        "name": "Community Hall Shelter",
        "location": {"type": "Point", "coordinates": random_coords()},
        "address": "T. Nagar, Chennai",
        "total_capacity": 300,
        "current_occupancy": 278,
        "status": "open",
        "facilities": ["food", "water", "power"],
        "contact_person": "Anitha Rajan",
        "contact_phone": "+91-9000000020",
        "manager_id": None,
        "supplies": {
            "food_days_remaining": 2.0,
            "water_days_remaining": 1.5,
            "medical_kits": 10,
            "blankets": 250,
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "shelter_id": generate_shelter_id(),
        "name": "Indoor Stadium Emergency Shelter",
        "location": {"type": "Point", "coordinates": random_coords()},
        "address": "Egmore, Chennai",
        "total_capacity": 800,
        "current_occupancy": 156,
        "status": "open",
        "facilities": ["medical", "food", "water", "power", "sanitation"],
        "contact_person": "Karthik Venkat",
        "contact_phone": "+91-9000000021",
        "manager_id": None,
        "supplies": {
            "food_days_remaining": 7.0,
            "water_days_remaining": 5.0,
            "medical_kits": 50,
            "blankets": 700,
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "shelter_id": generate_shelter_id(),
        "name": "Temple Complex Relief Center",
        "location": {"type": "Point", "coordinates": random_coords()},
        "address": "Mylapore, Chennai",
        "total_capacity": 200,
        "current_occupancy": 198,
        "status": "full",
        "facilities": ["food", "water"],
        "contact_person": "Lakshmi Devi",
        "contact_phone": "+91-9000000022",
        "manager_id": None,
        "supplies": {
            "food_days_remaining": 1.0,
            "water_days_remaining": 0.5,
            "medical_kits": 5,
            "blankets": 150,
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
]


SAMPLE_HOSPITALS = [
    {
        "hospital_id": generate_hospital_id(),
        "name": "Chennai General Hospital",
        "location": {"type": "Point", "coordinates": random_coords()},
        "address": "Park Town, Chennai",
        "total_beds": 500,
        "available_beds": 45,
        "icu_beds_total": 50,
        "icu_beds_available": 3,
        "er_capacity": 30,
        "er_current_load": 27,
        "specialties": ["trauma", "cardiology", "neurology", "orthopedics", "burns"],
        "blood_bank_status": {"A+": 20, "A-": 5, "B+": 15, "B-": 3, "O+": 25, "O-": 8, "AB+": 10, "AB-": 2},
        "ambulances_available": 3,
        "status": "operational",
        "contact": "+91-44-25305000",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "hospital_id": generate_hospital_id(),
        "name": "Apollo Hospital, Greams Road",
        "location": {"type": "Point", "coordinates": random_coords()},
        "address": "Greams Road, Chennai",
        "total_beds": 700,
        "available_beds": 120,
        "icu_beds_total": 80,
        "icu_beds_available": 15,
        "er_capacity": 40,
        "er_current_load": 22,
        "specialties": ["trauma", "cardiology", "neurology", "pediatrics", "transplant"],
        "blood_bank_status": {"A+": 30, "A-": 8, "B+": 25, "B-": 6, "O+": 35, "O-": 12, "AB+": 15, "AB-": 4},
        "ambulances_available": 8,
        "status": "operational",
        "contact": "+91-44-28293333",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "hospital_id": generate_hospital_id(),
        "name": "Rajiv Gandhi Government Hospital",
        "location": {"type": "Point", "coordinates": random_coords()},
        "address": "Triplicane, Chennai",
        "total_beds": 800,
        "available_beds": 15,
        "icu_beds_total": 60,
        "icu_beds_available": 1,
        "er_capacity": 35,
        "er_current_load": 34,
        "specialties": ["trauma", "general_surgery", "orthopedics", "burns"],
        "blood_bank_status": {"A+": 10, "A-": 2, "B+": 8, "B-": 1, "O+": 12, "O-": 3, "AB+": 5, "AB-": 1},
        "ambulances_available": 1,
        "status": "overwhelmed",
        "contact": "+91-44-25305555",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
]


SAMPLE_INCIDENTS = [
    {
        "incident_id": generate_incident_id(),
        "status": "verified",
        "source": {
            "type": "citizen",
            "reporter_name": "Arjun Nair",
            "reporter_contact": "+91-9000000007",
            "submission_channel": "web",
        },
        "raw_report": {
            "text": "Severe flooding in Velachery area. Water level has risen to 4 feet. Approximately 200 families trapped in residential apartments. Children and elderly unable to evacuate. Need immediate rescue boats and medical assistance. Several people with chronic illnesses running out of medication.",
            "images": [],
            "metadata": {},
        },
        "location": {
            "type": "Point",
            "coordinates": [80.2211, 12.9816],
            "address": "Velachery Main Road, Chennai",
            "landmark": "Near Velachery MRTS Station",
            "region": "South Chennai",
        },
        "ai_analysis": {
            "incident_type": "flood",
            "severity": "critical",
            "urgency": "immediate",
            "people_affected": 800,
            "vulnerable_populations": {"children": 150, "elderly": 100, "disabled": 20, "pregnant": 10, "chronic_illness": 45},
            "resource_requirements": [
                {"resource_type": "rescue_boat", "quantity": 5, "urgency": "immediate"},
                {"resource_type": "medical_team", "quantity": 2, "urgency": "immediate"},
                {"resource_type": "ambulance", "quantity": 3, "urgency": "high"},
                {"resource_type": "food_supply", "quantity": 1, "urgency": "high"},
                {"resource_type": "water_supply", "quantity": 1, "urgency": "high"},
            ],
            "confidence_score": 0.92,
            "reasoning": "Report describes severe flooding with significant trapped population including vulnerable groups. Chronic illness patients needing medication indicates medical urgency. High population density area confirms large affected count.",
            "processed_at": datetime.utcnow(),
        },
        "impact_estimate": {
            "medical_demand": 65,
            "shelter_demand": 800,
            "food_water_demand": 800,
            "rescue_demand": 200,
            "infrastructure_damage_score": 7.5,
            "estimated_duration_hours": 72,
        },
        "priority": {
            "score": 94.5,
            "rank": 1,
            "factors": {
                "severity_score": 20.0,
                "urgency_score": 20.0,
                "people_affected_score": 18.0,
                "vulnerability_score": 16.5,
                "resource_scarcity_score": 8.0,
                "accessibility_score": 6.0,
                "shelter_load_score": 4.0,
                "hospital_load_score": 2.0,
            },
            "explanation": "CRITICAL: Large-scale flooding with 800+ people affected including 325 vulnerable individuals. Immediate rescue and medical intervention required. Hospital capacity in area critically low.",
            "calculated_at": datetime.utcnow(),
        },
        "assigned_resources": [],
        "response_plan": {"recommended_actions": [], "resource_assignments": [], "expected_impact": "", "alternatives": [], "explanation": ""},
        "timeline": [
            {"event": "Report submitted", "timestamp": datetime.utcnow() - timedelta(hours=2), "actor": "citizen", "details": "Submitted via web portal"},
            {"event": "AI analysis completed", "timestamp": datetime.utcnow() - timedelta(hours=1, minutes=55), "actor": "system"},
            {"event": "Priority score calculated", "timestamp": datetime.utcnow() - timedelta(hours=1, minutes=50), "actor": "system", "details": "Score: 94.5/100"},
            {"event": "Status changed to verified", "timestamp": datetime.utcnow() - timedelta(hours=1, minutes=30), "actor": "coordinator"},
        ],
        "created_at": datetime.utcnow() - timedelta(hours=2),
        "updated_at": datetime.utcnow() - timedelta(hours=1, minutes=30),
    },
    {
        "incident_id": generate_incident_id(),
        "status": "verified",
        "source": {
            "type": "hospital",
            "reporter_name": "Dr. Aisha Khan",
            "reporter_contact": "+91-9000000004",
            "submission_channel": "web",
        },
        "raw_report": {
            "text": "Building collapse at Tambaram construction site. Reports of 15-20 workers trapped under rubble. Multiple injuries suspected. Need heavy rescue equipment and trauma medical teams immediately. Access road partially blocked by debris.",
            "images": [],
            "metadata": {},
        },
        "location": {
            "type": "Point",
            "coordinates": [80.1270, 12.9249],
            "address": "Tambaram East, Chennai",
            "landmark": "Near Tambaram Railway Station",
            "region": "South Chennai",
        },
        "ai_analysis": {
            "incident_type": "collapse",
            "severity": "catastrophic",
            "urgency": "immediate",
            "people_affected": 20,
            "vulnerable_populations": {"children": 0, "elderly": 0, "disabled": 0, "pregnant": 0, "chronic_illness": 0},
            "resource_requirements": [
                {"resource_type": "fire_unit", "quantity": 2, "urgency": "immediate"},
                {"resource_type": "medical_team", "quantity": 3, "urgency": "immediate"},
                {"resource_type": "ambulance", "quantity": 5, "urgency": "immediate"},
                {"resource_type": "volunteer_team", "quantity": 2, "urgency": "high"},
            ],
            "confidence_score": 0.88,
            "reasoning": "Building collapse with confirmed trapped individuals requires immediate heavy rescue. Time-critical scenario — survival rates drop significantly after first few hours. Blocked access road adds complexity.",
            "processed_at": datetime.utcnow(),
        },
        "impact_estimate": {
            "medical_demand": 20,
            "shelter_demand": 0,
            "food_water_demand": 50,
            "rescue_demand": 20,
            "infrastructure_damage_score": 9.0,
            "estimated_duration_hours": 48,
        },
        "priority": {
            "score": 89.0,
            "rank": 2,
            "factors": {
                "severity_score": 20.0,
                "urgency_score": 20.0,
                "people_affected_score": 8.0,
                "vulnerability_score": 5.0,
                "resource_scarcity_score": 15.0,
                "accessibility_score": 12.0,
                "shelter_load_score": 2.0,
                "hospital_load_score": 7.0,
            },
            "explanation": "CATASTROPHIC: Building collapse with 15-20 trapped workers. Time-critical rescue required. Access road partially blocked increases response complexity. Nearest hospital overwhelmed.",
            "calculated_at": datetime.utcnow(),
        },
        "assigned_resources": [],
        "response_plan": {"recommended_actions": [], "resource_assignments": [], "expected_impact": "", "alternatives": [], "explanation": ""},
        "timeline": [
            {"event": "Report submitted", "timestamp": datetime.utcnow() - timedelta(hours=1), "actor": "hospital"},
            {"event": "AI analysis completed", "timestamp": datetime.utcnow() - timedelta(minutes=55), "actor": "system"},
            {"event": "Status changed to verified", "timestamp": datetime.utcnow() - timedelta(minutes=45), "actor": "coordinator"},
        ],
        "created_at": datetime.utcnow() - timedelta(hours=1),
        "updated_at": datetime.utcnow() - timedelta(minutes=45),
    },
    {
        "incident_id": generate_incident_id(),
        "status": "new",
        "source": {
            "type": "citizen",
            "reporter_name": "Suresh Babu",
            "reporter_contact": "+91-9000000030",
            "submission_channel": "web",
        },
        "raw_report": {
            "text": "Power outage across entire Adyar area since morning. Multiple traffic signals down, causing accidents. Hospital backup generators running low on fuel. Street lights off, creating safety hazard at night. Approximately 50,000 residents affected.",
            "images": [],
            "metadata": {},
        },
        "location": {
            "type": "Point",
            "coordinates": [80.2565, 13.0067],
            "address": "Adyar, Chennai",
            "landmark": "Near IIT Madras",
            "region": "South Chennai",
        },
        "ai_analysis": {
            "incident_type": "power_outage",
            "severity": "high",
            "urgency": "high",
            "people_affected": 50000,
            "vulnerable_populations": {"children": 5000, "elderly": 8000, "disabled": 500, "pregnant": 200, "chronic_illness": 1500},
            "resource_requirements": [
                {"resource_type": "generator", "quantity": 5, "urgency": "immediate"},
                {"resource_type": "police_unit", "quantity": 3, "urgency": "high"},
            ],
            "confidence_score": 0.85,
            "reasoning": "Widespread power outage affecting critical infrastructure including hospitals and traffic systems. Large population affected with significant vulnerable groups. Hospital generator fuel shortage creates secondary medical emergency risk.",
            "processed_at": datetime.utcnow(),
        },
        "impact_estimate": {
            "medical_demand": 30,
            "shelter_demand": 0,
            "food_water_demand": 0,
            "rescue_demand": 0,
            "infrastructure_damage_score": 6.0,
            "estimated_duration_hours": 24,
        },
        "priority": {
            "score": 72.0,
            "rank": 3,
            "factors": {
                "severity_score": 15.0,
                "urgency_score": 15.0,
                "people_affected_score": 20.0,
                "vulnerability_score": 12.0,
                "resource_scarcity_score": 5.0,
                "accessibility_score": 3.0,
                "shelter_load_score": 0.0,
                "hospital_load_score": 2.0,
            },
            "explanation": "HIGH: Widespread power outage affecting 50,000+ residents. Hospital backup generators at risk. Traffic signal failures causing accidents. Significant vulnerable population affected.",
            "calculated_at": datetime.utcnow(),
        },
        "assigned_resources": [],
        "response_plan": {"recommended_actions": [], "resource_assignments": [], "expected_impact": "", "alternatives": [], "explanation": ""},
        "timeline": [
            {"event": "Report submitted", "timestamp": datetime.utcnow() - timedelta(minutes=30), "actor": "citizen"},
            {"event": "AI analysis completed", "timestamp": datetime.utcnow() - timedelta(minutes=25), "actor": "system"},
        ],
        "created_at": datetime.utcnow() - timedelta(minutes=30),
        "updated_at": datetime.utcnow() - timedelta(minutes=25),
    },
    {
        "incident_id": generate_incident_id(),
        "status": "assigned",
        "source": {
            "type": "field_officer",
            "reporter_name": "Rajesh Kumar",
            "reporter_contact": "+91-9000000003",
            "submission_channel": "mobile",
        },
        "raw_report": {
            "text": "Medical emergency at Perambur relief camp. Outbreak of waterborne disease. 35 people showing symptoms of acute diarrhea and dehydration. 8 children critically ill. Camp sanitation facilities overwhelmed. Need medical teams, ORS supplies, and water purification equipment immediately.",
            "images": [],
            "metadata": {},
        },
        "location": {
            "type": "Point",
            "coordinates": [80.2339, 13.1187],
            "address": "Perambur, Chennai",
            "landmark": "Near ICF Colony",
            "region": "North Chennai",
        },
        "ai_analysis": {
            "incident_type": "medical",
            "severity": "critical",
            "urgency": "immediate",
            "people_affected": 35,
            "vulnerable_populations": {"children": 8, "elderly": 5, "disabled": 0, "pregnant": 2, "chronic_illness": 3},
            "resource_requirements": [
                {"resource_type": "medical_team", "quantity": 2, "urgency": "immediate"},
                {"resource_type": "medical_kit", "quantity": 5, "urgency": "immediate"},
                {"resource_type": "water_supply", "quantity": 2, "urgency": "immediate"},
                {"resource_type": "ambulance", "quantity": 2, "urgency": "high"},
            ],
            "confidence_score": 0.95,
            "reasoning": "Field officer report with confirmed waterborne disease outbreak. Critically ill children require immediate medical attention. Risk of rapid spread in camp conditions. Sanitation breakdown will worsen the outbreak if not addressed.",
            "processed_at": datetime.utcnow(),
        },
        "impact_estimate": {
            "medical_demand": 35,
            "shelter_demand": 0,
            "food_water_demand": 100,
            "rescue_demand": 0,
            "infrastructure_damage_score": 3.0,
            "estimated_duration_hours": 96,
        },
        "priority": {
            "score": 86.0,
            "rank": 3,
            "factors": {
                "severity_score": 18.0,
                "urgency_score": 20.0,
                "people_affected_score": 10.0,
                "vulnerability_score": 14.0,
                "resource_scarcity_score": 10.0,
                "accessibility_score": 4.0,
                "shelter_load_score": 5.0,
                "hospital_load_score": 5.0,
            },
            "explanation": "CRITICAL: Waterborne disease outbreak with critically ill children. Risk of epidemic spread in camp conditions. Medical intervention urgently needed to prevent fatalities and contain the outbreak.",
            "calculated_at": datetime.utcnow(),
        },
        "assigned_resources": [],
        "response_plan": {"recommended_actions": [], "resource_assignments": [], "expected_impact": "", "alternatives": [], "explanation": ""},
        "timeline": [
            {"event": "Report submitted", "timestamp": datetime.utcnow() - timedelta(hours=3), "actor": "field_officer"},
            {"event": "AI analysis completed", "timestamp": datetime.utcnow() - timedelta(hours=2, minutes=55), "actor": "system"},
            {"event": "Priority score calculated", "timestamp": datetime.utcnow() - timedelta(hours=2, minutes=50), "actor": "system"},
            {"event": "Status changed to assigned", "timestamp": datetime.utcnow() - timedelta(hours=2), "actor": "coordinator"},
        ],
        "created_at": datetime.utcnow() - timedelta(hours=3),
        "updated_at": datetime.utcnow() - timedelta(hours=2),
    },
    {
        "incident_id": generate_incident_id(),
        "status": "in_progress",
        "source": {
            "type": "ngo",
            "reporter_name": "Disaster Relief Foundation",
            "reporter_contact": "+91-9000000040",
            "submission_channel": "api",
        },
        "raw_report": {
            "text": "Evacuation needed for low-lying areas near Adyar River. Water level rising rapidly. Approximately 500 families in danger zones. Many elderly and disabled residents unable to self-evacuate. Need transportation and temporary shelter arrangements.",
            "images": [],
            "metadata": {},
        },
        "location": {
            "type": "Point",
            "coordinates": [80.2574, 13.0122],
            "address": "Adyar River Bank, Chennai",
            "landmark": "Near Adyar Bridge",
            "region": "Central Chennai",
        },
        "ai_analysis": {
            "incident_type": "evacuation",
            "severity": "high",
            "urgency": "high",
            "people_affected": 2000,
            "vulnerable_populations": {"children": 300, "elderly": 250, "disabled": 50, "pregnant": 30, "chronic_illness": 80},
            "resource_requirements": [
                {"resource_type": "volunteer_team", "quantity": 5, "urgency": "immediate"},
                {"resource_type": "rescue_boat", "quantity": 3, "urgency": "high"},
                {"resource_type": "ambulance", "quantity": 2, "urgency": "medium"},
            ],
            "confidence_score": 0.87,
            "reasoning": "NGO report with credible assessment of rising water levels. Large population in danger zone with significant vulnerable groups. Proactive evacuation before conditions worsen is critical.",
            "processed_at": datetime.utcnow(),
        },
        "impact_estimate": {
            "medical_demand": 20,
            "shelter_demand": 2000,
            "food_water_demand": 2000,
            "rescue_demand": 300,
            "infrastructure_damage_score": 5.0,
            "estimated_duration_hours": 120,
        },
        "priority": {
            "score": 78.5,
            "rank": 4,
            "factors": {
                "severity_score": 15.0,
                "urgency_score": 15.0,
                "people_affected_score": 18.0,
                "vulnerability_score": 14.5,
                "resource_scarcity_score": 6.0,
                "accessibility_score": 5.0,
                "shelter_load_score": 3.0,
                "hospital_load_score": 2.0,
            },
            "explanation": "HIGH: Large-scale evacuation needed for 2000 people in flood zone. 710 vulnerable individuals require assisted evacuation. Shelter capacity needs to be verified before mass evacuation.",
            "calculated_at": datetime.utcnow(),
        },
        "assigned_resources": [],
        "response_plan": {"recommended_actions": [], "resource_assignments": [], "expected_impact": "", "alternatives": [], "explanation": ""},
        "timeline": [
            {"event": "Report submitted", "timestamp": datetime.utcnow() - timedelta(hours=5), "actor": "ngo"},
            {"event": "AI analysis completed", "timestamp": datetime.utcnow() - timedelta(hours=4, minutes=55), "actor": "system"},
            {"event": "Status changed to in_progress", "timestamp": datetime.utcnow() - timedelta(hours=4), "actor": "coordinator"},
        ],
        "created_at": datetime.utcnow() - timedelta(hours=5),
        "updated_at": datetime.utcnow() - timedelta(hours=4),
    },
]


async def seed_database():
    """Populate the database with sample data."""
    print("🌱 ResQNet AI — Database Seeding")
    print("=" * 50)

    await connect_mongodb()
    await connect_redis()

    db = get_database()

    # Clear existing data
    print("\n🗑️  Clearing existing data...")
    await db.users.delete_many({})
    await db.incidents.delete_many({})
    await db.resources.delete_many({})
    await db.shelters.delete_many({})
    await db.hospitals.delete_many({})
    await db.audit_logs.delete_many({})
    await db.command_briefs.delete_many({})

    # Seed users
    print(f"\n👤 Seeding {len(SAMPLE_USERS)} users...")
    await db.users.insert_many(SAMPLE_USERS)
    for user in SAMPLE_USERS:
        print(f"   ✅ {user['email']} ({user['role']})")

    # Seed resources
    print(f"\n🚑 Seeding {len(SAMPLE_RESOURCES)} resources...")
    await db.resources.insert_many(SAMPLE_RESOURCES)
    for res in SAMPLE_RESOURCES:
        print(f"   ✅ {res['name']} ({res['type']})")

    # Seed shelters
    print(f"\n🏠 Seeding {len(SAMPLE_SHELTERS)} shelters...")
    await db.shelters.insert_many(SAMPLE_SHELTERS)
    for shelter in SAMPLE_SHELTERS:
        print(f"   ✅ {shelter['name']} — {shelter['current_occupancy']}/{shelter['total_capacity']}")

    # Seed hospitals
    print(f"\n🏥 Seeding {len(SAMPLE_HOSPITALS)} hospitals...")
    await db.hospitals.insert_many(SAMPLE_HOSPITALS)
    for hosp in SAMPLE_HOSPITALS:
        print(f"   ✅ {hosp['name']} — {hosp['available_beds']}/{hosp['total_beds']} beds available")

    # Seed incidents
    print(f"\n🚨 Seeding {len(SAMPLE_INCIDENTS)} incidents...")
    await db.incidents.insert_many(SAMPLE_INCIDENTS)
    for inc in SAMPLE_INCIDENTS:
        print(f"   ✅ {inc['incident_id']} — {inc['ai_analysis']['incident_type']} ({inc['ai_analysis']['severity']}) — Score: {inc['priority']['score']}")

    print("\n" + "=" * 50)
    print("✅ Database seeded successfully!")
    print(f"   Users: {len(SAMPLE_USERS)}")
    print(f"   Resources: {len(SAMPLE_RESOURCES)}")
    print(f"   Shelters: {len(SAMPLE_SHELTERS)}")
    print(f"   Hospitals: {len(SAMPLE_HOSPITALS)}")
    print(f"   Incidents: {len(SAMPLE_INCIDENTS)}")
    print("\n📝 Login credentials:")
    print("   Super Admin:  admin@resqnet.ai / Admin@2024")
    print("   Coordinator:  coordinator@resqnet.ai / Coord@2024")
    print("   Field Officer: fieldofficer@resqnet.ai / Field@2024")
    print("   Hospital:     hospital@resqnet.ai / Hospital@2024")
    print("   Shelter Mgr:  shelter@resqnet.ai / Shelter@2024")
    print("   Volunteer:    volunteer@resqnet.ai / Volunteer@2024")
    print("   Citizen:      citizen@resqnet.ai / Citizen@2024")

    await close_mongodb()
    await close_redis()


if __name__ == "__main__":
    asyncio.run(seed_database())
