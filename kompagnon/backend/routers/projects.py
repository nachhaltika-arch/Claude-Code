"""
Project Management API routes.
GET /api/projects/ - List all projects
GET /api/projects/debug - Diagnostic info (counts, sample rows)
POST /api/projects/seed - Seed projects from leads (admin)
GET /api/projects/{id} - Project detail
PATCH /api/projects/{id}/phase - Change phase
POST /api/projects/{id}/time - Log hours
GET /api/projects/{id}/checklist - Get checklist
PATCH /api/projects/{id}/checklist/{item_key} - Check item
GET /api/projects/{id}/margin - Get margin
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
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

logger = logging.getLogger(__name__)

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


@router.get("/debug")
def debug_projects(db: Session = Depends(get_db)):
    """Diagnostic: raw project + lead counts and sample rows."""
    try:
        project_count = db.execute(text("SELECT COUNT(*) FROM projects")).scalar()
        lead_count = db.execute(text("SELECT COUNT(*) FROM leads")).scalar()
        won_count = db.execute(text("SELECT COUNT(*) FROM leads WHERE status = 'won'")).scalar()
        table_exists = db.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'projects')")
        ).scalar()
        sample = db.execute(
            text("SELECT id, lead_id, status, created_at FROM projects ORDER BY id DESC LIMIT 5")
        ).fetchall()
        leads_sample = db.execute(
            text("SELECT id, company_name, status FROM leads ORDER BY created_at DESC LIMIT 5")
        ).fetchall()
        return {
            "table_exists": table_exists,
            "project_count": project_count,
            "lead_count": lead_count,
            "won_lead_count": won_count,
            "projects_sample": [
                {"id": r[0], "lead_id": r[1], "status": r[2], "created_at": str(r[3])}
                for r in sample
            ],
            "leads_sample": [
                {"id": r[0], "company_name": r[1], "status": r[2]}
                for r in leads_sample
            ],
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/seed")
def seed_projects(db: Session = Depends(get_db)):
    """
    Admin: Create projects from leads that have none yet.
    Priority: status='won' leads first, then all others as fallback
    if projects table is completely empty.
    """
    project_count = db.query(Project).count()
    won_leads = db.query(Lead).filter(
        Lead.status == "won",
        ~Lead.projects.any()
    ).all()

    seeded = []

    # Always seed won leads
    for lead in won_leads:
        now = datetime.utcnow()
        p = Project(lead_id=lead.id, status="phase_1", start_date=now,
                    created_at=now, updated_at=now)
        for col, val in [
            ("company_name", lead.company_name),
            ("website_url",  lead.website_url),
            ("contact_name", lead.contact_name),
            ("contact_email", lead.email),
        ]:
            try:
                setattr(p, col, val)
            except Exception:
                pass
        db.add(p)
        seeded.append({"lead_id": lead.id, "company": lead.company_name, "reason": "won"})

    # If table was completely empty, also seed non-won leads
    if project_count == 0 and not won_leads:
        all_leads_without_project = db.query(Lead).filter(
            ~Lead.projects.any()
        ).order_by(Lead.id.desc()).limit(50).all()
        for lead in all_leads_without_project:
            now = datetime.utcnow()
            p = Project(lead_id=lead.id, status="phase_1", start_date=now,
                        created_at=now, updated_at=now)
            for col, val in [
                ("company_name", lead.company_name),
                ("website_url",  lead.website_url),
                ("contact_name", lead.contact_name),
                ("contact_email", lead.email),
            ]:
                try:
                    setattr(p, col, val)
                except Exception:
                    pass
            db.add(p)
            seeded.append({"lead_id": lead.id, "company": lead.company_name, "reason": "fallback"})

    if seeded:
        db.commit()
    logger.info(f"Seed: {len(seeded)} projects created")
    return {"seeded": len(seeded), "details": seeded}


@router.get("/")
def list_projects(
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(200),
    db: Session = Depends(get_db),
):
    """List all projects. Returns raw dicts to prevent silent Pydantic filtering."""
    try:
        query = db.query(Project)
        if status:
            query = query.filter(Project.status == status)
        projects = query.offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"list_projects DB error: {e}")
        return []
    result = []
    for p in projects:
        try:
            lead = p.lead if p.lead_id else None
            result.append({
                "id": p.id,
                "lead_id": p.lead_id,
                "name": getattr(p, "name", "") or "",
                "customer_name": getattr(p, "customer_name", "") or (lead.company_name if lead else ""),
                "company_name": getattr(p, "company_name", "") or (lead.company_name if lead else ""),
                "status": p.status or "aktiv",
                "current_phase": getattr(p, "current_phase", 1) or 1,
                "website_url": getattr(p, "website_url", "") or (lead.website_url if lead else ""),
                "cms_type": getattr(p, "cms_type", None),
                "contact_name": getattr(p, "contact_name", "") or (lead.contact_name if lead else ""),
                "contact_phone": getattr(p, "contact_phone", None),
                "contact_email": getattr(p, "contact_email", "") or (lead.email if lead else ""),
                "go_live_date": str(getattr(p, "go_live_date", "") or ""),
                "package_type": getattr(p, "package_type", None),
                "payment_status": getattr(p, "payment_status", None),
                "desired_pages": getattr(p, "desired_pages", None),
                "has_logo": getattr(p, "has_logo", False),
                "has_briefing": getattr(p, "has_briefing", False),
                "has_photos": getattr(p, "has_photos", False),
                "pagespeed_mobile": getattr(p, "pagespeed_mobile", None),
                "pagespeed_desktop": getattr(p, "pagespeed_desktop", None),
                "audit_score": getattr(p, "audit_score", None),
                "audit_level": getattr(p, "audit_level", None),
                "top_problems": getattr(p, "top_problems", None),
                "industry": getattr(p, "industry", None),
                "fixed_price": p.fixed_price or 0.0,
                "actual_hours": p.actual_hours or 0.0,
                "start_date": str(p.start_date)[:10] if p.start_date else "",
                "target_go_live": str(p.target_go_live)[:10] if p.target_go_live else "",
                "created_at": str(p.created_at)[:10] if p.created_at else "",
            })
        except Exception as e:
            logger.warning(f"list_projects: skipping project {getattr(p, 'id', '?')}: {e}")
            continue
    logger.info(f"list_projects: returning {len(result)} of {len(projects)} projects")
    return result


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get project detail. Raw dict — no Pydantic response_model to prevent silent filtering."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    lead = None
    if project.lead_id:
        lead = db.query(Lead).filter(Lead.id == project.lead_id).first()
    return {
        "id": project.id,
        "lead_id": project.lead_id,
        "name": getattr(project, "name", "") or "",
        "customer_name": getattr(project, "customer_name", "") or (lead.company_name if lead else ""),
        "company_name": getattr(project, "company_name", "") or (lead.company_name if lead else ""),
        "status": project.status or "akquise",
        "current_phase": getattr(project, "current_phase", 1) or 1,
        "website_url": getattr(project, "website_url", "") or (lead.website_url if lead else ""),
        "cms_type": getattr(project, "cms_type", None),
        "contact_name": getattr(project, "contact_name", "") or (lead.contact_name if lead else ""),
        "contact_phone": getattr(project, "contact_phone", None),
        "contact_email": getattr(project, "contact_email", "") or (lead.email if lead else ""),
        "go_live_date": str(getattr(project, "go_live_date", "") or ""),
        "package_type": getattr(project, "package_type", None),
        "payment_status": getattr(project, "payment_status", None),
        "desired_pages": getattr(project, "desired_pages", None),
        "has_logo": getattr(project, "has_logo", False),
        "has_briefing": getattr(project, "has_briefing", False),
        "has_photos": getattr(project, "has_photos", False),
        "pagespeed_mobile": getattr(project, "pagespeed_mobile", None),
        "pagespeed_desktop": getattr(project, "pagespeed_desktop", None),
        "audit_score": getattr(project, "audit_score", None),
        "audit_level": getattr(project, "audit_level", None),
        "top_problems": getattr(project, "top_problems", None),
        "industry": getattr(project, "industry", None),
        "fixed_price": project.fixed_price or 2000,
        "actual_hours": project.actual_hours or 0,
        "hourly_rate": project.hourly_rate or 45,
        "ai_tool_costs": project.ai_tool_costs or 50,
        "margin_percent": project.margin_percent or 0,
        "scope_creep_flags": project.scope_creep_flags or 0,
        "start_date": str(project.start_date)[:10] if project.start_date else "",
        "target_go_live": str(project.target_go_live)[:10] if project.target_go_live else "",
        "actual_go_live": str(project.actual_go_live)[:10] if project.actual_go_live else "",
        "created_at": str(project.created_at)[:10] if project.created_at else "",
        # Lead fields (direct access for components that use lead.X)
        "email": lead.email if lead else "",
        "phone": lead.phone if lead else "",
        "city": lead.city if lead else "",
        "trade": lead.trade if lead else "",
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
    Create a project from any lead (Nutzerkartei).

    - 404 if lead not found
    - 409 if a project for this lead already exists
    - 201 + project JSON on success
    """
    # 1. Resolve lead
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    # 2. Guard against duplicates
    existing = db.query(Project).filter(Project.lead_id == lead_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Für diesen Lead existiert bereits ein Projekt")

    # 3. Create project
    company_name = lead.company_name or f"Lead #{lead_id}"
    now = datetime.utcnow()
    project = Project(
        lead_id=lead_id,
        status="phase_1",
        start_date=now,
        created_at=now,
        updated_at=now,
    )
    # Set extra columns via setattr so missing ORM fields don't crash
    for col, val in [
        ("company_name", company_name),
        ("website_url",  lead.website_url),
        ("contact_name", lead.contact_name),
        ("contact_email", lead.email),
    ]:
        try:
            setattr(project, col, val)
        except Exception:
            pass
    db.add(project)
    db.commit()
    db.refresh(project)

    # 4. Try to find an existing customer linked via email
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
        "website_url": lead.website_url,
        "start_date": project.start_date.isoformat(),
        "created_at": project.created_at.isoformat(),
        "customer_id": customer_id,
        "message": f"Projekt 'Website – {company_name}' wurde erfolgreich angelegt",
    }
