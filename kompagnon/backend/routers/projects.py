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
from database import Project, ProjectChecklist, TimeTracking, Lead, Customer, get_db
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
    lead_id: int = None
    status: str = None
    start_date: datetime = None
    target_go_live: datetime = None
    actual_go_live: datetime = None
    fixed_price: float = 0.0
    actual_hours: float = 0.0
    hourly_rate: float = 0.0
    ai_tool_costs: float = 0.0
    margin_percent: float = 0.0
    scope_creep_flags: int = 0
    created_at: datetime = None
    # redesign fields
    company_name: str = None
    website_url: str = None
    cms_type: str = None
    contact_name: str = None
    contact_phone: str = None
    contact_email: str = None
    go_live_date: str = None
    package_type: str = None
    payment_status: str = None
    desired_pages: str = None
    has_logo: bool = None
    has_briefing: bool = None
    has_photos: bool = None
    pagespeed_mobile: int = None
    pagespeed_desktop: int = None
    audit_score: int = None
    audit_level: str = None
    top_problems: str = None
    industry: str = None

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    email: str = None


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


class ProjectUpdateRequest(BaseModel):
    website_url: str = None
    cms_type: str = None
    contact_name: str = None
    contact_phone: str = None
    contact_email: str = None
    go_live_date: str = None        # ISO date string, e.g. "2025-09-01"
    package_type: str = None
    payment_status: str = None
    desired_pages: str = None
    has_logo: bool = None
    has_briefing: bool = None
    has_photos: bool = None
    pagespeed_mobile: int = None
    pagespeed_desktop: int = None
    audit_score: int = None
    audit_level: str = None
    top_problems: str = None
    industry: str = None


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
    rows = query.offset(skip).limit(limit).all()
    result = []
    for p in rows:
        lead = p.lead
        d = {c.name: getattr(p, c.name) for c in p.__table__.columns}
        if not d.get("company_name") and lead:
            d["company_name"] = lead.company_name
        if not d.get("website_url") and lead:
            d["website_url"] = lead.website_url
        if not d.get("contact_name") and lead:
            d["contact_name"] = lead.contact_name
        if not d.get("contact_email") and lead:
            d["contact_email"] = lead.email
        result.append(d)
    return result


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get project detail with lead information."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Build response with lead data
    lead = project.lead
    return {
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
        # lead-derived defaults (fallback if project fields are empty)
        "company_name": lead.company_name if lead else "N/A",
        "email": lead.email if lead else "N/A",
        # redesign fields
        "website_url": getattr(project, "website_url", None),
        "cms_type": getattr(project, "cms_type", None),
        "contact_name": getattr(project, "contact_name", None) or (lead.contact_name if lead else None),
        "contact_phone": getattr(project, "contact_phone", None),
        "contact_email": getattr(project, "contact_email", None),
        "go_live_date": getattr(project, "go_live_date", None),
        "package_type": getattr(project, "package_type", None),
        "payment_status": getattr(project, "payment_status", None),
        "desired_pages": getattr(project, "desired_pages", None),
        "has_logo": getattr(project, "has_logo", None),
        "has_briefing": getattr(project, "has_briefing", None),
        "has_photos": getattr(project, "has_photos", None),
        "pagespeed_mobile": getattr(project, "pagespeed_mobile", None),
        "pagespeed_desktop": getattr(project, "pagespeed_desktop", None),
        "audit_score": getattr(project, "audit_score", None),
        "audit_level": getattr(project, "audit_level", None),
        "top_problems": getattr(project, "top_problems", None),
        "industry": getattr(project, "industry", None),
    }


@router.put("/{project_id}")
def update_project(project_id: int, body: ProjectUpdateRequest, db: Session = Depends(get_db)):
    """Update redesign fields on a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return {"id": project.id, "updated": list(update_data.keys())}


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


@router.post("/from-lead/{lead_id}", status_code=201)
def create_project_from_lead(lead_id: int, db: Session = Depends(get_db)):
    """
    Automatically create a project from a won lead.

    - 400 if lead status is not 'won'
    - 409 if a project for this lead already exists
    - 201 + project JSON on success
    """
    # 1. Resolve lead
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    # 2. Verify won status
    if lead.status != "won":
        raise HTTPException(
            status_code=400,
            detail=f"Lead ist nicht als gewonnen markiert (aktueller Status: {lead.status or 'unbekannt'})",
        )

    # 3. Guard against duplicates
    existing = db.query(Project).filter(Project.lead_id == lead_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Für diesen Lead existiert bereits ein Projekt")

    # 4. Create project
    company_name = lead.company_name or f"Lead #{lead_id}"
    now = datetime.utcnow()
    project = Project(
        lead_id=lead_id,
        status="phase_1",
        start_date=now,
        created_at=now,
        updated_at=now,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # 5. Try to find an existing customer linked to a project with the same e-mail
    customer_id = None
    if lead.email:
        linked = (
            db.query(Customer)
            .join(Project, Customer.project_id == Project.id)
            .join(Lead, Project.lead_id == Lead.id)
            .filter(Lead.email == lead.email, Lead.id != lead_id)
            .first()
        )
        if linked:
            customer_id = linked.id

    return {
        "id": project.id,
        "lead_id": project.lead_id,
        "status": project.status,
        "company_name": company_name,
        "project_name": f"Website – {company_name}",
        "start_date": project.start_date.isoformat(),
        "created_at": project.created_at.isoformat(),
        "customer_id": customer_id,
        "message": f"Projekt 'Website – {company_name}' wurde erfolgreich angelegt",
    }
