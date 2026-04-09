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
import threading
import os
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

logger = logging.getLogger(__name__)


def _get_fernet():
    """
    Gibt eine Fernet-Instanz zurück.
    CREDENTIALS_KEY muss ein 32-Byte URL-safe base64 Key sein.
    Generierung: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

    Kein Fallback: wenn CREDENTIALS_KEY fehlt oder ungültig ist,
    wird eine RuntimeError geworfen — niemals zufällige oder unsichere Keys.
    """
    from cryptography.fernet import Fernet
    key = os.getenv("CREDENTIALS_KEY", "")
    if not key:
        raise RuntimeError(
            "CREDENTIALS_KEY Umgebungsvariable nicht gesetzt. "
            "Bitte in Render.com Environment eintragen. "
            "Generieren mit: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as e:
        raise RuntimeError(
            f"CREDENTIALS_KEY ist ungültig ({e}). "
            f"Muss ein 32-Byte URL-safe base64-encoded Fernet-Key sein."
        ) from e


def _fernet_available() -> bool:
    """True wenn CREDENTIALS_KEY gültig gesetzt ist."""
    try:
        _get_fernet()
        return True
    except Exception:
        return False


from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from database import Project, ProjectChecklist, TimeTracking, Lead, Customer, ProjectScrapeJob, get_db
from services.margin_calculator import MarginCalculator
from routers.content_scraper_router import _run_content_scrape
from email_service import send_phase_change_email, send_approval_request_email
from routers.auth_router import require_admin, get_current_user
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
    lead_id: Optional[int] = None
    name: Optional[str] = None
    customer_name: Optional[str] = None
    status: Optional[str] = None
    current_phase: Optional[int] = None
    website_url: Optional[str] = None
    cms_type: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    industry: Optional[str] = None
    wz_code: Optional[str] = None
    wz_title: Optional[str] = None
    package_type: Optional[str] = None
    payment_status: Optional[str] = None
    desired_pages: Optional[str] = None
    top_problems: Optional[str] = None
    customer_email: Optional[str] = None
    hosting_provider: Optional[str] = None
    domain_registrar: Optional[str] = None
    nameserver1: Optional[str] = None
    nameserver2: Optional[str] = None
    ftp_credentials: Optional[str] = None
    wp_admin_url: Optional[str] = None
    hosting_notes: Optional[str] = None
    fixed_price: Optional[float] = None
    actual_hours: Optional[float] = None
    hourly_rate: Optional[float] = None
    ai_tool_costs: Optional[float] = None
    margin_percent: Optional[float] = None
    scope_creep_flags: Optional[int] = None
    pagespeed_mobile: Optional[int] = None
    pagespeed_desktop: Optional[int] = None
    analysis_score: Optional[int] = None
    audit_score: Optional[int] = None
    has_logo: Optional[bool] = None
    has_briefing: Optional[bool] = None
    has_photos: Optional[bool] = None
    email_notifications_enabled: Optional[bool] = None
    start_date: datetime = None
    target_go_live: datetime = None
    actual_go_live: datetime = None
    go_live_date: datetime = None
    created_at: datetime = None

    class Config:
        from_attributes = True


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
    customer_name: str = None
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
    wz_code: str = None
    wz_title: str = None
    email_notifications_enabled: bool = None
    customer_email: str = None
    fixed_price: float = None
    target_go_live: str = None
    status: str = None
    current_phase: int = None
    hosting_provider: str = None
    domain_registrar: str = None
    nameserver1: str = None
    nameserver2: str = None
    ftp_credentials: str = None
    wp_admin_url: str = None
    hosting_notes: str = None


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
    current_user=Depends(get_current_user),
):
    # Kunden sehen nur ihre eigenen Projekte
    customer_filter = ""
    params = {"limit": limit, "skip": skip}
    if current_user.role == "kunde":
        customer_filter = "WHERE lead_id = :lead_id "
        params["lead_id"] = current_user.lead_id
        if status:
            customer_filter += "AND status = :status "
            params["status"] = status
    elif status:
        customer_filter = "WHERE status = :status "
        params["status"] = status

    try:
        rows = db.execute(
            text(
                "SELECT id, lead_id, status, fixed_price, actual_hours, hourly_rate, "
                "ai_tool_costs, margin_percent, scope_creep_flags, created_at, "
                "company_name, website_url, contact_name "
                "FROM projects "
                + customer_filter
                + "ORDER BY id DESC LIMIT :limit OFFSET :skip"
            ),
            params,
        ).fetchall()
    except Exception as e:
        logger.error(f"list_projects query error: {e}")
        return []

    result = []
    for row in rows:
        try:
            lead_id = row[1]
            lead = db.query(Lead).filter(Lead.id == lead_id).first() if lead_id else None
            company = row[10] or (lead.company_name if lead else '') or ''
            website = row[11] or (lead.website_url if lead else '') or ''
            result.append({
                'id': row[0],
                'lead_id': lead_id,
                'name': f"Website – {company}" if company else f"Projekt #{row[0]}",
                'customer_name': company,
                'status': row[2] or 'phase_1',
                'current_phase': 1,
                'website_url': website,
                'fixed_price': row[3] or 2000,
                'actual_hours': row[4] or 0,
                'hourly_rate': row[5] or 45,
                'ai_tool_costs': row[6] or 50,
                'margin_percent': row[7] or 0,
                'scope_creep_flags': row[8] or 0,
                'created_at': str(row[9])[:10] if row[9] else '',
            })
        except Exception:
            continue
    return result


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get project detail via raw SQL — bypasses ORM column mapping issues."""
    try:
        row = db.execute(
            text(
                "SELECT id, lead_id, status, fixed_price, actual_hours, hourly_rate, "
                "ai_tool_costs, margin_percent, scope_creep_flags, start_date, "
                "target_go_live, created_at, company_name, website_url, contact_name, "
                "sitemap_json, sitemap_freigabe, content_freigaben, qa_checklist_json, "
                "abnahme_datum, abnahme_durch, "
                "pagespeed_after_mobile, pagespeed_after_desktop, screenshot_after, "
                "gbp_checklist_json "
                "FROM projects WHERE id = :pid"
            ),
            {"pid": project_id},
        ).fetchone()
    except Exception as e:
        logger.error(f"get_project query error: {e}")
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    lead_id = row[1]
    # Kunden dürfen nur ihr eigenes Projekt sehen
    if current_user.role == "kunde" and lead_id != current_user.lead_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf dieses Projekt")

    lead = db.query(Lead).filter(Lead.id == lead_id).first() if lead_id else None
    company = row[12] or (lead.company_name if lead else '') or ''
    website = row[13] or (lead.website_url if lead else '') or ''

    return {
        'id': row[0],
        'lead_id': lead_id,
        'name': f"Website – {company}" if company else f"Projekt #{row[0]}",
        'customer_name': company,
        'status': row[2] or 'phase_1',
        'current_phase': 1,
        'website_url': website,
        'fixed_price': row[3] or 2000,
        'actual_hours': row[4] or 0,
        'hourly_rate': row[5] or 45,
        'ai_tool_costs': row[6] or 50,
        'margin_percent': row[7] or 0,
        'scope_creep_flags': row[8] or 0,
        'start_date': str(row[9])[:10] if row[9] else '',
        'target_go_live': str(row[10])[:10] if row[10] else '',
        'created_at': str(row[11])[:10] if row[11] else '',
        'company_name': company,
        'contact_name': row[14] or (lead.contact_name if lead else '') or '',
        'email': lead.email if lead else '',
        'phone': lead.phone if lead else '',
        'city': lead.city if lead else '',
        'trade': lead.trade if lead else '',
        'sitemap_json':             row[15],
        'sitemap_freigabe':         str(row[16])[:16] if row[16] else None,
        'content_freigaben':        row[17],
        'qa_checklist_json':        row[18],
        'abnahme_datum':            str(row[19])[:16] if row[19] else None,
        'abnahme_durch':            row[20],
        'pagespeed_after_mobile':   row[21],
        'pagespeed_after_desktop':  row[22],
        'screenshot_after':         row[23],
        # Lead-seitige PageSpeed-Werte (Vorher)
        'pagespeed_mobile':         getattr(lead, 'pagespeed_mobile_score', None),
        'pagespeed_desktop':        getattr(lead, 'pagespeed_desktop_score', None),
        'screenshot_before':        getattr(lead, 'website_screenshot', None),
        # Lead-seitige GBP-Daten
        'gbp_place_id':             getattr(lead, 'gbp_place_id', None),
        'gbp_rating':               getattr(lead, 'gbp_rating', None),
        'gbp_ratings_total':        getattr(lead, 'gbp_ratings_total', None),
        'gbp_checklist_json':       row[24],
    }


BLOCKED_KEYS = {
    "id", "pid", "project_id", "projects_id",
    "created_at", "updated_at", "lead_id"
}


@router.put("/{project_id}")
def update_project(
    project_id: int,
    body: dict,
    db: Session = Depends(get_db),
):
    """Update project fields via raw SQL — avoids ORM column-mapping issues."""
    from sqlalchemy import text as _text

    existing = db.execute(
        _text("SELECT id, status FROM projects WHERE id = :id"),
        {"id": project_id}
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    old_status = existing[1]

    # Filtere: keine gesperrten Keys, keine None, keine leeren Strings
    data = {
        k: v for k, v in body.items()
        if k not in BLOCKED_KEYS
        and v is not None
        and v != ""
        and v != []
    }

    if not data:
        row = db.execute(
            _text("SELECT * FROM projects WHERE id = :id"),
            {"id": project_id}
        ).fetchone()
        return dict(row._mapping) if row else {"success": True}

    # updated_at automatisch setzen
    data["updated_at"] = datetime.utcnow()
    data["pid"] = project_id

    sets = ", ".join(f"{k} = :{k}" for k in data if k != "pid")
    db.execute(_text(f"UPDATE projects SET {sets} WHERE id = :pid"), data)
    db.commit()

    # Go-Live Trigger
    new_status = data.get("status", old_status)
    if new_status != old_status and new_status in _GOLIVE_STATUSES:
        def _run():
            import asyncio
            asyncio.run(_golive_automation(project_id))
        threading.Thread(target=_run, daemon=True).start()

    row = db.execute(
        _text("SELECT * FROM projects WHERE id = :id"),
        {"id": project_id}
    ).fetchone()
    return dict(row._mapping) if row else {"success": True}


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

    # ── Go-Live Trigger ──────────────────────────────────────
    new_status = change_request.new_status
    is_golive  = new_status in _GOLIVE_STATUSES
    if is_golive:
        def _run_automation():
            import asyncio
            asyncio.run(_golive_automation(project_id))
        t = threading.Thread(target=_run_automation, daemon=True)
        t.start()
        logger.info(f"Go-Live: Automatisierung gestartet ({project_id})")

    # ── Kunden-E-Mail bei Phasenwechsel ──────────────────────
    try:
        phase_nr = int("".join(c for c in str(new_status) if c.isdigit()) or "0")
        if phase_nr and project.lead and project.lead.email:
            from services.email import send_email
            from services.email_templates import PHASE_NAMES, render
            phase_name, phase_desc = PHASE_NAMES.get(phase_nr, (f"Phase {phase_nr}", ""))
            portal = os.getenv(
                "FRONTEND_URL",
                "https://kompagnon-frontend.onrender.com"
            ) + "/portal/login"
            rendered = render("phase_change", {
                "firma":              project.lead.company_name or "dort",
                "phase_nr":           phase_nr,
                "phase_name":         phase_name,
                "phase_beschreibung": phase_desc,
                "portal_url":         portal,
            })
            threading.Thread(
                target=send_email,
                args=(project.lead.email, rendered["subject"], rendered["html"]),
                daemon=True,
            ).start()
    except Exception as e:
        logger.warning(f"Phasenwechsel-E-Mail Fehler: {e}")

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


class ApprovalRequest(BaseModel):
    topic: str
    notes: str = ""


@router.post("/{project_id}/request-approval")
def request_approval(
    project_id: int,
    body: ApprovalRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Admin: send a approval-request e-mail to the customer."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    notifications_on = getattr(project, "email_notifications_enabled", True)
    to_email = getattr(project, "customer_email", None) or ""

    if not notifications_on or not to_email:
        return {"success": False, "message": "Keine E-Mail hinterlegt"}

    company = getattr(project, "company_name", "") or f"Projekt #{project_id}"
    try:
        send_approval_request_email(
            to=to_email,
            company=company,
            topic=body.topic,
            notes=body.notes,
        )
    except Exception as exc:
        logger.warning(f"Freigabe-E-Mail fehlgeschlagen für Projekt {project_id}: {exc}")
        return {"success": False, "message": f"E-Mail-Versand fehlgeschlagen: {exc}"}

    return {"success": True, "message": "Freigabe-E-Mail gesendet"}


# ── Go-Live Automation ────────────────────────────────────────────────────────

_GOLIVE_STATUSES = {"phase_6", "6", 6, "go_live", "live", "golive", "phase6"}


async def _golive_automation(project_id: int):
    """
    Läuft im Hintergrund nach Phase-6-Wechsel.
    Macht: Screenshot, PageSpeed, Audit, E-Mail.
    Kein raise — Fehler werden nur geloggt.
    """
    try:
        from database import SessionLocal
        db = SessionLocal()
        try:
            project = db.query(Project).filter(
                Project.id == project_id
            ).first()
            if not project:
                return

            # Website-URL ermitteln
            website_url = getattr(project, 'website_url', None)
            if not website_url and project.lead:
                website_url = project.lead.website_url
            if not website_url:
                logger.warning(f"Go-Live: Keine URL für Projekt {project_id}")
                return

            company = getattr(project, 'customer_name', None) or \
                      (project.lead.company_name if project.lead else 'Ihr Betrieb')
            customer_email = getattr(project, 'customer_email', None) or \
                             (project.lead.email if project.lead else None)

            # ── 1. GO-LIVE DATUM SETZEN ──────────────────────
            project.actual_go_live = datetime.utcnow()
            db.commit()
            logger.info(f"Go-Live: Datum gesetzt für Projekt {project_id}")

            # ── 2. NACHHER-SCREENSHOT ────────────────────────
            try:
                from services.screenshot import capture_screenshot
                screenshot_b64 = await capture_screenshot(website_url)
                if screenshot_b64:
                    project.screenshot_after = screenshot_b64
                    project.screenshot_after_date = datetime.utcnow()
                    db.commit()
                    logger.info(f"Go-Live: Screenshot gespeichert ({project_id})")
            except Exception as e:
                logger.warning(f"Go-Live: Screenshot Fehler: {e}")

            # ── 3. NACHHER-PAGESPEED ─────────────────────────
            try:
                import httpx
                api_key = os.getenv("GOOGLE_PAGESPEED_API_KEY", "")

                async def _ps(strategy):
                    url = (
                        "https://www.googleapis.com/pagespeedonline"
                        f"/v5/runPagespeed?url={website_url}"
                        f"&strategy={strategy}"
                        + (f"&key={api_key}" if api_key else "")
                    )
                    async with httpx.AsyncClient(timeout=20.0) as c:
                        r = await c.get(url)
                        score = r.json().get("lighthouseResult", {}) \
                                       .get("categories", {}) \
                                       .get("performance", {}) \
                                       .get("score", 0)
                        return int((score or 0) * 100)

                mobile  = await _ps("mobile")
                desktop = await _ps("desktop")
                project.pagespeed_after_mobile  = mobile
                project.pagespeed_after_desktop = desktop
                db.commit()
                logger.info(
                    f"Go-Live: PageSpeed Mobile={mobile} "
                    f"Desktop={desktop} für Projekt {project_id}"
                )
            except Exception as e:
                logger.warning(f"Go-Live: PageSpeed Fehler: {e}")

            # ── 4. HOMEPAGE-STANDARD-AUDIT ───────────────────
            try:
                lead_id = project.lead_id
                if lead_id:
                    import httpx as _httpx
                    backend_url = os.getenv(
                        "BACKEND_URL",
                        "http://localhost:8000"
                    )
                    async with _httpx.AsyncClient(timeout=5.0) as c:
                        resp = await c.post(
                            f"{backend_url}/api/audit/start",
                            json={"lead_id": lead_id},
                            headers={"Content-Type": "application/json"},
                        )
                    if resp.status_code in (200, 201, 202):
                        logger.info(
                            f"Go-Live: Audit gestartet für Lead {lead_id}"
                        )
                    else:
                        logger.warning(
                            f"Go-Live: Audit HTTP {resp.status_code}"
                        )
            except Exception as e:
                logger.warning(f"Go-Live: Audit Fehler: {e}")

            # ── 5. GO-LIVE E-MAIL ────────────────────────────
            if customer_email:
                try:
                    from services.email import send_email
                    portal_url = os.getenv(
                        "FRONTEND_URL",
                        "https://kompagnon-frontend.onrender.com"
                    ) + "/portal/login"

                    ps_mobile  = getattr(project, 'pagespeed_after_mobile', None)
                    ps_desktop = getattr(project, 'pagespeed_after_desktop', None)

                    ps_abschnitt = ""
                    if ps_mobile or ps_desktop:
                        def ps_farbe(score):
                            if not score: return "#94a3b8"
                            if score >= 90: return "#1D9E75"
                            if score >= 50: return "#BA7517"
                            return "#E24B4A"

                        ps_abschnitt = f"""
                        <div style="background:#f8f9fa;border-radius:8px;
                                    padding:14px 18px;margin:16px 0">
                          <div style="font-size:11px;font-weight:600;
                                      color:#64748b;text-transform:uppercase;
                                      letter-spacing:0.06em;margin-bottom:10px">
                            Ihr Website-Score
                          </div>
                          <div style="display:flex;gap:20px">
                            <div style="text-align:center">
                              <div style="font-size:28px;font-weight:700;
                                          color:{ps_farbe(ps_mobile)}">
                                {ps_mobile or '—'}
                              </div>
                              <div style="font-size:11px;color:#94a3b8">
                                Mobil
                              </div>
                            </div>
                            <div style="text-align:center">
                              <div style="font-size:28px;font-weight:700;
                                          color:{ps_farbe(ps_desktop)}">
                                {ps_desktop or '—'}
                              </div>
                              <div style="font-size:11px;color:#94a3b8">
                                Desktop
                              </div>
                            </div>
                          </div>
                        </div>
                        """

                    html = f"""
                    <div style="font-family:Arial,sans-serif;
                                max-width:600px;margin:0 auto">
                      <div style="background:#1D9E75;padding:28px;
                                  text-align:center;
                                  border-radius:12px 12px 0 0">
                        <div style="font-size:44px;margin-bottom:8px">🚀</div>
                        <h1 style="color:white;margin:0;font-size:22px">
                          Ihre Website ist jetzt live!
                        </h1>
                      </div>
                      <div style="padding:28px 32px;background:#ffffff">
                        <p style="font-size:15px;color:#1a2332;margin-top:0">
                          Herzlichen Glückwunsch, {company}!
                        </p>
                        <p style="color:#64748b;line-height:1.7;font-size:13px">
                          Ihre neue Website ist ab sofort online erreichbar.
                          Wir haben sie nach unserem Homepage Standard 2025
                          geprüft und optimiert.
                        </p>

                        <div style="background:#F0FDF4;
                                    border:1.5px solid #BBF7D0;
                                    border-radius:8px;padding:14px 18px;
                                    margin:16px 0">
                          <div style="font-size:11px;font-weight:600;
                                      color:#166534;margin-bottom:6px">
                            IHRE NEUE WEBSITE
                          </div>
                          <a href="{website_url}"
                             style="color:#008eaa;font-size:16px;
                                    font-weight:600;text-decoration:none">
                            {website_url}
                          </a>
                        </div>

                        {ps_abschnitt}

                        <h3 style="color:#1a2332;font-size:14px;
                                   margin:20px 0 10px">
                          Was jetzt passiert:
                        </h3>
                        <table style="width:100%">
                          <tr>
                            <td style="padding:5px 0;vertical-align:top;
                                       width:20px;color:#1D9E75">✓</td>
                            <td style="padding:5px 0;font-size:12px;
                                       color:#64748b">
                              Google meldet Ihre Website in 1–3 Tagen
                              als indexiert
                            </td>
                          </tr>
                          <tr>
                            <td style="padding:5px 0;vertical-align:top;
                                       color:#1D9E75">✓</td>
                            <td style="padding:5px 0;font-size:12px;
                                       color:#64748b">
                              Wir begleiten Sie noch 30 Tage im
                              Post-Launch
                            </td>
                          </tr>
                          <tr>
                            <td style="padding:5px 0;vertical-align:top;
                                       color:#1D9E75">✓</td>
                            <td style="padding:5px 0;font-size:12px;
                                       color:#64748b">
                              Ihr Homepage-Audit-Report folgt per E-Mail
                            </td>
                          </tr>
                        </table>

                        <div style="text-align:center;margin-top:24px">
                          <a href="{portal_url}"
                             style="display:inline-block;
                                    background:#008eaa;color:white;
                                    padding:13px 28px;border-radius:8px;
                                    text-decoration:none;font-weight:600;
                                    font-size:14px">
                            Zum Kundenportal →
                          </a>
                        </div>

                        <p style="color:#94a3b8;font-size:11px;
                                  margin-top:20px">
                          Fragen?
                          <a href="mailto:info@kompagnon.eu"
                             style="color:#008eaa">
                            info@kompagnon.eu
                          </a>
                        </p>
                      </div>
                      <div style="padding:14px;background:#f8f9fa;
                                  text-align:center;
                                  border-radius:0 0 12px 12px">
                        <p style="color:#94a3b8;font-size:11px;margin:0">
                          KOMPAGNON Communications BP GmbH
                          &bull; kompagnon.eu
                        </p>
                      </div>
                    </div>
                    """

                    send_email(
                        to_email  = customer_email,
                        subject   = f"🚀 Ihre Website ist live — {company}",
                        html_body = html,
                    )
                    logger.info(
                        f"Go-Live: E-Mail gesendet an {customer_email}"
                    )
                except Exception as e:
                    logger.error(f"Go-Live: E-Mail Fehler: {e}")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Go-Live Automation Fehler: {e}")


@router.post("/from-lead/{lead_id}", status_code=201)
def create_project_from_lead(lead_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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

    # 3b. Auto-start content scrape if website_url is present
    if lead.website_url:
        try:
            scrape_job = ProjectScrapeJob(project_id=project.id, status="pending")
            db.add(scrape_job)
            db.commit()
            db.refresh(scrape_job)
            background_tasks.add_task(_run_content_scrape, scrape_job.id, project.id, lead.website_url)
        except Exception as exc:
            logger.warning("Could not start auto-scrape for project %s: %s", project.id, exc)

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


@router.post("/{project_id}/scrape")
async def scrape_project_website(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Scrapt die Website des Projekts und extrahiert Branddesign-Daten."""
    import httpx, re, json
    from datetime import datetime as dt

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    lead = project.lead
    if not lead or not lead.website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")

    url = lead.website_url
    if not url.startswith("http"):
        url = "https://" + url

    try:
        async with httpx.AsyncClient(timeout=15.0, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }) as client:
            resp = await client.get(url, follow_redirects=True)

        html = resp.text

        hex_colors = list(set(re.findall(r'#([0-9a-fA-F]{6})\b', html)))[:15]
        fonts = list(set(re.findall(r"font-family:\s*['\"]?([^;'\"{}]+)", html)))[:5]
        logo_match = re.search(r'<img[^>]+(logo)[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
        logo_url = logo_match.group(2) if logo_match else None

        primary = ('#' + hex_colors[0]) if hex_colors else None
        secondary = ('#' + hex_colors[1]) if len(hex_colors) > 1 else None
        font_primary = fonts[0].strip() if fonts else None

        lead.brand_primary_color = primary
        lead.brand_secondary_color = secondary
        lead.brand_font_primary = font_primary
        lead.brand_logo_url = logo_url
        lead.brand_colors = json.dumps(['#' + c for c in hex_colors])
        lead.brand_fonts = json.dumps(fonts)
        lead.brand_scrape_failed = False
        lead.brand_scraped_at = dt.utcnow()
        db.commit()

        return {
            "success": True,
            "primary_color": primary,
            "secondary_color": secondary,
            "font_primary": font_primary,
            "logo_url": logo_url,
            "all_colors": ['#' + c for c in hex_colors],
            "all_fonts": fonts,
            "scrape_failed": False,
            "scraped_at": dt.utcnow().isoformat(),
        }

    except Exception as e:
        lead.brand_scrape_failed = True
        db.commit()
        return {
            "success": False,
            "scrape_failed": True,
            "error": str(e),
            "message": "Website konnte nicht gescrapt werden",
        }


@router.post("/{project_id}/hosting-scan")
async def hosting_scan(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Scannt Hosting, DNS, WHOIS und WordPress-Erkennung für das Projekt."""
    from services.hosting_scraper import scrape_hosting_info

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    website_url = getattr(project, "website_url", None)
    if not website_url:
        return {"error": "Keine Website-URL im Projekt hinterlegt"}

    if not website_url.startswith("http"):
        website_url = "https://" + website_url

    data = await scrape_hosting_info(website_url)

    db.execute(text("""
        UPDATE projects SET
            hosting_provider    = :hosting_provider,
            hosting_org         = :hosting_org,
            hosting_ip          = :hosting_ip,
            hosting_country     = :hosting_country,
            dns_provider        = :dns_provider,
            nameservers         = :nameservers,
            domain_registrar    = :domain_registrar,
            domain_created      = :domain_created,
            domain_expires      = :domain_expires,
            server_software     = :server_software,
            wordpress_hosting        = :wordpress_hosting,
            is_wordpress             = :is_wordpress,
            detected_technologies    = :detected_technologies,
            hosting_checked_at       = NOW()
        WHERE id = :project_id
    """), {
        "project_id":            project_id,
        "hosting_provider":      data.get("hosting_provider"),
        "hosting_org":           data.get("hosting_org"),
        "hosting_ip":            data.get("ip_address"),
        "hosting_country":       data.get("country"),
        "dns_provider":          data.get("dns_provider"),
        "nameservers":           ",".join(data.get("nameservers") or []) or None,
        "domain_registrar":      data.get("registrar"),
        "domain_created":        data.get("domain_created"),
        "domain_expires":        data.get("domain_expires"),
        "server_software":       data.get("server_software"),
        "wordpress_hosting":     data.get("wordpress_hosting"),
        "is_wordpress":          data.get("is_wordpress"),
        "detected_technologies": ",".join(data.get("detected_technologies") or []) or None,
    })
    db.commit()

    from datetime import datetime
    return {
        "hosting_provider":      data.get("hosting_provider"),
        "hosting_org":           data.get("hosting_org"),
        "hosting_ip":            data.get("ip_address"),
        "hosting_country":       data.get("country"),
        "dns_provider":          data.get("dns_provider"),
        "nameservers":           ",".join(data.get("nameservers") or []) or None,
        "domain_registrar":      data.get("registrar"),
        "domain_created":        data.get("domain_created"),
        "domain_expires":        data.get("domain_expires"),
        "server_software":       data.get("server_software"),
        "wordpress_hosting":     data.get("wordpress_hosting"),
        "is_wordpress":          data.get("is_wordpress"),
        "detected_technologies": ",".join(data.get("detected_technologies") or []) or None,
        "hosting_checked_at":    datetime.utcnow().isoformat(),
        "website_url":           website_url,
    }


# ── Screenshots ──────────────────────────────────────────────────────────────

async def _capture_project_screenshot_after(project_id: int):
    """Background-Hilfsfunktion: After-Screenshot aufnehmen und speichern."""
    from database import SessionLocal
    from services.screenshot import capture_screenshot
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        url = getattr(project, "new_website_url", None) or project.website_url
        if not url:
            return
        b64 = await capture_screenshot(url)
        if b64:
            project.screenshot_after      = b64
            project.screenshot_after_date = datetime.utcnow()
            project.screenshot_url_after  = url
            db.commit()
            logger.info(f"✓ After-Screenshot für Projekt {project_id} gespeichert")
    except Exception as e:
        logger.warning(f"After-Screenshot Fehler (Projekt {project_id}): {e}")
    finally:
        db.close()


@router.post("/{project_id}/screenshot/before")
async def screenshot_before(
    project_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Nimmt einen Before-Screenshot der alten Website auf."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    if not project.website_url:
        raise HTTPException(status_code=400, detail="Keine website_url am Projekt hinterlegt")

    from services.screenshot import capture_screenshot
    b64 = await capture_screenshot(project.website_url)
    if not b64:
        raise HTTPException(status_code=502, detail="Screenshot konnte nicht erstellt werden")

    project.screenshot_before      = b64
    project.screenshot_before_date = datetime.utcnow()
    project.screenshot_url_before  = project.website_url
    db.commit()

    return {"success": True, "screenshot_url": f"data:image/jpeg;base64,{b64}"}


@router.post("/{project_id}/screenshot/after")
async def screenshot_after(
    project_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Nimmt einen After-Screenshot der neuen Website auf."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    url = getattr(project, "new_website_url", None) or project.website_url
    if not url:
        raise HTTPException(status_code=400, detail="Keine URL am Projekt hinterlegt")

    from services.screenshot import capture_screenshot
    b64 = await capture_screenshot(url)
    if not b64:
        raise HTTPException(status_code=502, detail="Screenshot konnte nicht erstellt werden")

    project.screenshot_after      = b64
    project.screenshot_after_date = datetime.utcnow()
    project.screenshot_url_after  = url
    db.commit()

    return {"success": True, "screenshot_url": f"data:image/jpeg;base64,{b64}"}


@router.get("/{project_id}/screenshots")
def get_screenshots(
    project_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Gibt gespeicherte Before/After-Screenshots zurück."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    return {
        "before": {
            "data":  f"data:image/jpeg;base64,{project.screenshot_before}" if project.screenshot_before else None,
            "date":  project.screenshot_before_date.isoformat() if project.screenshot_before_date else None,
            "url":   project.screenshot_url_before,
        },
        "after": {
            "data":  f"data:image/jpeg;base64,{project.screenshot_after}" if project.screenshot_after else None,
            "date":  project.screenshot_after_date.isoformat() if project.screenshot_after_date else None,
            "url":   project.screenshot_url_after,
        },
    }


@router.get("/{project_id}/hosting-info")
def hosting_info(
    project_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Gibt gespeicherte Hosting-Infos des Projekts zurück (kein neuer Scan)."""
    row = db.execute(text("""
        SELECT hosting_provider, hosting_org, hosting_ip, hosting_country,
               dns_provider, nameservers, domain_registrar, domain_created,
               domain_expires, server_software, wordpress_hosting, is_wordpress,
               detected_technologies, hosting_checked_at, website_url
        FROM projects WHERE id = :id
    """), {"id": project_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    return dict(row)



@router.post("/{project_id}/domain-check")
async def domain_check_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Prüft DNS, WHOIS und SSL für die Website-URL des Projekts."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead = project.lead
    website_url = getattr(project, "website_url", None) or (lead.website_url if lead else None)
    if not website_url:
        raise HTTPException(400, "Keine Website-URL hinterlegt")

    url = website_url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    from urllib.parse import urlparse
    import socket
    import ssl
    import datetime as dt

    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path

    result = {
        "domain": domain,
        "url": url,
        "dns": None,
        "ssl": None,
        "ssl_expiry": None,
        "ssl_days_remaining": None,
        "reachable": False,
        "status_code": None,
        "redirect_url": None,
        "error": None,
    }

    # DNS check
    try:
        ip = socket.gethostbyname(domain)
        result["dns"] = ip
    except Exception as e:
        result["error"] = f"DNS-Fehler: {str(e)}"
        return result

    # Reachability check
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)
            result["reachable"] = True
            result["status_code"] = resp.status_code
            if str(resp.url) != url:
                result["redirect_url"] = str(resp.url)
    except Exception as e:
        result["error"] = f"Erreichbarkeit: {str(e)}"

    # SSL cert expiry
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(5)
            s.connect((domain, 443))
            cert = s.getpeercert()
            expiry_str = cert.get("notAfter", "")
            if expiry_str:
                expiry = dt.datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
                days = (expiry - dt.datetime.utcnow()).days
                result["ssl"] = "valid"
                result["ssl_expiry"] = expiry.strftime("%d.%m.%Y")
                result["ssl_days_remaining"] = days
    except Exception:
        result["ssl"] = "none_or_error"

    # Persist reachability to project
    try:
        project.domain_reachable   = result["reachable"]
        project.domain_status_code = result.get("status_code")
        project.domain_checked_at  = datetime.utcnow()
        db.commit()
    except Exception:
        pass

    return result


@router.post("/{project_id}/screenshot/before")
async def screenshot_before(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    lead = project.lead
    if not lead or not lead.website_url:
        raise HTTPException(400, "Keine Website-URL beim verknüpften Lead hinterlegt")
    url = lead.website_url
    if not url.startswith("http"):
        url = "https://" + url
    from services.screenshot import capture_screenshot
    screenshot_b64 = await capture_screenshot(url)
    if not screenshot_b64:
        raise HTTPException(500, "Screenshot konnte nicht erstellt werden")
    db.execute(
        text("UPDATE projects SET screenshot_before = :s, screenshot_before_date = :d WHERE id = :id"),
        {"s": screenshot_b64, "d": datetime.utcnow(), "id": project_id},
    )
    db.commit()
    return {
        "success": True,
        "screenshot_url": f"data:image/jpeg;base64,{screenshot_b64}",
        "type": "before",
    }


@router.post("/{project_id}/screenshot/after")
async def screenshot_after(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    lead = project.lead
    if not lead or not lead.website_url:
        raise HTTPException(400, "Keine Website-URL beim verknüpften Lead hinterlegt")
    url = lead.website_url
    if not url.startswith("http"):
        url = "https://" + url
    from services.screenshot import capture_screenshot
    screenshot_b64 = await capture_screenshot(url)
    if not screenshot_b64:
        raise HTTPException(500, "Screenshot konnte nicht erstellt werden")
    db.execute(
        text("UPDATE projects SET screenshot_after = :s, screenshot_after_date = :d WHERE id = :id"),
        {"s": screenshot_b64, "d": datetime.utcnow(), "id": project_id},
    )
    db.commit()
    return {
        "success": True,
        "screenshot_url": f"data:image/jpeg;base64,{screenshot_b64}",
        "type": "after",
    }


@router.get("/{project_id}/screenshots")
def get_screenshots(project_id: int, db: Session = Depends(get_db)):
    row = db.execute(
        text(
            "SELECT screenshot_before, screenshot_after, screenshot_before_date, screenshot_after_date "
            "FROM projects WHERE id = :id"
        ),
        {"id": project_id},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Projekt nicht gefunden")
    return {
        "before": {"data": f"data:image/jpeg;base64,{row[0]}" if row[0] else None, "date": row[2].isoformat() if row[2] else None, "url": None},
        "after":  {"data": f"data:image/jpeg;base64,{row[1]}" if row[1] else None, "date": row[3].isoformat() if row[3] else None, "url": None},
    }


# ── Netlify-Integration ───────────────────────────────────────────────────────

class NetlifyDeployRequest(BaseModel):
    html:      str
    css:       str = ""
    redirects: str = ""

class NetlifyDomainRequest(BaseModel):
    domain: str


@router.post("/{project_id}/netlify/create-site")
async def netlify_create_site(
    project_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Erstellt eine neue Netlify-Site für das Projekt (nur Admin)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    existing = db.execute(
        text("SELECT netlify_site_id FROM projects WHERE id = :id"),
        {"id": project_id},
    ).scalar()
    if existing:
        raise HTTPException(409, f"Netlify-Site bereits vorhanden: {existing}")

    lead = project.lead
    company = (
        getattr(project, "company_name", None)
        or (lead.company_name if lead else None)
        or f"projekt-{project_id}"
    )

    from services.netlify_service import create_site
    result = await create_site(company)

    db.execute(
        text(
            "UPDATE projects SET netlify_site_id = :sid, netlify_site_url = :url "
            "WHERE id = :id"
        ),
        {"sid": result["site_id"], "url": result["site_url"], "id": project_id},
    )
    db.commit()
    return {"site_id": result["site_id"], "site_url": result["site_url"]}


@router.post("/{project_id}/netlify/deploy")
async def netlify_deploy(
    project_id: int,
    body: NetlifyDeployRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Deployt HTML auf die Netlify-Site des Projekts (nur Admin)."""
    row = db.execute(
        text("SELECT netlify_site_id FROM projects WHERE id = :id"),
        {"id": project_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(400, "Keine Netlify-Site vorhanden. Zuerst Site anlegen.")

    site_id = row[0]
    from services.netlify_service import deploy_html
    result = await deploy_html(site_id, body.html, body.css, body.redirects)

    db.execute(
        text(
            "UPDATE projects SET netlify_deploy_id = :did, netlify_last_deploy = :ts "
            "WHERE id = :id"
        ),
        {"did": result["deploy_id"], "ts": datetime.utcnow(), "id": project_id},
    )
    db.commit()
    return {
        "deploy_id":  result["deploy_id"],
        "deploy_url": result["deploy_url"],
        "state":      result["state"],
    }


@router.post("/{project_id}/netlify/set-domain")
async def netlify_set_domain(
    project_id: int,
    body: NetlifyDomainRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Setzt eine Custom-Domain auf der Netlify-Site (nur Admin)."""
    row = db.execute(
        text("SELECT netlify_site_id FROM projects WHERE id = :id"),
        {"id": project_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(400, "Keine Netlify-Site vorhanden.")

    site_id = row[0]
    from services.netlify_service import set_custom_domain
    result = await set_custom_domain(site_id, body.domain)

    db.execute(
        text(
            "UPDATE projects SET netlify_domain = :domain, netlify_domain_status = 'pending' "
            "WHERE id = :id"
        ),
        {"domain": body.domain, "id": project_id},
    )
    db.commit()
    return {
        "custom_domain":       result["custom_domain"],
        "required_dns_record": result.get("required_dns_record"),
        "cname_target":        f"{body.domain}.netlify.app",
    }


@router.get("/{project_id}/netlify/status")
async def netlify_status(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Ruft den Netlify-Status des Projekts ab."""
    row = db.execute(
        text(
            "SELECT netlify_site_id, netlify_site_url, netlify_deploy_id, "
            "netlify_domain, netlify_domain_status, netlify_ssl_active, netlify_last_deploy "
            "FROM projects WHERE id = :id"
        ),
        {"id": project_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(404, "Keine Netlify-Site für dieses Projekt vorhanden.")

    site_id = row[0]
    from services.netlify_service import get_site_status
    live = await get_site_status(site_id)

    # SSL-Status in DB aktualisieren
    ssl_active = bool(live.get("ssl"))
    db.execute(
        text("UPDATE projects SET netlify_ssl_active = :ssl WHERE id = :id"),
        {"ssl": ssl_active, "id": project_id},
    )
    db.commit()

    return {
        **live,
        "netlify_site_id":       row[0],
        "netlify_site_url":      row[1],
        "netlify_deploy_id":     row[2],
        "netlify_domain":        row[3],
        "netlify_domain_status": row[4],
        "netlify_ssl_active":    ssl_active,
        "netlify_last_deploy":   row[6].isoformat() if row[6] else None,
    }


# ── Scrape Website Content ─────────────────────────────────────────────────────

@router.get("/{project_id}/scrape-content")
def scrape_project_content(project_id: int, db: Session = Depends(get_db)):
    """Fetch and parse the project's website, store clean text in scraped_content."""
    import requests
    from bs4 import BeautifulSoup

    # Ensure columns exist
    db.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS scraped_content TEXT"))
    db.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS scraped_at TIMESTAMP"))
    db.commit()

    # Load project URL
    row = db.execute(
        text("SELECT website_url FROM projects WHERE id = :id"),
        {"id": project_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    website_url = row[0]
    if not website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")

    # Fetch page
    try:
        resp = requests.get(
            website_url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"},
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Website nicht erreichbar: {e}")

    # Parse with BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    parts = []
    for el in soup.find_all(["main", "article", "section", "p", "h1", "h2", "h3", "h4", "h5", "h6"]):
        text_content = el.get_text(separator=" ", strip=True)
        if text_content:
            parts.append(text_content)

    content = "\n\n".join(parts)

    # Persist
    scraped_at = datetime.utcnow()
    db.execute(
        text("UPDATE projects SET scraped_content = :content, scraped_at = :ts WHERE id = :id"),
        {"content": content, "ts": scraped_at, "id": project_id},
    )
    db.commit()

    return {"content": content, "scraped_at": scraped_at.isoformat()}


# ── QA-Scanner Endpunkte ──────────────────────────────────────────────────────

@router.post("/{project_id}/qa/run")
async def run_project_qa(project_id: int, db: Session = Depends(get_db)):
    """Führt vollständigen KI-QA-Scan durch und speichert Ergebnis."""
    from services.qa_scanner import run_full_qa, ai_evaluate_qa
    import json as _json

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    # Website-URL ermitteln
    url = getattr(project, "website_url", None)
    if not url and project.lead:
        url = project.lead.website_url
    if not url:
        raise HTTPException(400, "Keine Website-URL hinterlegt")

    company = getattr(project, "customer_name", None) or \
              (project.lead.company_name if project.lead else "")
    trade = (project.lead.trade if project.lead else "") or ""

    # 1. Automatische Checks
    scan = await run_full_qa(url, company, trade)
    if "error" in scan:
        raise HTTPException(422, f"Website nicht erreichbar: {scan['error']}")

    # 2. KI-Auswertung
    ai = await ai_evaluate_qa(scan)

    # 3. Ergebnis speichern
    full_result = {**scan, "ai": ai, "checks": scan["checks"]}
    full_result.pop("html_snippet", None)  # zu groß für DB

    project.qa_result    = _json.dumps(full_result, ensure_ascii=False)
    project.qa_score     = ai.get("gesamt_score", 0)
    project.qa_golive_ok = ai.get("golive_empfehlung", False)
    project.qa_run_at    = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "score": project.qa_score,
        "golive_ok": project.qa_golive_ok,
        "result": full_result,
    }


@router.get("/{project_id}/qa/result")
def get_qa_result(project_id: int, db: Session = Depends(get_db)):
    """Gibt das zuletzt gespeicherte QA-Ergebnis zurück."""
    import json as _json

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"status": "no_result", "message": "Projekt nicht gefunden"}
    if not project.qa_result:
        return {"status": "no_result", "message": "Noch kein QA-Scan für dieses Projekt"}

    try:
        parsed = _json.loads(project.qa_result)
    except _json.JSONDecodeError as e:
        logger.error(f"QA Result JSON Parse Fehler Projekt {project_id}: {e}")
        logger.error(f"JSON Länge: {len(project.qa_result)}, Ende: ...{project.qa_result[-200:]}")
        return {
            "status": "parse_error",
            "message": f"QA-Ergebnis konnte nicht gelesen werden: {e}",
            "score": project.qa_score,
            "run_at": str(project.qa_run_at)[:16] if project.qa_run_at else None,
        }

    return {
        "score": project.qa_score,
        "golive_ok": project.qa_golive_ok,
        "run_at": str(project.qa_run_at)[:16] if project.qa_run_at else None,
        "result": parsed,
    }


@router.post("/{project_id}/credentials")
def add_credential(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    label    = (data.get("label") or "").strip()
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    url      = (data.get("url") or "").strip()
    notes    = (data.get("notes") or "").strip()

    if not label:
        raise HTTPException(400, "Label ist Pflichtfeld")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    encrypted = ""
    if password:
        try:
            f = _get_fernet()
            encrypted = f.encrypt(password.encode()).decode()
        except RuntimeError as e:
            logger.error(f"CREDENTIALS_KEY Fehler: {e}")
            raise HTTPException(
                status_code=503,
                detail="Zugangsdaten-Safe nicht verfügbar: CREDENTIALS_KEY nicht konfiguriert. Bitte Administrator kontaktieren.",
            )
        except Exception as e:
            logger.error(f"Verschluesselung Fehler: {e}")
            raise HTTPException(500, "Verschluesselung fehlgeschlagen")

    db.execute(text("""
        INSERT INTO project_credentials
            (project_id, label, username, password_encrypted, url, notes)
        VALUES
            (:pid, :label, :username, :pw, :url, :notes)
    """), {
        "pid":      project_id,
        "label":    label,
        "username": username,
        "pw":       encrypted,
        "url":      url,
        "notes":    notes,
    })
    db.commit()

    row = db.execute(text(
        "SELECT id, created_at FROM project_credentials "
        "WHERE project_id=:pid ORDER BY id DESC LIMIT 1"
    ), {"pid": project_id}).fetchone()

    return {
        "success":    True,
        "id":         row[0] if row else None,
        "label":      label,
        "username":   username,
        "url":        url,
        "created_at": str(row[1])[:16] if row else "",
    }


@router.get("/{project_id}/credentials")
def get_credentials(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    rows = db.execute(text("""
        SELECT id, label, username, password_encrypted,
               url, notes, created_at
        FROM project_credentials
        WHERE project_id = :pid
        ORDER BY created_at ASC
    """), {"pid": project_id}).mappings().all()

    try:
        f = _get_fernet()
    except RuntimeError as e:
        logger.error(f"CREDENTIALS_KEY Fehler: {e}")
        raise HTTPException(
            status_code=503,
            detail="Zugangsdaten-Safe nicht verfügbar: CREDENTIALS_KEY nicht konfiguriert. Bitte Administrator kontaktieren.",
        )
    result = []
    for r in rows:
        decrypted = ""
        if r["password_encrypted"]:
            try:
                decrypted = f.decrypt(r["password_encrypted"].encode()).decode()
            except Exception:
                decrypted = "Entschluesselung fehlgeschlagen"
        result.append({
            "id":         r["id"],
            "label":      r["label"],
            "username":   r["username"] or "",
            "password":   decrypted,
            "url":        r["url"] or "",
            "notes":      r["notes"] or "",
            "created_at": str(r["created_at"])[:16],
        })
    return result


@router.delete("/{project_id}/credentials/{cred_id}")
def delete_credential(
    project_id: int,
    cred_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    db.execute(text("""
        DELETE FROM project_credentials
        WHERE id = :cid AND project_id = :pid
    """), {"cid": cred_id, "pid": project_id})
    db.commit()
    return {"success": True}


@router.get("/{project_id}/auftragsbestaetigung")
def download_auftragsbestaetigung(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Lädt die Auftragsbestätigung als PDF herunter (nur Admin)."""
    import os as _os
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    path = getattr(project, "auftragsbestaetigung_pdf", None)
    if not path or not _os.path.exists(path):
        raise HTTPException(404, "PDF nicht vorhanden")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename="KOMPAGNON-Auftragsbestaetigung.pdf",
    )


# ── Sitemap-Planer ────────────────────────────────────────────────────────────

@router.get("/{project_id}/sitemap")
def get_sitemap(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    row = db.execute(
        text("SELECT sitemap_json, sitemap_freigabe FROM projects WHERE id=:id"),
        {"id": project_id},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Projekt nicht gefunden")
    seiten = []
    if row[0]:
        try:
            seiten = json.loads(row[0])
        except Exception:
            seiten = []
    return {
        "seiten":           seiten,
        "sitemap_freigabe": str(row[1])[:16] if row[1] else None,
    }


@router.patch("/{project_id}/sitemap")
def save_sitemap(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    seiten = data.get("seiten", [])
    db.execute(
        text("UPDATE projects SET sitemap_json=:sj WHERE id=:id"),
        {"sj": json.dumps(seiten, ensure_ascii=False), "id": project_id},
    )
    db.commit()
    return {"success": True, "count": len(seiten)}


@router.post("/{project_id}/freigabe")
def request_freigabe(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    from datetime import datetime

    typ    = data.get("typ", "")
    seiten = data.get("seiten", [])
    now    = datetime.utcnow()

    if typ == "sitemap":
        db.execute(
            text("""
                UPDATE projects SET
                  sitemap_json=:sj,
                  sitemap_freigabe=:ts
                WHERE id=:id
            """),
            {
                "sj": json.dumps(seiten, ensure_ascii=False),
                "ts": now,
                "id": project_id,
            },
        )
        db.commit()
        return {
            "success":          True,
            "typ":              "sitemap",
            "sitemap_freigabe": str(now)[:16],
        }

    raise HTTPException(400, f"Unbekannter Freigabe-Typ: {typ}")


# ── Content-Freigaben ─────────────────────────────────────────────────────────

@router.post("/{project_id}/request-approval")
def request_approval(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    from datetime import datetime

    topic    = data.get("topic", "Freigabe erforderlich")
    notes    = data.get("notes", "")
    seite_id = data.get("seite_id")

    row = db.execute(text("""
        SELECT p.id, p.content_freigaben, l.email, l.company_name
        FROM projects p
        LEFT JOIN leads l ON l.id = p.lead_id
        WHERE p.id = :id
    """), {"id": project_id}).fetchone()

    if not row:
        raise HTTPException(404, "Projekt nicht gefunden")

    customer_email = row[2] or ""
    company_name   = row[3] or "Kunde"

    freigaben = {}
    if row[1]:
        try:
            freigaben = json.loads(row[1])
        except Exception:
            freigaben = {}

    now_str = datetime.utcnow().strftime("%d.%m.%Y %H:%M")

    if seite_id:
        freigaben[str(seite_id)] = {
            "status":       "angefragt",
            "angefragt_am": now_str,
            "topic":        topic,
        }

    db.execute(text(
        "UPDATE projects SET content_freigaben=:cf WHERE id=:id"
    ), {"cf": json.dumps(freigaben, ensure_ascii=False), "id": project_id})
    db.commit()

    email_sent = False
    if customer_email:
        try:
            from services.email import send_email
            html = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
              <div style="background:#008eaa;padding:20px 28px;border-radius:12px 12px 0 0">
                <h2 style="color:white;margin:0;font-size:18px">
                  Ihre Freigabe wird ben&#246;tigt
                </h2>
              </div>
              <div style="padding:24px 28px;background:#fff">
                <p style="color:#1a2332">Guten Tag, {company_name},</p>
                <p style="color:#64748b;line-height:1.7">
                  f&#252;r den n&#228;chsten Schritt in Ihrem Projekt ben&#246;tigen wir Ihre Freigabe:
                </p>
                <div style="background:#F8F9FA;border-left:4px solid #008eaa;
                            padding:12px 16px;border-radius:0 8px 8px 0;margin:16px 0">
                  <strong style="color:#1a2332">{topic}</strong>
                  {"<p style='color:#64748b;margin-top:8px;font-size:14px'>" + notes + "</p>" if notes else ""}
                </div>
                <p style="color:#64748b;line-height:1.7">
                  Bitte antworten Sie auf diese E-Mail oder melden Sie sich
                  in Ihrem Kundenportal an, um die Freigabe zu erteilen.
                </p>
              </div>
              <div style="padding:14px 28px;background:#f8f9fa;
                          border-radius:0 0 12px 12px;text-align:center">
                <p style="font-size:11px;color:#94a3b8;margin:0">
                  KOMPAGNON Communications BP GmbH &#183; kompagnon.eu
                </p>
              </div>
            </div>"""
            email_sent = send_email(
                to_email=customer_email,
                subject=f"Freigabe erforderlich: {topic}",
                html_body=html,
            )
        except Exception as e:
            logger.warning(f"Approval-E-Mail Fehler: {e}")

    return {
        "success":        True,
        "seite_id":       seite_id,
        "email_sent":     email_sent,
        "customer_email": customer_email,
        "angefragt_am":   now_str,
        "freigaben":      freigaben,
    }


@router.post("/{project_id}/confirm-approval")
def confirm_approval(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    import json
    from datetime import datetime

    seite_id   = str(data.get("seite_id", ""))
    bestaetigt = data.get("bestaetigt", True)

    row = db.execute(
        text("SELECT content_freigaben FROM projects WHERE id=:id"),
        {"id": project_id},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Nicht gefunden")

    freigaben = {}
    if row[0]:
        try:
            freigaben = json.loads(row[0])
        except Exception:
            freigaben = {}

    now_str = datetime.utcnow().strftime("%d.%m.%Y %H:%M")
    if seite_id in freigaben:
        freigaben[seite_id]["status"]         = "freigegeben" if bestaetigt else "abgelehnt"
        freigaben[seite_id]["freigegeben_am"] = now_str
    else:
        freigaben[seite_id] = {
            "status":         "freigegeben" if bestaetigt else "abgelehnt",
            "freigegeben_am": now_str,
        }

    db.execute(
        text("UPDATE projects SET content_freigaben=:cf WHERE id=:id"),
        {"cf": json.dumps(freigaben, ensure_ascii=False), "id": project_id},
    )
    db.commit()
    return {"success": True, "seite_id": seite_id, "freigaben": freigaben}


# ── QA-Checkliste ─────────────────────────────────────────────────────────────

@router.patch("/{project_id}/qa-checklist")
def save_qa_checklist(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    checked = data.get("checked", {})
    db.execute(
        text("UPDATE projects SET qa_checklist_json=:qj WHERE id=:id"),
        {"qj": json.dumps(checked, ensure_ascii=False), "id": project_id},
    )
    db.commit()
    return {"success": True, "checked_count": len(checked)}


# ── Abnahme & Go-Live Nachher ─────────────────────────────────────────────────

@router.post("/{project_id}/abnahme")
def abnahme_erteilen(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from datetime import datetime as dt

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "Name ist Pflichtfeld")

    now = dt.utcnow()
    db.execute(text("""
        UPDATE projects SET
          abnahme_datum=:ts,
          abnahme_durch=:name,
          actual_go_live=COALESCE(actual_go_live, :ts)
        WHERE id=:id
    """), {"ts": now, "name": name, "id": project_id})
    db.commit()

    now_de = now.strftime("%d.%m.%Y um %H:%M Uhr")
    return {
        "success":       True,
        "abnahme_datum": str(now)[:16],
        "abnahme_durch": name,
        "text":          f"Abgenommen am {now_de} von {name}",
    }


@router.post("/{project_id}/go-live-pagespeed")
async def go_live_pagespeed(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import httpx
    import os
    import asyncio

    row = db.execute(text("""
        SELECT l.website_url FROM projects p
        LEFT JOIN leads l ON l.id = p.lead_id
        WHERE p.id = :id
    """), {"id": project_id}).fetchone()

    if not row or not row[0]:
        raise HTTPException(400, "Keine Website-URL hinterlegt")

    url     = row[0]
    api_key = os.getenv("GOOGLE_PAGESPEED_API_KEY", "")
    base    = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params  = {"url": url}
    if api_key:
        params["key"] = api_key

    mob_score = desk_score = None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            mob, desk = await asyncio.gather(
                client.get(base, params={**params, "strategy": "mobile"}),
                client.get(base, params={**params, "strategy": "desktop"}),
            )

        def sc(r):
            try:
                return round(
                    (r.json()["categories"]["performance"]["score"] or 0) * 100
                )
            except Exception:
                return None

        mob_score  = sc(mob)
        desk_score = sc(desk)
    except Exception as e:
        logger.warning(f"Go-Live PageSpeed Fehler: {e}")

    screenshot_after = None
    try:
        from services.screenshot import capture_screenshot
        screenshot_after = await capture_screenshot(url)
    except Exception as e:
        logger.warning(f"Go-Live Screenshot Fehler: {e}")

    db.execute(text("""
        UPDATE projects SET
          pagespeed_after_mobile=:mob,
          pagespeed_after_desktop=:desk,
          screenshot_after=:sc
        WHERE id=:id
    """), {
        "mob":  mob_score,
        "desk": desk_score,
        "sc":   screenshot_after,
        "id":   project_id,
    })
    db.commit()

    return {
        "success":                 True,
        "pagespeed_after_mobile":  mob_score,
        "pagespeed_after_desktop": desk_score,
        "has_screenshot":          bool(screenshot_after),
    }


# ── Bewertungs-QR-Code & GBP-Checkliste ──────────────────────────────────────

@router.get("/{project_id}/bewertungs-qrcode")
def get_bewertungs_qrcode(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from fastapi.responses import Response
    import io

    row = db.execute(text("""
        SELECT l.gbp_place_id, l.company_name
        FROM projects p
        LEFT JOIN leads l ON l.id = p.lead_id
        WHERE p.id = :id
    """), {"id": project_id}).fetchone()

    if not row:
        raise HTTPException(404, "Projekt nicht gefunden")

    place_id = row[0]
    if not place_id:
        raise HTTPException(
            422,
            "Kein Google Business Profil verknüpft. "
            "Bitte zuerst GBP-Check in der Nutzerkartei durchführen.",
        )

    review_url = f"https://search.google.com/local/writereview?placeid={place_id}"

    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=3,
    )
    qr.add_data(review_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0F1E3A", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return Response(
        content=buf.read(),
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="bewertungs-qr-{project_id}.png"',
            "X-Review-URL": review_url,
        },
    )


@router.get("/{project_id}/bewertungs-url")
def get_bewertungs_url(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.execute(text("""
        SELECT l.gbp_place_id, l.gbp_rating, l.gbp_ratings_total,
               l.company_name
        FROM projects p
        LEFT JOIN leads l ON l.id = p.lead_id
        WHERE p.id = :id
    """), {"id": project_id}).fetchone()

    if not row:
        raise HTTPException(404, "Nicht gefunden")

    place_id = row[0]
    if not place_id:
        return {"available": False, "review_url": None, "place_id": None}

    return {
        "available":     True,
        "review_url":    f"https://search.google.com/local/writereview?placeid={place_id}",
        "place_id":      place_id,
        "rating":        row[1],
        "ratings_total": row[2],
        "company_name":  row[3],
    }


@router.patch("/{project_id}/gbp-checklist")
def save_gbp_checklist(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    checked = data.get("checked", {})
    db.execute(
        text("UPDATE projects SET gbp_checklist_json=:gj WHERE id=:id"),
        {"gj": json.dumps(checked, ensure_ascii=False), "id": project_id},
    )
    db.commit()
    return {"success": True}
