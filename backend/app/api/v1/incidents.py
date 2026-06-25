"""
ResQNet AI - Incident Routes
Defines all FastAPI routes for emergency reports intake, priority queue, bulk imports, and CRUD.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
import uuid
import shutil
from pathlib import Path

from app.config import get_settings
from app.schemas.incident import (
    CreateIncidentRequest, UpdateIncidentRequest, BulkImportRequest,
    MergeIncidentsRequest, IncidentFilterParams, IncidentSummaryResponse,
    IncidentDetailResponse,
)
from app.schemas.common import PaginatedResponse
from app.api.middleware.auth import (
    require_citizen, require_field_officer, require_coordinator,
)
from app.services.incident_service import (
    create_incident, get_incidents, get_total_incidents_count,
    get_incident_by_id, update_incident, reprocess_incident_ai,
    get_priority_queue, get_priority_queue_count, bulk_import_incidents,
    merge_duplicate_incidents,
)
from app.schemas.common import PaginationParams

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post("/upload", response_model=dict)
async def upload_image_endpoint(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_citizen)
):
    """
    Upload an incident image.
    Access: Citizen or higher.
    """
    settings = get_settings()
    # Validate file extension
    filename_split = file.filename.split(".") if file.filename else []
    extension = filename_split[-1].lower() if len(filename_split) > 1 else ""
    if extension not in ["jpg", "jpeg", "png", "gif"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only images (jpg, jpeg, png, gif) are allowed"
        )
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}.{extension}"
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )
        
    return {"image_url": f"/uploads/{filename}"}


def map_doc_to_summary(doc: dict) -> IncidentSummaryResponse:
    """Helper to map MongoDB incident document to summary schema."""
    # Handle optional fields and provide defaults
    ai_analysis = doc.get("ai_analysis", {})
    priority = doc.get("priority", {})
    location = doc.get("location", {})
    raw_report = doc.get("raw_report", {})

    return IncidentSummaryResponse(
        id=doc["id"],
        incident_id=doc["incident_id"],
        status=doc["status"],
        incident_type=ai_analysis.get("incident_type", "other"),
        severity=ai_analysis.get("severity", "moderate"),
        urgency=ai_analysis.get("urgency", "medium"),
        priority_score=priority.get("score", 0.0),
        people_affected=ai_analysis.get("people_affected", 0),
        location=location,
        address=location.get("address"),
        text_preview=raw_report.get("text", "")[:200] + ("..." if len(raw_report.get("text", "")) > 200 else ""),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"]
    )


def map_doc_to_detail(doc: dict) -> IncidentDetailResponse:
    """Helper to map MongoDB incident document to detail schema."""
    return IncidentDetailResponse(
        id=doc["id"],
        incident_id=doc["incident_id"],
        status=doc["status"],
        source=doc.get("source", {}),
        raw_report=doc.get("raw_report", {}),
        location=doc.get("location", {}),
        ai_analysis=doc.get("ai_analysis", {}),
        impact_estimate=doc.get("impact_estimate", {}),
        priority=doc.get("priority", {}),
        duplicate_group_id=doc.get("duplicate_group_id"),
        assigned_resources=doc.get("assigned_resources", []),
        response_plan=doc.get("response_plan", {}),
        timeline=doc.get("timeline", []),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"]
    )


@router.post("", response_model=IncidentDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_incident_endpoint(
    request: CreateIncidentRequest,
    current_user: dict = Depends(require_citizen)
):
    """
    Submit a new incident report.
    Access: Citizen or higher.
    """
    try:
        doc = await create_incident(
            request=request,
            actor_id=current_user["_id"],
            actor_role=current_user["role"]
        )
        return map_doc_to_detail(doc)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to submit incident: {str(e)}"
        )


@router.get("/priority-queue", response_model=PaginatedResponse[IncidentSummaryResponse])
async def get_priority_queue_endpoint(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(require_coordinator)
):
    """
    Get the active incidents in the priority queue, sorted by priority score descending.
    Access: Coordinator or higher.
    """
    docs = await get_priority_queue(limit=pagination.page_size, skip=pagination.skip)
    total = await get_priority_queue_count()
    items = [map_doc_to_summary(doc) for doc in docs]
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.post("/bulk-import", response_model=List[IncidentDetailResponse])
async def bulk_import_endpoint(
    request: BulkImportRequest,
    current_user: dict = Depends(require_coordinator)
):
    """
    Bulk import multiple incident reports.
    Access: Coordinator or higher.
    """
    try:
        docs = await bulk_import_incidents(
            request=request,
            actor_id=current_user["_id"],
            actor_role=current_user["role"]
        )
        return [map_doc_to_detail(doc) for doc in docs]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bulk import failed: {str(e)}"
        )


@router.get("", response_model=PaginatedResponse[IncidentSummaryResponse])
async def get_incidents_endpoint(
    filters: IncidentFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(require_field_officer)
):
    """
    List incidents with optional filtering (status, severity, urgency, proximity) and pagination.
    Access: Field Officer or higher.
    """
    query_filter = filters.to_mongo_filter()
    docs = await get_incidents(
        query_filter=query_filter,
        limit=pagination.page_size,
        skip=pagination.skip
    )
    total = await get_total_incidents_count(query_filter)
    items = [map_doc_to_summary(doc) for doc in docs]
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get("/{id}", response_model=IncidentDetailResponse)
async def get_incident_endpoint(
    id: str,
    current_user: dict = Depends(require_field_officer)
):
    """
    Get full details of a specific incident by ID or custom incident_id.
    Access: Field Officer or higher.
    """
    doc = await get_incident_by_id(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {id} not found"
        )
    return map_doc_to_detail(doc)


@router.patch("/{id}", response_model=IncidentDetailResponse)
async def update_incident_endpoint(
    id: str,
    request: UpdateIncidentRequest,
    current_user: dict = Depends(require_coordinator)
):
    """
    Update an incident's status or add coordinator notes.
    Access: Coordinator or higher.
    """
    doc = await update_incident(
        incident_id=id,
        request=request,
        actor_id=current_user["_id"],
        actor_name=current_user["full_name"],
        actor_role=current_user["role"]
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {id} not found"
        )
    return map_doc_to_detail(doc)


@router.post("/{id}/reprocess", response_model=IncidentDetailResponse)
async def reprocess_incident_endpoint(
    id: str,
    current_user: dict = Depends(require_coordinator)
):
    """
    Manually trigger AI analysis and priority calculation for an incident.
    Access: Coordinator or higher.
    """
    doc = await reprocess_incident_ai(
        incident_id=id,
        actor_id=current_user["_id"],
        actor_role=current_user["role"]
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {id} not found"
        )
    return map_doc_to_detail(doc)


@router.get("/{id}/timeline", response_model=List[dict])
async def get_incident_timeline_endpoint(
    id: str,
    current_user: dict = Depends(require_field_officer)
):
    """
    Get the event timeline for a specific incident.
    Access: Field Officer or higher.
    """
    doc = await get_incident_by_id(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {id} not found"
        )
    return doc.get("timeline", [])


@router.post("/{id}/merge", response_model=IncidentDetailResponse)
async def merge_incidents_endpoint(
    id: str,
    request: MergeIncidentsRequest,
    current_user: dict = Depends(require_coordinator)
):
    """
    Merge duplicate reports into this incident.
    Access: Coordinator or higher.
    """
    if id != request.primary_incident_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident ID in URL must match primary_incident_id in request body"
        )
        
    doc = await merge_duplicate_incidents(
        request=request,
        actor_id=current_user["_id"],
        actor_role=current_user["role"],
        actor_name=current_user["full_name"]
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {id} not found"
        )
    return map_doc_to_detail(doc)
