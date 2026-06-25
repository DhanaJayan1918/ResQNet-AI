"""
ResQNet AI - Incident API Tests
Integration tests verifying CRUD, role guards, filtering, and workflow actions using async client.
"""

import pytest
from fastapi import status
from io import BytesIO


@pytest.mark.asyncio
async def test_create_incident_citizen(client, citizen_headers):
    """Test that a citizen can successfully submit a new report."""
    payload = {
        "text": "Severe flooding on our street. Need help evacuating my elderly parents.",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "address": "123 Street, Anna Nagar",
        "landmark": "Near post office",
        "reporter_name": "Arjun Nair",
        "reporter_contact": "+91-9000000007"
    }

    response = await client.post("/api/v1/incidents", json=payload, headers=citizen_headers)
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    assert data["incident_id"].startswith("RESQ-")
    assert data["status"] == "new"
    assert data["raw_report"]["text"] == payload["text"]
    assert data["location"]["coordinates"] == [payload["longitude"], payload["latitude"]]
    assert data["source"]["type"] == "citizen"
    assert data["ai_analysis"]["incident_type"] == "flood"
    assert data["ai_analysis"]["severity"] == "high"
    assert data["priority"]["score"] > 30.0  # Should be flagged as severe


@pytest.mark.asyncio
async def test_create_incident_validation_error(client, citizen_headers):
    """Test that submitting an incident with invalid inputs yields validation errors."""
    # Description too short
    payload = {
        "text": "Short",
        "latitude": 13.0827,
        "longitude": 80.2707
    }

    response = await client.post("/api/v1/incidents", json=payload, headers=citizen_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_unauthorized_endpoints(client, citizen_headers):
    """Test that role guards prevent citizens from accessing coordinator actions."""
    # Attempting to fetch priority queue as citizen
    response = await client.get("/api/v1/incidents/priority-queue", headers=citizen_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_incidents_list(client, field_officer_headers, citizen_headers):
    """Test incident listing, filtering, and pagination by authorized roles."""
    # Submit two incidents
    await client.post(
        "/api/v1/incidents",
        json={"text": "Flood water in Velachery residential zone.", "latitude": 12.9816, "longitude": 80.2211},
        headers=citizen_headers
    )
    await client.post(
        "/api/v1/incidents",
        json={"text": "Fire in warehouse at Tambaram.", "latitude": 12.9249, "longitude": 80.1270},
        headers=citizen_headers
    )

    # List incidents as field officer
    response = await client.get("/api/v1/incidents?page=1&page_size=10", headers=field_officer_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Filter by incident type 'wildfire'
    response = await client.get("/api/v1/incidents?incident_type=wildfire", headers=field_officer_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["incident_type"] == "wildfire"


@pytest.mark.asyncio
async def test_update_incident_status(client, coordinator_headers, citizen_headers):
    """Test that a coordinator can verify and update incident status."""
    # Submit report
    create_resp = await client.post(
        "/api/v1/incidents",
        json={"text": "Road block due to landslide near Perambur.", "latitude": 13.1187, "longitude": 80.2339},
        headers=citizen_headers
    )
    incident_id = create_resp.json()["incident_id"]

    # Verify report (update status to verified)
    update_payload = {
        "status": "verified",
        "notes": "Verified through state emergency patrol confirmation."
    }

    response = await client.patch(f"/api/v1/incidents/{incident_id}", json=update_payload, headers=coordinator_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["status"] == "verified"
    
    # Check timeline for the added note
    assert len(data["timeline"]) == 5  # Initial 3 + status updated + coordinator note
    assert data["timeline"][-1]["details"] == update_payload["notes"]


@pytest.mark.asyncio
async def test_bulk_import_reports(client, coordinator_headers):
    """Test bulk importing of incident reports by coordinator."""
    payload = {
        "incidents": [
            {
                "text": "Medical emergency outbreak at local shelter.",
                "latitude": 13.0827,
                "longitude": 80.2707,
                "source_type": "hospital"
            },
            {
                "text": "Power grid breakdown affecting hospital operations.",
                "latitude": 13.0500,
                "longitude": 80.2500,
                "source_type": "ngo"
            }
        ]
    }

    response = await client.post("/api/v1/incidents/bulk-import", json=payload, headers=coordinator_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert len(data) == 2
    assert data[0]["source"]["type"] == "hospital"
    assert data[1]["source"]["type"] == "ngo"


@pytest.mark.asyncio
async def test_merge_duplicate_reports(client, coordinator_headers, citizen_headers):
    """Test duplicate report grouping and merging."""
    # Create primary report
    resp1 = await client.post(
        "/api/v1/incidents",
        json={"text": "Velachery bridge flooded, traffic blocked.", "latitude": 12.9816, "longitude": 80.2211},
        headers=citizen_headers
    )
    primary_id = resp1.json()["incident_id"]

    # Create secondary duplicate report
    resp2 = await client.post(
        "/api/v1/incidents",
        json={"text": "Bridge in Velachery completely submerged, cars stuck.", "latitude": 12.9815, "longitude": 80.2210},
        headers=citizen_headers
    )
    duplicate_id = resp2.json()["incident_id"]

    # Merge duplicate
    merge_payload = {
        "primary_incident_id": primary_id,
        "duplicate_incident_ids": [duplicate_id]
    }

    response = await client.post(f"/api/v1/incidents/{primary_id}/merge", json=merge_payload, headers=coordinator_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check that primary has duplicate group id set
    primary_data = response.json()
    assert primary_data["duplicate_group_id"] is not None

    # Check duplicate status has changed to 'duplicate'
    dup_details_resp = await client.get(f"/api/v1/incidents/{duplicate_id}", headers=coordinator_headers)
    dup_details = dup_details_resp.json()
    assert dup_details["status"] == "duplicate"
    assert dup_details["duplicate_group_id"] == primary_data["duplicate_group_id"]


@pytest.mark.asyncio
async def test_upload_image(client, citizen_headers):
    """Test image upload endpoint."""
    file_content = b"fake-image-bytes"
    file_name = "test.png"
    
    response = await client.post(
        "/api/v1/incidents/upload",
        files={"file": (file_name, BytesIO(file_content), "image/png")},
        headers=citizen_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "image_url" in data
    assert data["image_url"].startswith("/uploads/")
    assert data["image_url"].endswith(".png")
