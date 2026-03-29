"""
Project Management API routes.
GET /api/projects/ - List all projects
GET /api/projects/{id} - Project detail
PATCH /api/projects/{id}/phase - Change phase
POST /api/projects/{id}/time - Log hours
GET /api/projects/{id}/checklist - Get checklist
PATCH /api/projects/{id}/checklist/{item_key} - Check item
GET /api/projects/{id}/margin - Get margin
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from database import Project, ProjectChecklist, TimeTracking, Lead, get_db
from services.margin_calculator import MarginCalculator
from automations.scheduler import (
    get_scheduler,
    job_tag_5_followup,
    job_tag_14_funktionscheck,
    job_tag_21_bewertungsanfrage,
    job_tag_30_geo_check,
    job_tag_30_upsell,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectResponse(BaseModel):
    id: int
    lead_id: int
    status: str
    start_date: datetime = None
    target_go_live: datetime = None
    actual_go_live: datetime = None
    fixed_price: float
    actual_hours: float
    hourly_rate: float
    ai_tool_costs: float
    margin_percent: float
    scope_creep_flags: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    company_name: str
    contact_name: str
    email: str


class TimeLogRequest(BaseModel):
    hours: float
    phase: int = None
    logged_by: str
    activity_description: str = None


class ChecklistItemResponse(BaseModel):
    id: int
    phase: int
    item_key: str
    item_label: str
    responsible: str
    is_critical: bool
    is_completed: bool
    completed_at: datetime = None
    completed_by: str = None

    class Config:
        from_attributes = True


class ChecklistItemUpdate(BaseModel):
    is_completed: bool
    completed_by: str = None


class PhaseChangeRequest(BaseModel):
    new_status: str


class MarginResponse(BaseModel):
    human_hours: float
    human_costs: float
    ai_tool_costs: float
    total_costs: float
    margin_eur: float
    margin_percent: float
    hours_remaining_at_target: float
    status: str  # green, yellow, red
    alert: bool
    target_margin: float
    min_acceptable_margin: float


@router.get("/", response_model=list[ProjectResponse])
def list_projects(
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db),
):
    """List all projects, optionally filtered by status."""
    query = db.query(Project)
    if status:
        query = query.filter(Project.status == status)
    projects = query.offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get project detail with lead information."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Build response with lead data
    lead = project.lead
    return {
        **{
            "id": project.id,
            "lead_id": project.lead_id,
            "status": project.status,
            "start_date": project.start_date,
            "target_go_live": project.target_go_live,
            "actual_go_live": project.actual_go_live,
            "fixed_price": project.fixed_price,
            "actual_hours": project.actual_hours,
            "hourly_rate": project.hourly_rate,
            "ai_tool_costs": project.ai_tool_costs,
            "margin_percent": project.margin_percent,
            "scope_creep_flags": project.scope_creep_flags,
            "created_at": project.created_at,
        },
        "company_name": lead.company_name if lead else "N/A",
        "contact_name": lead.contact_name if lead else "N/A",
        "email": lead.email if lead else "N/A",
    }


@router.patch("/{project_id}/phase")
def change_phase(
    project_id: int,
    change_request: PhaseChangeRequest,
    db: Session = Depends(get_db),
):
    """Change project phase and trigger automations."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    old_status = project.status
    project.status = change_request.new_status
    db.commit()

    # Trigger scheduler for phase-specific automations
    scheduler = get_scheduler()
    scheduler.trigger_phase_change(project_id, change_request.new_status)

    return {
        "project_id": project_id,
        "old_status": old_status,
        "new_status": change_request.new_status,
        "timestamp": datetime.utcnow(),
        "message": f"Phase changed to {change_request.new_status}",
    }


@router.post("/{project_id}/time")
def log_time(
    project_id: int,
    time_log: TimeLogRequest,
    db: Session = Depends(get_db),
):
    """Log hours spent on a project and update margin."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        # Log time
        time_entry = MarginCalculator.log_time(
            db=db,
            project_id=project_id,
            hours=time_log.hours,
            logged_by=time_log.logged_by,
            phase=time_log.phase,
            activity_description=time_log.activity_description,
        )

        # Get updated margin
        margin = MarginCalculator.calculate_margin(db, project_id)

        return {
            "time_entry_id": time_entry.id,
            "hours_logged": time_log.hours,
            "logged_by": time_log.logged_by,
            "updated_margin": margin,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Time logging failed: {str(e)}")


@router.get("/{project_id}/checklist", response_model=list[ChecklistItemResponse])
def get_checklist(
    project_id: int,
    phase: int = Query(None),
    db: Session = Depends(get_db),
):
    """Get project checklist, optionally filtered by phase."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    query = db.query(ProjectChecklist).filter(ProjectChecklist.project_id == project_id)
    if phase:
        query = query.filter(ProjectChecklist.phase == phase)

    items = query.all()
    return items


@router.patch("/{project_id}/checklist/{item_key}")
def update_checklist_item(
    project_id: int,
    item_key: str,
    update: ChecklistItemUpdate,
    db: Session = Depends(get_db),
):
    """Mark checklist item as complete."""
    item = (
        db.query(ProjectChecklist)
        .filter(
            ProjectChecklist.project_id == project_id,
            ProjectChecklist.item_key == item_key,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    item.is_completed = update.is_completed
    if update.is_completed:
        item.completed_at = datetime.utcnow()
        item.completed_by = update.completed_by or "unknown"
    db.commit()

    return {
        "item_key": item_key,
        "is_completed": item.is_completed,
        "completed_at": item.completed_at,
        "completed_by": item.completed_by,
    }


@router.get("/{project_id}/margin", response_model=MarginResponse)
def get_margin(project_id: int, db: Session = Depends(get_db)):
    """Get real-time margin for project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    margin = MarginCalculator.calculate_margin(db, project_id)
    if "error" in margin:
        raise HTTPException(status_code=500, detail=margin["error"])

    return margin


@router.post("/{project_id}/trigger")
def trigger_automation(
    project_id: int,
    automation_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Manually trigger an automation for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Map automation IDs to standalone job functions
    automation_map = {
        "tag_5_followup": job_tag_5_followup,
        "tag_14_check": job_tag_14_funktionscheck,
        "tag_21_review": job_tag_21_bewertungsanfrage,
        "tag_30_geo": job_tag_30_geo_check,
        "tag_30_upsell": job_tag_30_upsell,
    }

    if automation_id not in automation_map:
        raise HTTPException(status_code=400, detail=f"Unknown automation: {automation_id}")

    try:
        automation_map[automation_id](project_id)
        return {
            "project_id": project_id,
            "automation_id": automation_id,
            "status": "triggered",
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Automation failed: {str(e)}")
