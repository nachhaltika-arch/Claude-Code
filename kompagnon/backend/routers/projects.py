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
import json as _json_mod
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

logger = logging.getLogger(__name__)


def safe_json_parse(raw, default=None):
    """Gibt ein Python-Objekt zurück egal ob die DB den Wert als String
    oder bereits als dict/list liefert (PostgreSQL JSONB-Spalten kommen
    oft schon geparst zurück).

    - None / leer     → default
    - dict / list     → direkt zurück
    - str/bytes       → json.loads()
    - JSONDecodeError → default (mit Log)
    - Sonst           → default
    """
    if raw is None or raw == "":
        return default
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = raw.decode("utf-8")
        except Exception:
            return default
    if isinstance(raw, str):
        try:
            return _json_mod.loads(raw)
        except _json_mod.JSONDecodeError as e:
            logger.warning(f"safe_json_parse: {e} (len={len(raw)}, tail={raw[-80:]!r})")
            return default
    return default


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
from database import Project, ProjectChecklist, TimeTracking, Lead, Customer, ProjectScrapeJob, get_db, SessionLocal
from services.margin_calculator import MarginCalculator
from routers.content_scraper_router import _run_content_scrape
from services.email_service import send_phase_change_email, send_approval_request_email
from routers.auth_router import require_admin, require_any_auth, get_current_user
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
def debug_projects(db: Session = Depends(get_db), _=Depends(require_admin)):
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
        logger.error(f"projects debug error: {e}", exc_info=True)
        return {"error": "Interner Fehler"}


@router.post("/seed")
def seed_projects(db: Session = Depends(get_db), _=Depends(require_admin)):
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
    limit: int = Query(100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    List projects with pagination + optional status filter.

    Perf-optimiert: die Main-Query war bereits raw SQL, aber der Ergebnis-Loop
    machte pro Projekt eine zusaetzliche `db.query(Lead).filter(...).first()`
    um `company_name`/`website_url` als Fallback zu lesen (bei Legacy-Daten,
    wo `projects.company_name` leer war). Bei 50 Projekten = 51 Queries.

    Fix: LEFT JOIN auf leads direkt in der Main-Query, Fallback via
    COALESCE(projects.company_name, leads.company_name, '').
    → 1 Query total.
    """
    # Kunden sehen nur ihre eigenen Projekte
    where_parts = []
    params = {"limit": limit, "skip": skip}

    if current_user.role == "kunde":
        where_parts.append("p.lead_id = :lead_id")
        params["lead_id"] = current_user.lead_id
    if status:
        where_parts.append("p.status = :status")
        params["status"] = status

    where_clause = ("WHERE " + " AND ".join(where_parts) + " ") if where_parts else ""

    try:
        rows = db.execute(
            text(
                "SELECT "
                "  p.id, p.lead_id, p.status, p.fixed_price, p.actual_hours, "
                "  p.hourly_rate, p.ai_tool_costs, p.margin_percent, "
                "  p.scope_creep_flags, p.created_at, "
                "  COALESCE(NULLIF(p.company_name, ''), l.company_name, '') AS company_name, "
                "  COALESCE(NULLIF(p.website_url, ''), l.website_url, '')   AS website_url "
                "FROM projects p "
                "LEFT JOIN leads l ON l.id = p.lead_id "
                + where_clause +
                "ORDER BY p.id DESC LIMIT :limit OFFSET :skip"
            ),
            params,
        ).fetchall()
    except Exception as e:
        logger.error(f"list_projects query error: {e}", exc_info=True)
        return []

    return [
        {
            "id":                row.id,
            "lead_id":           row.lead_id,
            "name":              f"Website – {row.company_name}" if row.company_name else f"Projekt #{row.id}",
            "customer_name":     row.company_name or "",
            "status":            row.status or "phase_1",
            "current_phase":     1,
            "website_url":       row.website_url or "",
            "fixed_price":       row.fixed_price or 2000,
            "actual_hours":      row.actual_hours or 0,
            "hourly_rate":       row.hourly_rate or 45,
            "ai_tool_costs":     row.ai_tool_costs or 50,
            "margin_percent":    row.margin_percent or 0,
            "scope_creep_flags": row.scope_creep_flags or 0,
            "created_at":        str(row.created_at)[:10] if row.created_at else "",
        }
        for row in rows
    ]


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
                "gbp_checklist_json, "
                "briefing_submitted_at, briefing_approved_at, briefing_approved_by, "
                "content_approval_sent_at, content_approved_at, content_approved_by "
                "FROM projects WHERE id = :pid"
            ),
            {"pid": project_id},
        ).fetchone()
    except Exception as e:
        logger.error(f"get_project query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Interner Fehler")

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
        # Tor 1 — Briefing-Freigabe-Gate (Baustein 2)
        'briefing_submitted_at':    row[25].isoformat() if row[25] else None,
        'briefing_approved_at':     row[26].isoformat() if row[26] else None,
        'briefing_approved_by':     row[27] or None,
        # Tor 2 — Content-Freigabe-Gate (Baustein 3)
        'content_approval_sent_at': row[28].isoformat() if row[28] else None,
        'content_approved_at':      row[29].isoformat() if row[29] else None,
        'content_approved_by':      row[30] or None,
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
    _=Depends(require_any_auth),
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
    _=Depends(require_any_auth),
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
    _=Depends(require_any_auth),
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
        logger.error(f"time logging failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Interner Fehler")


@router.get("/{project_id}/checklist", response_model=list[ChecklistItemResponse])
def get_checklist(
    project_id: int,
    phase: int = Query(None),
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
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
    _=Depends(require_any_auth),
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
def get_margin(project_id: int, db: Session = Depends(get_db), _=Depends(require_any_auth)):
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
    _=Depends(require_any_auth),
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
        logger.error(f"automation trigger failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Interner Fehler")


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
def create_project_from_lead(lead_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _=Depends(require_any_auth)):
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
    _=Depends(require_any_auth),
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
    lead_id = lead.id

    # SSRF-Schutz — blockiert private IPs, Metadata-Services, file://, etc.
    from services.url_validator import validate_url
    url = validate_url(url)

    # DB-Verbindung vor dem externen Scrape-Call freigeben
    db.close()

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

        # Neue Session zum Speichern
        db2 = SessionLocal()
        try:
            lead = db2.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                lead.brand_primary_color = primary
                lead.brand_secondary_color = secondary
                lead.brand_font_primary = font_primary
                lead.brand_logo_url = logo_url
                lead.brand_colors = json.dumps(['#' + c for c in hex_colors])
                lead.brand_fonts = json.dumps(fonts)
                lead.brand_scrape_failed = False
                lead.brand_scraped_at = dt.utcnow()
                db2.commit()
        finally:
            db2.close()

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
        db2 = SessionLocal()
        try:
            lead = db2.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                lead.brand_scrape_failed = True
                db2.commit()
        except Exception:
            db2.rollback()
        finally:
            db2.close()
        logger.error(f"project scrape failed: {e}", exc_info=True)
        return {
            "success": False,
            "scrape_failed": True,
            "error": "Scrape fehlgeschlagen",
            "message": "Website konnte nicht gescrapt werden",
        }


@router.post("/{project_id}/hosting-scan")
async def hosting_scan(
    project_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Scannt Hosting, DNS, WHOIS und WordPress-Erkennung für das Projekt.
    Cache: liefert gespeicherten Scan wenn < 12h alt (außer force=true).
    """
    from services.hosting_scraper import scrape_hosting_info

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    website_url = getattr(project, "website_url", None)
    if not website_url:
        return {"error": "Keine Website-URL im Projekt hinterlegt"}

    if not website_url.startswith("http"):
        website_url = "https://" + website_url

    # ── Cache-Check: 12h TTL ──
    row = db.execute(text(
        "SELECT hosting_provider, hosting_org, hosting_ip, hosting_country, "
        "dns_provider, nameservers, domain_registrar, domain_created, domain_expires, "
        "server_software, wordpress_hosting, is_wordpress, detected_technologies, "
        "hosting_checked_at FROM projects WHERE id = :id"
    ), {"id": project_id}).fetchone()

    if not force and row and row[13]:  # hosting_checked_at
        age = (datetime.utcnow() - row[13]).total_seconds()
        if age < 43200:  # 12h
            logger.info(f"hosting-scan cache hit project {project_id} ({int(age/60)}min alt)")
            return {
                "hosting_provider":      row[0],
                "hosting_org":           row[1],
                "hosting_ip":            row[2],
                "hosting_country":       row[3],
                "dns_provider":          row[4],
                "nameservers":           row[5],
                "domain_registrar":      row[6],
                "domain_created":        row[7],
                "domain_expires":        row[8],
                "server_software":       row[9],
                "wordpress_hosting":     row[10],
                "is_wordpress":          row[11],
                "detected_technologies": row[12],
                "hosting_checked_at":    row[13].isoformat() if row[13] else None,
                "website_url":           website_url,
                "_cached":               True,
                "_cache_age_minutes":    int(age / 60),
            }

    # DB-Verbindung vor externem hosting scrape freigeben
    db.close()

    data = await scrape_hosting_info(website_url)

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        db2.execute(text("""
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
        db2.commit()
    finally:
        db2.close()

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
    _=Depends(require_any_auth),
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

    # DB-Verbindung vor externen Checks freigeben
    db.close()

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

    # Persist reachability to project — neue Session
    db2 = SessionLocal()
    try:
        project = db2.query(Project).filter(Project.id == project_id).first()
        if project:
            project.domain_reachable   = result["reachable"]
            project.domain_status_code = result.get("status_code")
            project.domain_checked_at  = datetime.utcnow()
            db2.commit()
    except Exception:
        db2.rollback()
    finally:
        db2.close()

    return result


@router.post("/{project_id}/screenshot/before")
async def screenshot_before(project_id: int, db: Session = Depends(get_db), _=Depends(require_any_auth)):
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
async def screenshot_after(project_id: int, db: Session = Depends(get_db), _=Depends(require_any_auth)):
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
def get_screenshots(project_id: int, db: Session = Depends(get_db), _=Depends(require_any_auth)):
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
    page_title:       str = "Website"
    meta_description: str = ""
    company_name:     str = ""

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

    # DB-Verbindung vor externem Netlify-API-Call freigeben
    db.close()

    from services.netlify_service import create_site
    result = await create_site(company)

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        db2.execute(
            text(
                "UPDATE projects SET netlify_site_id = :sid, netlify_site_url = :url "
                "WHERE id = :id"
            ),
            {"sid": result["site_id"], "url": result["site_url"], "id": project_id},
        )
        db2.commit()
    finally:
        db2.close()
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
        text(
            "SELECT p.netlify_site_id, COALESCE(l.company_name, '') "
            "FROM projects p LEFT JOIN leads l ON l.id = p.lead_id "
            "WHERE p.id = :id"
        ),
        {"id": project_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(400, "Keine Netlify-Site vorhanden. Zuerst Site anlegen.")

    site_id       = row[0]
    company_name  = body.company_name or row[1] or ""
    page_title    = body.page_title or company_name or "Website"

    # DB-Verbindung vor externem Netlify-Deploy freigeben
    db.close()

    from services.netlify_service import deploy_html
    result = await deploy_html(
        site_id,
        body.html,
        body.css,
        body.redirects,
        page_title=page_title,
        meta_description=body.meta_description,
        company_name=company_name,
    )

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        db2.execute(
            text(
                "UPDATE projects SET netlify_deploy_id = :did, netlify_last_deploy = :ts "
                "WHERE id = :id"
            ),
            {"did": result["deploy_id"], "ts": datetime.utcnow(), "id": project_id},
        )
        db2.commit()
    finally:
        db2.close()
    return {
        "deploy_id":  result["deploy_id"],
        "deploy_url": result["deploy_url"],
        "state":      result["state"],
    }


def _slugify_page_name(name: str) -> str:
    """URL-safe slug for sitemap page names (used by Multi-Page Deploy)."""
    import re
    s = (name or "").lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "seite"


@router.post("/{project_id}/netlify/deploy-all")
async def netlify_deploy_all(
    project_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """
    Deployt alle gespeicherten GrapesJS-Seiten eines Projekts auf Netlify.
    Jede Seite wird als eigene HTML-Datei abgelegt (Pfad = Ordner).

    Startseite (position=0 oder Name Startseite/Home) → /index.html
    Andere Seiten → /{slug}/index.html
    """
    row = db.execute(
        text(
            "SELECT p.netlify_site_id, p.lead_id, COALESCE(l.company_name, '') "
            "FROM projects p LEFT JOIN leads l ON l.id = p.lead_id "
            "WHERE p.id = :id"
        ),
        {"id": project_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(400, "Keine Netlify-Site vorhanden. Zuerst Site anlegen.")
    if not row[1]:
        raise HTTPException(400, "Kein Lead verknuepft")

    site_id      = row[0]
    lead_id      = row[1]
    company_name = row[2] or "Website"

    pages = db.execute(
        text("""
            SELECT page_name, gjs_html, gjs_css, zweck, position, ist_pflichtseite
            FROM sitemap_pages
            WHERE lead_id = :lid
            ORDER BY position, id
        """),
        {"lid": lead_id},
    ).fetchall()

    if not pages:
        raise HTTPException(400, "Keine Seiten in der Sitemap gefunden.")

    # ── Seiten-Dateien zusammenstellen ────────────────────────────────────
    page_files: dict = {}
    css_parts: list = []
    used_slugs: dict = {}

    for page in pages:
        page_name, gjs_html, gjs_css, zweck, position, ist_pflichtseite = page
        html = gjs_html or "<p>Diese Seite hat noch keinen Inhalt.</p>"
        css  = gjs_css or ""
        if css:
            css_parts.append(css)

        slug = _slugify_page_name(page_name)
        if slug in used_slugs:
            used_slugs[slug] += 1
            slug = f"{slug}-{used_slugs[slug]}"
        else:
            used_slugs[slug] = 0

        is_home = (position == 0) or slug in ("startseite", "home", "index")
        filename = "index.html" if is_home else f"{slug}/index.html"

        page_files[filename] = {
            "html":       html,
            "css":        css,
            "page_title": f"{page_name} — {company_name}" if not is_home else company_name,
            "meta_desc":  zweck or f"{page_name} — {company_name}",
        }

    # Deduplicate CSS (gemeinsame Styles)
    shared_css = "\n".join(dict.fromkeys(css_parts))

    # DB-Verbindung vor externem API-Call freigeben
    db.close()

    from services.netlify_service import deploy_all_pages
    try:
        result = await deploy_all_pages(site_id, page_files, shared_css, company_name)
    except Exception as e:
        raise HTTPException(500, f"Netlify Deploy Fehler: {str(e)[:200]}")

    # Deploy-Info speichern
    db2 = SessionLocal()
    try:
        db2.execute(
            text(
                "UPDATE projects SET netlify_deploy_id = :did, netlify_last_deploy = :ts "
                "WHERE id = :id"
            ),
            {"did": result["deploy_id"], "ts": datetime.utcnow(), "id": project_id},
        )
        db2.commit()
    finally:
        db2.close()

    return {
        "deploy_id":      result["deploy_id"],
        "deploy_url":     result["deploy_url"],
        "state":          result["state"],
        "pages_deployed": list(page_files.keys()),
    }


@router.post("/{project_id}/netlify/set-domain")
async def netlify_set_domain(
    project_id: int,
    body: NetlifyDomainRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Setzt eine Custom-Domain auf der Netlify-Site, generiert DNS-Guide,
    sendet E-Mail an Kunden und legt eine Portal-Nachricht an."""
    row = db.execute(
        text("SELECT netlify_site_id, netlify_site_url, lead_id FROM projects WHERE id = :id"),
        {"id": project_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(400, "Keine Netlify-Site vorhanden.")

    site_id       = row[0]
    site_url      = row[1] or ""
    lead_id       = row[2]

    # DB-Verbindung vor externem Netlify-Call freigeben
    db.close()

    from services.netlify_service import set_custom_domain, generate_dns_guide
    try:
        result = await set_custom_domain(site_id, body.domain)
    except Exception as e:
        logger.warning(f"Netlify set_custom_domain Fehler: {e}")
        result = {"custom_domain": body.domain}

    # DNS-Guide generieren
    guide = generate_dns_guide(body.domain, site_url)

    # Neue Session zum Speichern + Mail/Nachricht
    db2 = SessionLocal()
    try:
        db2.execute(
            text(
                "UPDATE projects SET netlify_domain = :domain, netlify_domain_status = 'pending' "
                "WHERE id = :id"
            ),
            {"domain": body.domain, "id": project_id},
        )
        db2.commit()

        # Asynchron: E-Mail + Portal-Nachricht senden (Fehler werden nur geloggt)
        try:
            _send_dns_guide_email_and_message(project_id, lead_id, body.domain, guide, db2)
        except Exception as e:
            logger.warning(f"DNS-Guide E-Mail/Nachricht Fehler: {e}")
    finally:
        db2.close()

    return {
        "custom_domain":       result.get("custom_domain", body.domain),
        "required_dns_record": result.get("required_dns_record"),
        "cname_target":        f"{body.domain}.netlify.app",
        "guide":               guide,
        "status":              "pending",
    }


def _send_dns_guide_email_and_message(project_id, lead_id, domain, guide, db):
    """Sendet DNS-Guide per E-Mail an den Kunden und legt eine Portal-Nachricht an."""
    if not lead_id:
        return
    lead = db.execute(
        text("SELECT email, company_name FROM leads WHERE id = :id"),
        {"id": lead_id},
    ).fetchone()
    if not lead:
        return

    # HTML-Tabelle für die E-Mail
    records_html = "".join([
        f"""<tr>
          <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;font-weight:600;color:#2d3748">{r['type']}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;font-family:monospace">{r['name']}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;font-family:monospace;color:#008eaa;word-break:break-all">{r['value']}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;color:#718096;font-size:12px">{r['note']}</td>
        </tr>"""
        for r in guide["records"]
    ])

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto;background:#f7fafc;padding:20px">
      <div style="background:#008eaa;padding:32px;border-radius:12px 12px 0 0;text-align:center">
        <h1 style="color:white;margin:0;font-size:24px">Ihre Website ist bereit!</h1>
        <p style="color:rgba(255,255,255,0.9);margin:8px 0 0;font-size:14px">
          Nur noch ein Schritt bis zum Go-Live
        </p>
      </div>
      <div style="padding:32px;background:#ffffff">
        <p style="color:#2d3748">Sehr geehrte Damen und Herren,</p>
        <p style="color:#4a5568;line-height:1.7">
          Ihre neue Website für <strong>{lead.company_name or 'Ihr Unternehmen'}</strong> ist fertig und bereit für den Go-Live.
          Um Ihre Domain <strong>{domain}</strong> mit der Website zu verbinden,
          tragen Sie bitte folgende Einstellungen bei Ihrem Domain-Anbieter ein:
        </p>

        <table style="width:100%;border-collapse:collapse;margin:24px 0;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden">
          <thead>
            <tr style="background:#f7fafc">
              <th style="padding:10px 14px;text-align:left;font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:0.05em">Typ</th>
              <th style="padding:10px 14px;text-align:left;font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:0.05em">Name</th>
              <th style="padding:10px 14px;text-align:left;font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:0.05em">Wert</th>
              <th style="padding:10px 14px;text-align:left;font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:0.05em">Info</th>
            </tr>
          </thead>
          <tbody>{records_html}</tbody>
        </table>

        <div style="background:#f0fff4;border:1px solid #c6f6d5;border-radius:8px;padding:16px;margin:20px 0">
          <p style="margin:0;color:#276749;font-size:13px">
            <strong>Zeitrahmen:</strong> DNS-Änderungen werden innerhalb von 1–48 Stunden aktiv.
            Wir informieren Sie automatisch sobald Ihre Domain live ist.
          </p>
        </div>

        <p style="color:#4a5568;font-size:13px;line-height:1.6">
          {guide.get('instructions', '')}
        </p>
        <p style="color:#4a5568;font-size:13px">
          Bei Fragen helfen wir Ihnen gerne weiter.
        </p>
      </div>
      <div style="background:#f7fafc;padding:16px;text-align:center;border-radius:0 0 12px 12px;font-size:12px;color:#718096">
        KOMPAGNON Communications
      </div>
    </div>
    """

    # E-Mail versenden ueber die kanonische send_email in services/email.py.
    # Die Funktion gibt bool zurueck und wirft keine Exception, deshalb kein
    # try/except-Fallback noetig — stattdessen das Return-Ergebnis pruefen.
    if lead.email:
        from services.email import send_email
        ok = send_email(
            to_email=lead.email,
            subject=f"DNS-Einstellungen für {domain} — letzter Schritt vor Go-Live",
            html_body=html_body,
        )
        if ok:
            logger.info(f"DNS-Guide E-Mail gesendet an {lead.email}")
        else:
            logger.warning(
                f"DNS-Guide E-Mail an {lead.email} fehlgeschlagen — "
                "SMTP-Konfiguration in Render pruefen "
                "(SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_SENDER_EMAIL)"
            )

    # Portal-Nachricht anlegen
    try:
        records_text = "\n".join([
            f"  • {r['type']}  {r['name']}  →  {r['value']}" for r in guide["records"]
        ])
        msg = (
            f"Ihre Website ist bereit! Um {domain} zu verbinden, tragen Sie bitte "
            f"folgende DNS-Einträge bei Ihrem Domain-Anbieter ein:\n\n"
            f"{records_text}\n\n"
            f"Die Änderungen werden innerhalb von 1–48 Stunden aktiv. "
            f"Sie haben diese Anleitung auch per E-Mail erhalten."
        )
        db.execute(text("""
            INSERT INTO messages (lead_id, channel, content, direction, created_at, sender_role)
            VALUES (:lead_id, 'in_app', :content, 'outbound', NOW(), 'system')
        """), {"lead_id": lead_id, "content": msg})
        db.commit()
    except Exception as e:
        logger.warning(f"DNS-Guide Portal-Nachricht Fehler: {e}")
        try:
            db.rollback()
        except Exception:
            pass


@router.get("/{project_id}/netlify/status")
async def netlify_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ruft den Netlify-Status des Projekts ab.
    Gibt IMMER 200 mit status-Feld zurück — nie 404/500 für fehlende Site.
    """
    row = db.execute(
        text(
            "SELECT netlify_site_id, netlify_site_url, netlify_deploy_id, "
            "netlify_domain, netlify_domain_status, netlify_ssl_active, netlify_last_deploy "
            "FROM projects WHERE id = :id"
        ),
        {"id": project_id},
    ).fetchone()

    if not row:
        return {"connected": False, "status": "project_not_found", "project_id": project_id}
    if not row[0]:
        return {
            "connected": False,
            "status": "not_connected",
            "message": "Keine Netlify-Site verbunden",
            "project_id": project_id,
        }

    # Check if NETLIFY_API_TOKEN is configured
    if not os.getenv("NETLIFY_API_TOKEN"):
        return {
            "connected": False,
            "status": "no_token",
            "message": "NETLIFY_API_TOKEN nicht konfiguriert",
            "netlify_site_id": row[0],
            "netlify_site_url": row[1],
        }

    site_id = row[0]
    try:
        from services.netlify_service import get_site_status
        live = await get_site_status(site_id)
    except Exception as e:
        logger.error(f"Netlify get_site_status Fehler: {e}", exc_info=True)
        return {
            "connected": False,
            "status": "api_error",
            "message": "Netlify-Status nicht abrufbar",
            "netlify_site_id": row[0],
            "netlify_site_url": row[1],
        }

    # SSL-Status in DB aktualisieren
    ssl_active = bool(live.get("ssl"))
    try:
        db.execute(
            text("UPDATE projects SET netlify_ssl_active = :ssl WHERE id = :id"),
            {"ssl": ssl_active, "id": project_id},
        )
        db.commit()
    except Exception as e:
        logger.warning(f"Netlify SSL-Status update Fehler: {e}")
        db.rollback()

    return {
        **live,
        "connected":             True,
        "status":                "connected",
        "netlify_site_id":       row[0],
        "netlify_site_url":      row[1],
        "netlify_deploy_id":     row[2],
        "netlify_domain":        row[3],
        "netlify_domain_status": row[4],
        "netlify_ssl_active":    ssl_active,
        "netlify_last_deploy":   row[6].isoformat() if row[6] else None,
    }


# ── Website-Versionen (KI generiert 3 Entwürfe) ───────────────────────────────

@router.post("/{project_id}/generate-versions")
async def generate_website_versions(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generiert 3 Website-Versionen basierend auf Briefing, Inspirationen und Templates."""
    import json as _json
    import os as _os

    # Projektdaten + Lead laden (inkl. Briefing-Felder)
    project_row = db.execute(text("""
        SELECT p.id as pid, p.lead_id as lead_id, p.company_name as p_company,
               l.company_name as l_company, l.trade, l.wz_title,
               l.inspiration_url_1, l.inspiration_url_2, l.inspiration_url_3
        FROM projects p
        LEFT JOIN leads l ON p.lead_id = l.id
        WHERE p.id = :id
    """), {"id": project_id}).fetchone()
    if not project_row:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead_id = project_row.lead_id
    company_name = project_row.p_company or project_row.l_company or f"Projekt {project_id}"

    # Briefing-Daten (separate Tabelle)
    briefing = None
    try:
        briefing = db.execute(text("""
            SELECT gewerk, leistungen, einzugsgebiet, usp, mitbewerber,
                   farben, wunschseiten, stil
            FROM briefings WHERE lead_id = :id
            ORDER BY created_at DESC LIMIT 1
        """), {"id": lead_id}).fetchone()
    except Exception:
        pass

    gewerk = (briefing.gewerk if briefing else None) or project_row.trade or project_row.wz_title or ""
    stil   = (briefing.stil if briefing else None) or "modern"

    # Alte Website-Content Teaser
    old_content_rows = []
    try:
        old_content_rows = db.execute(text("""
            SELECT title, h1, text_preview
            FROM website_content_cache
            WHERE customer_id = :cid
            ORDER BY scraped_at DESC LIMIT 5
        """), {"cid": lead_id}).fetchall()
    except Exception:
        pass

    # Templates filtern: passend zum Gewerk oder "alle"
    templates = db.execute(text("""
        SELECT id, name, slug,
               COALESCE(style_tags, '') AS style_tags,
               COALESCE(gewerk_tags, '') AS gewerk_tags
        FROM website_templates
        WHERE COALESCE(is_active, TRUE) = TRUE
          AND (gewerk_tags ILIKE :gewerk OR gewerk_tags ILIKE '%alle%' OR gewerk_tags IS NULL OR gewerk_tags = '')
        ORDER BY RANDOM()
        LIMIT 9
    """), {"gewerk": f"%{gewerk.lower()[:20]}%"}).fetchall()

    if len(templates) < 3:
        templates = db.execute(text("""
            SELECT id, name, slug,
                   COALESCE(style_tags, '') AS style_tags,
                   COALESCE(gewerk_tags, '') AS gewerk_tags
            FROM website_templates
            WHERE COALESCE(is_active, TRUE) = TRUE
            ORDER BY RANDOM() LIMIT 9
        """)).fetchall()

    if len(templates) < 1:
        raise HTTPException(400, "Keine Templates vorhanden. Bitte erst welche importieren.")

    template_options = "\n".join([
        f"Template {i+1}: ID={t.id}, Name={t.name}, Stile={t.style_tags}"
        for i, t in enumerate(templates[:9])
    ])

    old_content_text = "\n".join([
        f"- {r.title or ''}: {(r.text_preview or '')[:200]}"
        for r in old_content_rows if r.title
    ]) or "Keine Inhalte von alter Website vorhanden"

    inspirations = "\n".join(filter(None, [
        project_row.inspiration_url_1,
        project_row.inspiration_url_2,
        project_row.inspiration_url_3,
    ])) or "Keine Inspirationsseiten angegeben"

    system_prompt = (
        "Du bist ein professioneller Webdesigner und Markenstratege "
        "für deutsche Handwerksbetriebe. Du analysierst alle verfügbaren "
        "Informationen und wählst die 3 besten passenden Templates aus. "
        "Du denkst dabei PROAKTIV: Wenn der Kunde kein starkes Brand hat, "
        "machst du konkrete Optimierungsvorschläge für Farben, Stil und "
        "Positionierung die seine Zielgruppe ansprechen.\n\n"
        "Antworte AUSSCHLIESSLICH als valides JSON. Kein Markdown. "
        "Kein Text davor oder danach."
    )

    user_prompt = f"""
KUNDENINFORMATIONEN:
Firma: {company_name}
Gewerk: {gewerk or 'nicht angegeben'}
Leistungen: {(briefing.leistungen if briefing else None) or 'nicht angegeben'}
Einzugsgebiet: {(briefing.einzugsgebiet if briefing else None) or 'nicht angegeben'}
USPs: {(briefing.usp if briefing else None) or 'nicht angegeben'}
Gewünschte Farben: {(briefing.farben if briefing else None) or 'nicht angegeben'}
Gewünschter Stil: {stil}

INHALTE DER ALTEN WEBSITE:
{old_content_text}

INSPIRATIONSSEITEN DES KUNDEN:
{inspirations}

VERFÜGBARE TEMPLATES:
{template_options}

AUFGABE:
Wähle 3 verschiedene Templates aus den verfügbaren aus und begründe die Wahl.
Jede Version soll einen anderen Ansatz verfolgen:
- Version A: nah am Kundenwunsch
- Version B: optimierte/moderne Variante
- Version C: mutigere/auffälligere Variante

Antworte als JSON:
{{
  "versions": [
    {{
      "label": "A",
      "template_id": <ID>,
      "titel": "Kurzer Titel (max 6 Wörter)",
      "beschreibung": "2-3 Sätze",
      "optimierungen": "Was wird gegenüber der alten Website verbessert",
      "farb_empfehlung": "Konkrete Farbempfehlung",
      "zielgruppen_ansprache": "Wie das Design die Zielgruppe anspricht"
    }},
    {{"label": "B", ...}},
    {{"label": "C", ...}}
  ],
  "gesamt_empfehlung": "Welche Version empfohlen wird und warum"
}}
"""

    # Template-Infos als einfache dicts speichern (für Fallback nach DB-Close)
    templates_data = [
        {"id": t.id, "name": t.name, "style_tags": t.style_tags}
        for t in templates
    ]
    available_ids = {t["id"] for t in templates_data}

    # DB-Verbindung vor dem externen Claude-Call freigeben
    db.close()

    # Fallback ohne KI: zufällig 3 Templates
    result = None
    try:
        from anthropic import Anthropic
        api_key = _os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY nicht gesetzt")
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = response.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = _json.loads(raw)
    except Exception as e:
        logger.warning(f"KI-Versionierung Fehler, nutze Zufallsauswahl: {e}")
        # Fallback: zufällig 3 Templates
        chosen = templates_data[:3]
        labels = ["A", "B", "C"]
        result = {
            "versions": [
                {
                    "label": labels[i],
                    "template_id": t["id"],
                    "titel":        f"Version {labels[i]}: {t['name']}",
                    "beschreibung": "Automatische Auswahl (KI nicht verfügbar).",
                    "optimierungen": "",
                    "farb_empfehlung": "",
                    "zielgruppen_ansprache": "",
                }
                for i, t in enumerate(chosen)
            ],
            "gesamt_empfehlung": "KI war nicht verfügbar — 3 Templates zufällig gewählt.",
        }

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        # Alte Versionen löschen
        db2.execute(text("DELETE FROM website_versions WHERE project_id = :id"), {"id": project_id})

        # 3 Versionen speichern
        saved = []
        template_ids_in_result = {int(v.get("template_id", 0)) for v in result.get("versions", []) if v.get("template_id")}

        for v in result.get("versions", [])[:3]:
            tid = v.get("template_id")
            # Absicherung: falls KI eine falsche ID vorschlägt, nimm ein zufälliges verfügbares
            if not tid or tid not in available_ids:
                tid = next(iter(available_ids - template_ids_in_result), next(iter(available_ids)))
                template_ids_in_result.add(tid)

            tpl = db2.execute(text(
                "SELECT html_content, css_content, grapes_data FROM website_templates WHERE id = :id"
            ), {"id": tid}).fetchone()

            row = db2.execute(text("""
                INSERT INTO website_versions
                  (project_id, version_label, template_id, html, css, gjs_data, ki_reasoning)
                VALUES (:pid, :label, :tid, :html, :css, :gjs, :reasoning)
                RETURNING id
            """), {
                "pid":       project_id,
                "label":     v.get("label", "A"),
                "tid":       tid,
                "html":      (tpl.html_content if tpl else "") or "",
                "css":       (tpl.css_content if tpl else "") or "",
                "gjs":       _json.dumps(tpl.grapes_data) if (tpl and tpl.grapes_data) else None,
                "reasoning": _json.dumps({
                    "titel":             v.get("titel"),
                    "beschreibung":      v.get("beschreibung"),
                    "optimierungen":     v.get("optimierungen"),
                    "farb_empfehlung":   v.get("farb_empfehlung"),
                    "zielgruppe":        v.get("zielgruppen_ansprache"),
                }, ensure_ascii=False),
            })
            saved.append({"version": v.get("label", "A"), "id": row.fetchone()[0]})

        db2.commit()
    finally:
        db2.close()

    return {
        "versions":     saved,
        "empfehlung":   result.get("gesamt_empfehlung"),
        "project_id":   project_id,
    }


@router.get("/{project_id}/versions")
def list_versions(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Alle generierten Versionen für ein Projekt."""
    rows = db.execute(text("""
        SELECT v.id, v.version_label, v.template_id, v.selected, v.ki_reasoning,
               v.created_at, t.name as template_name, t.thumbnail_url
        FROM website_versions v
        LEFT JOIN website_templates t ON v.template_id = t.id
        WHERE v.project_id = :pid
        ORDER BY v.version_label
    """), {"pid": project_id}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/{project_id}/versions/{version_id}/select")
def select_version(
    project_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Eine Version als ausgewählt markieren (alle anderen deaktivieren)."""
    db.execute(text("UPDATE website_versions SET selected=FALSE WHERE project_id=:pid"), {"pid": project_id})
    db.execute(text("""
        UPDATE website_versions SET selected=TRUE
        WHERE id=:vid AND project_id=:pid
    """), {"vid": version_id, "pid": project_id})
    db.commit()
    return {"selected": version_id}


@router.get("/{project_id}/versions/{version_id}/preview")
def version_preview(
    project_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """HTML-Preview einer Version für iframe-Einbettung."""
    from fastapi.responses import HTMLResponse
    row = db.execute(text("""
        SELECT html, css FROM website_versions
        WHERE id = :vid AND project_id = :pid
    """), {"vid": version_id, "pid": project_id}).fetchone()
    if not row:
        raise HTTPException(404, "Version nicht gefunden")
    html = row.html or "<p>Kein Inhalt</p>"
    css  = row.css or ""
    return HTMLResponse(
        f"""<!DOCTYPE html><html lang="de"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{css}</style></head><body>{html}</body></html>"""
    )


# ── Scrape Website Content ─────────────────────────────────────────────────────

@router.get("/{project_id}/scrape-content")
def scrape_project_content(project_id: int, db: Session = Depends(get_db), _=Depends(require_any_auth)):
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
        logger.error(f"website unreachable: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail="Website nicht erreichbar")

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
async def run_project_qa(project_id: int, db: Session = Depends(get_db), _=Depends(require_any_auth)):
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
def get_qa_result(project_id: int, db: Session = Depends(get_db), _=Depends(require_any_auth)):
    """Gibt das zuletzt gespeicherte QA-Ergebnis zurück.
    Funktioniert egal ob qa_result als Text-JSON oder JSONB-Dict kommt.
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"status": "no_result", "message": "Projekt nicht gefunden"}
        if not project.qa_result:
            return {"status": "no_result", "message": "Noch kein QA-Scan für dieses Projekt"}

        parsed = safe_json_parse(project.qa_result, default=None)
        if parsed is None:
            return {
                "status": "parse_error",
                "message": "QA-Ergebnis konnte nicht gelesen werden",
                "score": project.qa_score,
                "run_at": str(project.qa_run_at)[:16] if project.qa_run_at else None,
            }

        return {
            "score": project.qa_score,
            "golive_ok": project.qa_golive_ok,
            "run_at": str(project.qa_run_at)[:16] if project.qa_run_at else None,
            "result": parsed,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"QA-Result unerwarteter Fehler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Interner Fehler")


@router.post("/{project_id}/credentials")
def add_credential(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_auth),
):
    label    = (data.get("label") or "").strip()
    username = (data.get("username") or data.get("benutzername") or "").strip()
    password = (data.get("password") or data.get("passwort") or "").strip()
    url      = (data.get("url") or "").strip()
    notes    = (data.get("notes") or data.get("notizen") or "").strip()

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

    typ = (data.get("typ") or "sonstiges").strip()
    db.execute(text("""
        INSERT INTO project_credentials
            (project_id, label, typ, username, password_encrypted, url, notes)
        VALUES
            (:pid, :label, :typ, :username, :pw, :url, :notes)
    """), {
        "pid":      project_id,
        "label":    label,
        "typ":      typ,
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
    current_user=Depends(require_any_auth),
):
    rows = db.execute(text("""
        SELECT id, label, COALESCE(typ,'sonstiges') as typ, username, password_encrypted,
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
            "typ":        r["typ"] or "sonstiges",
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
    current_user=Depends(require_any_auth),
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
    seiten = safe_json_parse(row[0], default=[])
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

    freigaben = safe_json_parse(row[1], default={}) or {}

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

    freigaben = safe_json_parse(row[0], default={}) or {}

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

    # DB-Verbindung vor externen PageSpeed + Screenshot Calls freigeben
    db.close()

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

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        db2.execute(text("""
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
        db2.commit()
    finally:
        db2.close()

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


@router.post("/{project_id}/ki-report")
async def generate_ki_report(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """
    Sammelt alle Onboarding-Daten und lässt Claude einen strukturierten
    Report mit Lückenanalyse erstellen.
    """
    import httpx, json, re

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead_id = project.lead_id
    if not lead_id:
        raise HTTPException(400, "Kein Lead verknüpft")

    # ── Alle verfügbaren Onboarding-Daten sammeln ──
    data_parts = []

    # 1. Lead-Basisdaten
    lead = db.execute(
        text("""
            SELECT company_name, website_url, email, phone, city,
                   trade, wz_code, wz_title, brand_primary_color,
                   brand_secondary_color, brand_font_primary, brand_design_style
            FROM leads WHERE id = :lid
        """),
        {"lid": lead_id},
    ).fetchone()
    if lead:
        data_parts.append(f"""## Unternehmensdaten
Firma: {lead.company_name or '–'}
Website: {lead.website_url or '–'}
E-Mail: {lead.email or '–'}
Telefon: {lead.phone or '–'}
Stadt: {lead.city or '–'}
Gewerk: {lead.trade or '–'}
WZ-Code: {lead.wz_code or '–'} — {lead.wz_title or '–'}
Primärfarbe: {lead.brand_primary_color or '–'}
Sekundärfarbe: {lead.brand_secondary_color or '–'}
Schriftart: {lead.brand_font_primary or '–'}
Designstil: {lead.brand_design_style or '–'}""")

    # 2. Briefing-Daten
    briefing = db.execute(
        text("""
            SELECT gewerk, leistungen, einzugsgebiet, zielgruppe,
                   usp, mitbewerber, wunschseiten, farben, stil,
                   sonstige_hinweise, logo_vorhanden, fotos_vorhanden
            FROM briefings WHERE lead_id = :lid
            ORDER BY id DESC LIMIT 1
        """),
        {"lid": lead_id},
    ).fetchone()
    if briefing:
        data_parts.append(f"""## Briefing-Daten
Gewerk: {briefing.gewerk or '–'}
Leistungen: {briefing.leistungen or '–'}
Einzugsgebiet: {briefing.einzugsgebiet or '–'}
Zielgruppe: {briefing.zielgruppe or '–'}
USP: {briefing.usp or '–'}
Mitbewerber: {briefing.mitbewerber or '–'}
Wunschseiten: {briefing.wunschseiten or '–'}
Farben: {briefing.farben or '–'}
Stil: {briefing.stil or '–'}
Sonstige Hinweise: {briefing.sonstige_hinweise or '–'}
Logo vorhanden: {'Ja' if briefing.logo_vorhanden else 'Nein'}
Fotos vorhanden: {'Ja' if briefing.fotos_vorhanden else 'Nein'}""")

    # 3. Letzter Audit (Tabelle: audit_results)
    try:
        audit = db.execute(
            text("""
                SELECT total_score, ai_summary
                FROM audit_results WHERE lead_id = :lid
                ORDER BY created_at DESC LIMIT 1
            """),
            {"lid": lead_id},
        ).fetchone()
        if audit:
            data_parts.append(f"""## Audit
Score: {audit[0] or '–'}/100
Zusammenfassung: {audit[1] or '–'}""")
    except Exception:
        pass

    # 4. PageSpeed (aus leads-Tabelle, nicht separate Tabelle)
    try:
        ps = db.execute(
            text("SELECT pagespeed_mobile_score, pagespeed_desktop_score FROM leads WHERE id = :lid"),
            {"lid": lead_id},
        ).fetchone()
        if ps and (ps[0] or ps[1]):
            data_parts.append(f"""## PageSpeed
Mobil: {ps[0] or '–'}/100
Desktop: {ps[1] or '–'}/100""")
    except Exception:
        pass

    # 5. Crawler (Tabelle: crawl_results, Spalte: customer_id)
    try:
        crawler_count = db.execute(
            text("SELECT COUNT(*) FROM crawl_results WHERE customer_id = :lid"),
            {"lid": lead_id},
        ).scalar()
        if crawler_count:
            data_parts.append(f"## Crawler\nGecrawlte Seiten: {crawler_count}")
    except Exception:
        pass

    # 6. Sitemap-Seiten
    sitemap_pages = db.execute(
        text("SELECT page_name, page_type, ziel_keyword FROM sitemap_pages WHERE lead_id = :lid AND ist_pflichtseite = false ORDER BY position"),
        {"lid": lead_id},
    ).fetchall()
    if sitemap_pages:
        seiten_text = "\n".join([
            f"- {p.page_name} ({p.page_type}){' → ' + p.ziel_keyword if p.ziel_keyword else ''}"
            for p in sitemap_pages
        ])
        data_parts.append(f"## Geplante Seiten (Sitemap)\n{seiten_text}")

    if not data_parts:
        raise HTTPException(400, "Keine Onboarding-Daten vorhanden. Bitte zuerst Audit, Briefing und Crawler ausführen.")

    all_data = "\n\n".join(data_parts)

    # DB-Verbindung vor externem API-Call freigeben
    db.close()

    # ── KI-Analyse via Claude ──
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    prompt = f"""Du bist ein Website-Stratege bei KOMPAGNON. Analysiere die folgenden Onboarding-Daten eines Kunden und erstelle einen strukturierten Report.

{all_data}

Erstelle einen JSON-Report mit GENAU dieser Struktur (nur JSON, kein Markdown):
{{
  "completeness_score": <0-100, wie vollständig sind die Daten>,
  "data_points_count": <Anzahl vorhandener Datenpunkte>,
  "gaps_count": <Anzahl fehlender wichtiger Informationen>,
  "summary": "<3-5 Sätze: Wer ist der Kunde, was macht er, wo steht er>",
  "available_data": [
    "<Was vorhanden ist, z.B. 'Briefing mit USP und Zielgruppe'>",
    "<weiterer Punkt>"
  ],
  "gaps": [
    {{
      "field": "<Name des fehlenden Feldes, z.B. 'Fotos/Bildmaterial'>",
      "impact": "<Warum das fehlt ist ein Problem für die Content-Erstellung>",
      "action": "<Was konkret getan werden kann>"
    }}
  ],
  "recommendation": "<1-2 Sätze: Kann man jetzt mit Content-Erstellung beginnen oder was fehlt noch>",
  "content_brief": "<Kompakter Steckbrief in 10-15 Zeilen für die spätere Content-KI: Firma, Gewerk, USP, Zielgruppe, Leistungen, Keyword-Fokus, Tonalität>"
}}"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        content = resp.json()["content"][0]["text"].strip()

        # JSON parsen — eventuelle Markdown-Backticks entfernen
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        report_data = json.loads(content)

        return report_data

    except Exception as e:
        raise HTTPException(500, f"KI-Report fehlgeschlagen: {str(e)[:200]}")


@router.post("/{project_id}/moodboard")
async def save_moodboard(
    project_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Speichert die Moodboard-Auswahl zum Projekt."""
    import json as _json
    db.execute(
        text("""
            UPDATE projects SET
              moodboard_data = :data,
              moodboard_updated_at = NOW()
            WHERE id = :id
        """),
        {"data": _json.dumps(body, ensure_ascii=False), "id": project_id},
    )
    db.commit()
    return {"ok": True}


@router.post("/{project_id}/moodboard/preview")
async def generate_moodboard_preview(
    project_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Lässt Claude eine Moodboard-Beschreibung + Farbpalette generieren."""
    import httpx, json, re

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    # DB-Verbindung vor externem Call freigeben
    db.close()

    stilrichtung = body.get("stilrichtung", "")
    farbstimmung = body.get("farbstimmung", "")
    typografie   = body.get("typografie", "")
    bildsprache  = body.get("bildsprache", [])
    notizen      = body.get("notizen", "")

    prompt = f"""Du bist ein Website-Designer für Handwerksbetriebe. Erstelle auf Basis dieser Moodboard-Auswahl eine konkrete Designbeschreibung und Farbpalette.

Stilrichtung: {stilrichtung}
Farbstimmung: {farbstimmung}
Typografie: {typografie}
Bildsprache: {', '.join(bildsprache) if bildsprache else 'nicht festgelegt'}
Besondere Wünsche: {notizen or 'keine'}

Antworte NUR mit diesem JSON (kein Markdown, keine Erklärungen):
{{
  "description": "<3-4 Sätze: Wie wird die Website aussehen, welche Atmosphäre entsteht, was macht sie besonders>",
  "color_palette": [
    {{"hex": "#FARBCODE", "role": "Primärfarbe"}},
    {{"hex": "#FARBCODE", "role": "Sekundärfarbe"}},
    {{"hex": "#FARBCODE", "role": "Akzentfarbe"}},
    {{"hex": "#FARBCODE", "role": "Hintergrund"}},
    {{"hex": "#FARBCODE", "role": "Text"}}
  ]
}}"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 600,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        content = resp.json()["content"][0]["text"].strip()
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        return json.loads(content)
    except Exception as e:
        raise HTTPException(500, f"Preview-Generierung fehlgeschlagen: {str(e)[:200]}")


@router.post("/{project_id}/briefing-prefill")
async def briefing_prefill_from_content(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Analysiert gecrawlten Website-Content und gibt Briefing-Vorschläge zurück."""
    import os, httpx, json, re
    from urllib.parse import urlparse

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    lead_id = project.lead_id
    if not lead_id:
        raise HTTPException(400, "Kein Lead verknüpft")

    rows = db.execute(
        text("""
            SELECT url, title, meta_description, h1, h2s, text_preview
            FROM website_content_cache
            WHERE customer_id = :lid ORDER BY scraped_at DESC LIMIT 20
        """),
        {"lid": lead_id},
    ).fetchall()

    if not rows:
        raise HTTPException(400, "Kein Website-Content vorhanden. Bitte zuerst Crawler + Content-Scraping ausführen.")

    # Kontaktdaten
    try:
        contact = db.execute(
            text("SELECT contact_phone, contact_email, contact_address FROM project_scraped_pages WHERE project_id = :pid LIMIT 1"),
            {"pid": project_id},
        ).fetchone()
    except Exception:
        contact = None

    pages_text = []
    all_h2s = []
    all_titles = []
    page_names = []

    for row in rows:
        url, title, meta, h1, h2s_json, preview = row
        all_titles.append(title or h1 or '')
        try:
            h2s = json.loads(h2s_json or '[]')
            all_h2s.extend(h2s)
        except Exception:
            pass
        if preview:
            pages_text.append(f"URL: {url}\nH1: {h1 or title}\nVorschau: {preview[:400]}")
        try:
            path = urlparse(url).path.strip('/').split('/')[-1]
            if path and len(path) > 1:
                name = path.replace('-', ' ').replace('_', ' ').title()
                if name not in page_names:
                    page_names.append(name)
        except Exception:
            pass

    wunschseiten = ', '.join(page_names[:8])

    def heuristic():
        return {
            "gewerk": (all_titles[0] if all_titles else '')[:80],
            "leistungen": '\n'.join(set(all_h2s[:10])),
            "einzugsgebiet": (contact[2] if contact and contact[2] else ''),
            "wunschseiten": wunschseiten,
            "source": "heuristic",
        }

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return heuristic()

    content_summary = "\n---\n".join(pages_text[:8])
    prompt = f"""Analysiere diesen Website-Content eines Handwerksbetriebs.
{content_summary}

Gib NUR JSON zurück:
{{"gewerk":"<max 60 Zeichen>","leistungen":"<kommagetrennt, max 300>","einzugsgebiet":"<Stadt/Region>","usp":"<max 200>","wunschseiten":"{wunschseiten}","zielgruppe":"Privatkunden|Gewerbekunden|Beides"}}"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 600, "messages": [{"role": "user", "content": prompt}]},
            )
        resp.raise_for_status()
        txt = resp.json()["content"][0]["text"].strip()
        txt = re.sub(r'^```json\s*', '', txt)
        txt = re.sub(r'\s*```$', '', txt)
        result = json.loads(txt)
        result["source"] = "claude"
        return result
    except Exception:
        return heuristic()


@router.post("/{project_id}/content-workshop/generate-all")
async def generate_all_pages_content(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generiert KI-Content fuer ALLE Sitemap-Seiten in einem einzigen Claude-Call.

    Optimierung #3: ersetzt das sequentielle Anklicken von "KI generieren"
    fuer jede Seite. Ein einziger Claude-Call erzeugt alle h1/hero/abschnitt/
    cta/meta-Texte, das Ergebnis wird per UPDATE in sitemap_pages geschrieben.

    Diese Route MUSS vor /content-workshop/{page_id} registriert sein, damit
    FastAPI "generate-all" nicht als page_id-Parameter interpretiert.
    """
    import os, httpx, json, re

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead    = project.lead
    lead_id = project.lead_id

    # ── Alle Sitemap-Seiten laden ──────────────────────────────────────
    pages = db.execute(
        text("""
            SELECT id, page_name, page_type, ziel_keyword, zweck
            FROM sitemap_pages
            WHERE lead_id = :lid
            ORDER BY position, id
        """),
        {"lid": lead_id},
    ).fetchall()

    if not pages:
        raise HTTPException(400, "Keine Sitemap-Seiten gefunden. Zuerst Sitemap anlegen.")

    # ── Briefing laden ─────────────────────────────────────────────────
    briefing = db.execute(
        text("""
            SELECT gewerk, leistungen, einzugsgebiet, usp, zielgruppe
            FROM briefings WHERE lead_id = :lid LIMIT 1
        """),
        {"lid": lead_id},
    ).fetchone()

    # ── Brand-Daten laden (Best-effort, defensiv gegen kaputtes JSON) ─
    brand = {}
    brand_json = getattr(lead, "brand_design_json", None)
    if brand_json:
        try:
            parsed = json.loads(brand_json) if isinstance(brand_json, str) else brand_json
            if isinstance(parsed, dict):
                brand = parsed
        except Exception:
            brand = {}

    # ── Gecrawlten Content laden (Top 8 nach Aktualitaet) ─────────────
    crawled_rows = db.execute(
        text("""
            SELECT url, h1, text_preview
            FROM website_content_cache
            WHERE customer_id = :lid
            ORDER BY scraped_at DESC
            LIMIT 20
        """),
        {"lid": lead_id},
    ).fetchall()
    crawled_summary = "\n".join(
        [f"- {r[1] or r[0]}: {(r[2] or '')[:200]}" for r in crawled_rows[:8]]
    ) or "Kein gecrawlter Content vorhanden."

    # ── Basisdaten ─────────────────────────────────────────────────────
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    gewerk     = briefing[0] if briefing and briefing[0] else "Handwerksbetrieb"
    leistungen = briefing[1] if briefing and briefing[1] else ""
    region     = briefing[2] if briefing and briefing[2] else ""
    usp        = briefing[3] if briefing and briefing[3] else ""
    zielgruppe = briefing[4] if briefing and briefing[4] else "Privatkunden"
    company    = getattr(lead, "company_name", "") or ""
    phone      = getattr(lead, "phone", "") or ""

    pages_for_prompt = [
        {
            "id": p[0],
            "name": p[1],
            "type": p[2],
            "keyword": p[3] or "",
            "zweck": p[4] or "",
        }
        for p in pages
    ]
    pages_json_str = json.dumps(pages_for_prompt, ensure_ascii=False, indent=2)

    prompt = f"""Du bist ein professioneller Werbetexter für deutsche Handwerksbetriebe.

UNTERNEHMEN:
- Firma: {company}
- Branche/Gewerk: {gewerk}
- Leistungen: {leistungen}
- Region: {region}
- USP: {usp}
- Telefon: {phone}
- Zielgruppe: {zielgruppe}
- Design-Stil: {brand.get("style_keyword", "Modern & professionell")}

BESTEHENDE WEBSITE (gecrawlt):
{crawled_summary}

Schreibe jetzt für JEDE der folgenden Seiten professionelle deutsche Texte.
Ton: direkt, vertrauenswürdig, keine Floskeln. Regional konkret. Immer den USP einbauen.

SEITEN:
{pages_json_str}

Antworte NUR mit einem JSON-Array. Ein Objekt pro Seite:
[
  {{
    "page_id": <int, die id aus der Seiten-Liste>,
    "h1": "<Hauptueberschrift, max 70 Zeichen, enthaelt Gewerk + Region>",
    "hero_text": "<Hero-Fliesstext, 2-3 Saetze, Nutzen fuer den Kunden>",
    "abschnitt_text": "<Haupttext der Seite, 3-5 Saetze, ausfuehrlicher>",
    "cta": "<Call-to-Action Text, max 40 Zeichen, aktiv formuliert>",
    "meta_title": "<SEO-Title, max 60 Zeichen, Keyword + Firmenname>",
    "meta_description": "<SEO-Description, max 155 Zeichen, Nutzen + CTA>"
  }}
]

Nur JSON, kein Markdown, keine Erklaerungen."""

    # DB-Verbindung vor dem API-Call freigeben — der Claude-Call kann
    # 30-60 Sekunden dauern, wir halten in der Zeit keinen DB-Connection-
    # Slot besetzt.
    db.close()

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        results = json.loads(raw)
        if not isinstance(results, list):
            raise ValueError("Claude-Response ist kein JSON-Array")
    except Exception as e:
        logger.error(f"generate_all_pages_content KI-Fehler: {e}", exc_info=True)
        raise HTTPException(500, f"KI-Generierung fehlgeschlagen: {str(e)[:200]}")

    # ── Ergebnisse in DB speichern (frische Session) ───────────────────
    db2 = SessionLocal()
    saved = []
    try:
        for item in results:
            if not isinstance(item, dict):
                continue
            page_id = item.get("page_id")
            if not page_id:
                continue
            try:
                page_id_int = int(page_id)
            except (TypeError, ValueError):
                continue
            db2.execute(
                text("""
                    UPDATE sitemap_pages SET
                        ki_h1                = :h1,
                        ki_hero_text         = :hero,
                        ki_abschnitt_text    = :abschnitt,
                        ki_cta               = :cta,
                        ki_meta_title        = :meta_title,
                        ki_meta_description  = :meta_desc,
                        content_generated    = true,
                        content_generated_at = NOW()
                    WHERE id = :pid AND lead_id = :lid
                """),
                {
                    "h1":         (item.get("h1") or "")[:500],
                    "hero":       item.get("hero_text") or "",
                    "abschnitt":  item.get("abschnitt_text") or "",
                    "cta":        (item.get("cta") or "")[:100],
                    "meta_title": (item.get("meta_title") or "")[:70],
                    "meta_desc":  (item.get("meta_description") or "")[:160],
                    "pid":        page_id_int,
                    "lid":        lead_id,
                },
            )
            saved.append(page_id_int)
        db2.commit()
    except Exception as e:
        db2.rollback()
        logger.error(f"generate_all_pages_content DB-Fehler: {e}", exc_info=True)
        raise HTTPException(500, f"DB-Speichern fehlgeschlagen: {str(e)[:200]}")
    finally:
        db2.close()

    logger.info(
        f"generate_all_pages_content: Projekt {project_id} — "
        f"{len(saved)} von {len(pages)} Seiten KI-generiert"
    )
    return {
        "success": True,
        "pages_generated": len(saved),
        "page_ids": saved,
        "results": results,
    }


@router.post("/{project_id}/content-workshop/{page_id}")
async def generate_page_content(
    project_id: int,
    page_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generiert KI-Content fuer eine Sitemap-Seite basierend auf Crawler-Daten + Briefing."""
    import os, httpx, json, re

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead_id = project.lead_id

    page = db.execute(
        text("SELECT page_name, page_type, ziel_keyword, zweck FROM sitemap_pages WHERE id = :id"),
        {"id": page_id},
    ).fetchone()
    if not page:
        raise HTTPException(404, "Seite nicht gefunden")

    page_name, page_type, keyword, zweck = page

    briefing = db.execute(
        text("SELECT gewerk, leistungen, einzugsgebiet, usp, zielgruppe FROM briefings WHERE lead_id = :lid LIMIT 1"),
        {"lid": lead_id},
    ).fetchone()

    crawled = db.execute(
        text(
            "SELECT url, h1, h2s, text_preview, full_text "
            "FROM website_content_cache "
            "WHERE customer_id = :lid "
            "AND (url ILIKE :name OR h1 ILIKE :name OR title ILIKE :name) "
            "ORDER BY scraped_at DESC LIMIT 1"
        ),
        {"lid": lead_id, "name": f"%{page_name.lower().replace(' ', '%')}%"},
    ).fetchone()

    old_content = ""
    if crawled:
        old_content = f"URL: {crawled[0]}\nH1: {crawled[1]}\n"
        try:
            h2s = json.loads(crawled[2] or '[]')
            if h2s:
                old_content += "H2: " + " | ".join(h2s[:5]) + "\n"
        except Exception:
            pass
        old_content += f"Text: {(crawled[4] or crawled[3] or '')[:1500]}"

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    gewerk     = briefing[0] if briefing else "Handwerksbetrieb"
    leistungen = briefing[1] if briefing else ""
    region     = briefing[2] if briefing else ""
    usp        = briefing[3] if briefing else ""
    zielgruppe = briefing[4] if briefing else "Privatkunden"

    old_section = f"\nBestehender Content:\n{old_content}" if old_content else "\nKein bestehender Content — komplett neu schreiben."

    prompt = (
        f"Du bist ein professioneller Webtexter fuer lokale Unternehmen.\n"
        f"Schreibe den Content fuer die Seite \"{page_name}\" ({page_type}).\n\n"
        f"Unternehmen: {gewerk}\nLeistungen: {leistungen}\nRegion: {region}\nUSP: {usp}\nZielgruppe: {zielgruppe}\n"
        f"Seite: {page_name}\nZweck: {zweck or 'Informieren und ueberzeugen'}\nKeyword: {keyword or 'nicht definiert'}\n"
        f"{old_section}\n\n"
        "Antworte NUR als JSON:\n"
        '{"headline":"<H1 max 60 Zeichen>","subheadline":"<max 100 Zeichen>","intro":"<2-3 Saetze>",'
        '"sections":[{"titel":"<H2>","text":"<3-5 Saetze>"}],'
        '"cta":"<Call-to-Action>","meta_title":"<max 60>","meta_description":"<max 155>"}'
    )

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 3000, "messages": [{"role": "user", "content": prompt}]},
            )
        resp.raise_for_status()
        raw_text = resp.json()["content"][0]["text"].strip()
        raw_text = re.sub(r'^```json\s*', '', raw_text)
        raw_text = re.sub(r'\s*```$', '', raw_text)
        # JSON repair for truncated responses
        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError:
            repaired = raw_text.rstrip().rstrip(",")
            if repaired.count('"') % 2 != 0:
                repaired += '"'
            open_brackets = repaired.count('[') - repaired.count(']')
            repaired += ']' * max(0, open_brackets)
            open_braces = repaired.count('{') - repaired.count('}')
            repaired += '}' * max(0, open_braces)
            result = json.loads(repaired)
        result["old_content"] = old_content
        result["page_name"] = page_name
        result["page_id"] = page_id
        return result
    except json.JSONDecodeError as e:
        raise HTTPException(500, f"KI-Antwort nicht parsebar: {str(e)[:100]}")
    except Exception as e:
        raise HTTPException(500, f"Content-Generierung fehlgeschlagen: {str(e)[:200]}")


# ── Ground Page Generator (GEO / KI-Optimierung) ─────────────────────────────

def _build_schema_jsonld(
    data: dict,
    company: str,
    city: str,
    website: str,
    phone: str,
    rating: str,
    rating_count: str,
    founded: str,
    employees: str,
    leistungen: str,
) -> dict:
    """Baut das Schema.org LocalBusiness JSON-LD Objekt fuer die Ground Page."""
    schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": company,
        "url": website or "",
        "telephone": phone or "",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": city,
            "addressCountry": "DE",
        },
        "description": data.get("meta_description", ""),
    }

    if rating and rating != "\u2014":
        try:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": str(rating),
                "reviewCount": str(rating_count or "0"),
            }
        except Exception:
            pass

    if founded and founded != "\u2014":
        schema["foundingDate"] = str(founded)

    if employees and employees != "\u2014":
        schema["numberOfEmployees"] = str(employees)

    services = [s.strip() for s in (leistungen or "").split(",") if s.strip()]
    if services:
        schema["hasOfferCatalog"] = {
            "@type": "OfferCatalog",
            "name": "Leistungen",
            "itemListElement": services[:10],
        }

    faq_items = data.get("faq", [])
    if faq_items:
        schema["mainEntity"] = [
            {
                "@type": "Question",
                "name": item.get("frage", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item.get("antwort", ""),
                },
            }
            for item in faq_items
        ]

    return schema


@router.post("/{project_id}/ground-page")
async def generate_ground_page(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """
    Generiert eine vollstaendige Ground Page fuer GEO / KI-Optimierung.
    Enthaelt: Fakten, Leistungen mit Keywords, USP, FAQ, Schema.org Markup.
    """
    import httpx
    import json as _gp_json
    import re as _gp_re
    from sqlalchemy import text as _sql_text

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead = project.lead
    lead_id = project.lead_id

    briefing = db.execute(
        _sql_text("""
            SELECT gewerk, leistungen, einzugsgebiet, usp,
                   zielgruppe, hauptziel, aktionen,
                   telefon, email, gruendungsjahr,
                   mitarbeiterzahl, google_bewertung,
                   google_bewertung_anzahl, zertifikate,
                   auszeichnungen, sonstige_hinweise
            FROM briefings WHERE lead_id = :lid LIMIT 1
        """),
        {"lid": lead_id},
    ).fetchone()

    company    = getattr(lead, "company_name", "") or ""
    city       = getattr(lead, "city", "") or ""
    website    = getattr(lead, "website_url", "") or ""
    phone      = getattr(lead, "phone", "") or ""

    gewerk         = (briefing[0]  if briefing else "") or ""
    leistungen     = (briefing[1]  if briefing else "") or ""
    einzugsgebiet  = (briefing[2]  if briefing else city) or city
    usp            = (briefing[3]  if briefing else "") or ""
    zielgruppe     = (briefing[4]  if briefing else "Privatkunden") or "Privatkunden"
    hauptziel      = (briefing[5]  if briefing else "") or ""
    telefon_b      = (briefing[7]  if briefing else phone) or phone
    gruendungsjahr = (briefing[9]  if briefing else "") or ""
    mitarbeiter    = (briefing[10] if briefing else "") or ""
    g_bewertung    = (briefing[11] if briefing else "") or ""
    g_anzahl       = (briefing[12] if briefing else "") or ""
    zertifikate    = (briefing[13] if briefing else "") or ""
    auszeichnungen = (briefing[14] if briefing else "") or ""
    hinweise       = (briefing[15] if briefing else "") or ""

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    prompt = f"""Du erstellst eine Ground Page fuer ein Handwerksunternehmen.
Eine Ground Page ist eine maschinenlesbare Seite fuer KI-Systeme (ChatGPT, Perplexity, Google AI).
Sie soll das Unternehmen bei relevanten KI-Suchanfragen empfehlenswert machen.

UNTERNEHMENSDATEN:
- Name: {company}
- Branche/Gewerk: {gewerk}
- Stadt: {city}
- Einzugsgebiet: {einzugsgebiet}
- Website: {website}
- Telefon: {telefon_b or phone}
- Gegruendet: {gruendungsjahr or '—'}
- Mitarbeiter: {mitarbeiter or '—'}
- Google-Bewertung: {g_bewertung or '—'} ({g_anzahl or '—'} Bewertungen)
- Zertifikate: {zertifikate or '—'}
- Auszeichnungen: {auszeichnungen or '—'}
- Leistungen: {leistungen}
- USP: {usp}
- Zielgruppe: {zielgruppe}
- Hauptziel: {hauptziel}
- Hinweise: {hinweise}

AUFGABE: Erstelle NUR gueltiges JSON mit GENAU dieser Struktur:

{{
  "page_title": "Ueber uns & Informationen — {company}",
  "meta_description": "<155 Zeichen: Wer wir sind, was wir anbieten, wo wir sind>",
  "intro": "<2-3 Saetze Einleitung, direkt und informativ fuer KI-Systeme>",
  "fakten": {{
    "name": "{company}",
    "branche": "<Gewerk>",
    "standort": "<Stadt, Bundesland, Deutschland>",
    "einzugsgebiet": "<Region mit Staedten>",
    "gegruendet": "<Jahr oder —>",
    "mitarbeiter": "<Zahl oder —>",
    "telefon": "<Telefon>",
    "website": "<URL>",
    "notdienst": "<Ja 24/7 / Ja Mo-Fr / Nein>",
    "sprachen": "Deutsch<, weitere falls bekannt>"
  }},
  "leistungen_keywords": [
    "<Leistung + Stadt, z.B. Wallbox installieren Muenchen>",
    "<weitere 7-9 GEO-optimierte Leistungs-Keywords>"
  ],
  "usp_saetze": [
    "<USP 1 als vollstaendiger Satz fuer KI-Verstaendnis>",
    "<USP 2>",
    "<USP 3>"
  ],
  "faq": [
    {{"frage": "<Frage wie Nutzer sie in ChatGPT eintippen>", "antwort": "<Direkte, informative Antwort mit Firmenname und Kontakt>"}},
    {{"frage": "<Frage 2>", "antwort": "<Antwort 2>"}},
    {{"frage": "<Frage 3>", "antwort": "<Antwort 3>"}},
    {{"frage": "<Frage 4>", "antwort": "<Antwort 4>"}},
    {{"frage": "<Frage 5>", "antwort": "<Antwort 5>"}}
  ],
  "vertrauen": {{
    "google_bewertung": "{g_bewertung or '—'}",
    "google_anzahl": "{g_anzahl or '—'}",
    "zertifikate": "<Zertifikate oder —>",
    "auszeichnungen": "<Auszeichnungen oder —>",
    "seit": "<Gruendungsjahr oder —>",
    "projekte": "<Geschaetzte Projektanzahl falls ableitbar, sonst —>"
  }},
  "schema_type": "LocalBusiness",
  "letzte_aktualisierung": "2026-04"
}}

Gib NUR das JSON zurueck, keine Erklaerung, kein Markdown."""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 3000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        raw = _gp_re.sub(r"^```json\s*", "", raw)
        raw = _gp_re.sub(r"^```\s*", "", raw)
        raw = _gp_re.sub(r"\s*```$", "", raw)
        ground_data = _gp_json.loads(raw)

        schema = _build_schema_jsonld(
            ground_data, company, city, website,
            telefon_b or phone, g_bewertung, g_anzahl,
            gruendungsjahr, mitarbeiter, leistungen,
        )
        ground_data["schema_jsonld"] = schema

        ground_page = db.execute(
            _sql_text("SELECT id FROM sitemap_pages WHERE lead_id = :lid AND page_type = 'ground' LIMIT 1"),
            {"lid": lead_id},
        ).fetchone()

        if ground_page:
            payload = _gp_json.dumps(ground_data, ensure_ascii=False)
            db.execute(
                _sql_text("""
                    UPDATE sitemap_pages
                    SET ki_content = :content,
                        ki_h1 = :h1,
                        ki_meta_title = :meta_t,
                        ki_meta_description = :meta_d,
                        content_generated = TRUE,
                        content_generated_at = NOW()
                    WHERE id = :pid
                """),
                {
                    "content": payload,
                    "h1": (ground_data.get("page_title") or "")[:500],
                    "meta_t": (ground_data.get("page_title") or "")[:70],
                    "meta_d": (ground_data.get("meta_description") or "")[:160],
                    "pid": ground_page[0],
                },
            )
            db.commit()

        return {"ok": True, "ground_page": ground_data}

    except _gp_json.JSONDecodeError:
        raise HTTPException(500, "KI-Antwort konnte nicht verarbeitet werden")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Ground Page Generierung fehlgeschlagen: {str(e)[:300]}")


# ── Link-Resolver ─────────────────────────────────────────────────────────────

import re as _re

def _make_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = slug.replace('ae', 'ae').replace('oe', 'oe').replace('ue', 'ue').replace('ss', 'ss')
    slug = _re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
    SLUG_MAP = {
        'startseite': '', 'home': '', 'impressum': 'impressum',
        'datenschutz': 'datenschutz', 'datenschutzerklaerung': 'datenschutz',
        'agb': 'agb', 'kontakt': 'kontakt', 'contact': 'kontakt',
        'ueber-uns': 'ueber-uns', 'uber-uns': 'ueber-uns', 'about': 'ueber-uns',
        'leistungen': 'leistungen', 'services': 'leistungen',
        'referenzen': 'referenzen', 'galerie': 'galerie',
        'blog': 'blog', 'news': 'news', 'karriere': 'karriere',
        'jobs': 'karriere', 'stellenangebote': 'karriere',
        'preise': 'preise', 'pricing': 'preise',
    }
    return SLUG_MAP.get(slug, slug)


def _build_sitemap_register(project_id: int, db) -> list:
    lead_row = db.execute(text("SELECT lead_id FROM projects WHERE id = :pid"), {"pid": project_id}).fetchone()
    lead_id = lead_row[0] if lead_row else None
    if not lead_id:
        return []
    rows = db.execute(
        text("SELECT id, page_name, page_type, '' as slug FROM sitemap_pages WHERE lead_id = :lid ORDER BY position, id"),
        {"lid": lead_id},
    ).fetchall()
    result = []
    for row in rows:
        page_id, name, ptype, slug = row
        if not slug:
            slug = _make_slug(name)
            db.execute(text("UPDATE sitemap_pages SET slug = :slug WHERE id = :id"), {"slug": slug, "id": page_id})
        result.append({"id": page_id, "name": name, "type": ptype, "slug": slug, "path": f"/{slug}" if slug else "/"})
    db.commit()
    return result


def _resolve_links(html: str, sitemap: list, phone: str = "", email: str = "") -> tuple:
    if not html:
        return html, []
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    report = []
    path_map = {}
    for page in sitemap:
        for kw in [page['name'].lower(), page['slug'].lower(), page['type'].lower()]:
            if kw:
                path_map[kw] = page['path']
    extras = {
        'kontakt': '/kontakt', 'contact': '/kontakt', 'anfrage': '/kontakt',
        'angebot': '/kontakt', 'beratung': '/kontakt', 'termin': '/kontakt',
        'impressum': '/impressum', 'datenschutz': '/datenschutz', 'agb': '/agb',
        'leistungen': '/leistungen', 'services': '/leistungen',
        'referenzen': '/referenzen', 'galerie': '/galerie',
        'startseite': '/', 'home': '/', 'mehr erfahren': '/leistungen',
        'jetzt anfragen': '/kontakt', 'kostenlos': '/kontakt',
    }
    if phone:
        extras['anrufen'] = f'tel:{phone}'
    if email:
        extras['e-mail'] = f'mailto:{email}'
        extras['email'] = f'mailto:{email}'
    path_map.update(extras)

    def _find(text):
        t = text.lower().strip()
        if t in path_map:
            return path_map[t]
        for kw, p in path_map.items():
            if kw in t or t in kw:
                return p
        return None

    for tag in soup.find_all(['a', 'button']):
        txt = tag.get_text(strip=True)
        href = tag.get('href', '')
        is_broken = not href or href in ['#', '#!', 'javascript:void(0)', 'javascript:;'] or href.startswith('http://example') or href == 'URL_HIER'
        resolved = _find(txt)
        if is_broken and resolved:
            if tag.name == 'a':
                tag['href'] = resolved
            else:
                tag['onclick'] = f"window.location.href='{resolved}'"
            status = 'auto_fixed'
        elif is_broken:
            status = 'unresolved'
        else:
            status = 'ok'
        report.append({'text': txt[:50], 'tag': tag.name, 'original': href, 'resolved': resolved, 'href': tag.get('href', tag.get('onclick', '')), 'status': status})

    return str(soup), report


@router.post("/{project_id}/resolve-links")
async def resolve_project_links(
    project_id: int, data: dict,
    db: Session = Depends(get_db), _=Depends(require_any_auth),
):
    html = data.get("html", "")
    page_id = data.get("page_id")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    lead = project.lead
    phone = getattr(lead, 'phone', '') or ''
    email = getattr(lead, 'email', '') or ''
    sitemap = _build_sitemap_register(project_id, db)
    fixed_html, link_report = _resolve_links(html, sitemap, phone, email)
    auto_fixed = sum(1 for r in link_report if r['status'] == 'auto_fixed')
    unresolved = sum(1 for r in link_report if r['status'] == 'unresolved')
    return {
        "html": fixed_html,
        "link_report": link_report,
        "summary": {
            "total": len(link_report),
            "ok": sum(1 for r in link_report if r['status'] == 'ok'),
            "auto_fixed": auto_fixed,
            "unresolved": unresolved,
        },
    }


@router.get("/{project_id}/sitemap-register")
def get_sitemap_register(
    project_id: int, db: Session = Depends(get_db), _=Depends(require_any_auth),
):
    return _build_sitemap_register(project_id, db)


@router.post("/{project_id}/design-json/{page_id}")
async def generate_design_json(
    project_id: int,
    page_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Claude liefert Block-JSON statt rohem HTML."""
    import os, httpx, json, re

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead    = project.lead
    lead_id = project.lead_id

    page = db.execute(
        text("""
            SELECT page_name, page_type, ziel_keyword, zweck,
                   ki_h1, ki_hero_text, ki_abschnitt_text, ki_cta,
                   content_generated
            FROM sitemap_pages WHERE id = :id
        """),
        {"id": page_id},
    ).fetchone()
    if not page:
        raise HTTPException(404, "Seite nicht gefunden")
    (
        page_name, page_type, keyword, zweck,
        ki_h1, ki_hero_text, ki_abschnitt_text, ki_cta,
        ki_content_generated,
    ) = page

    briefing = db.execute(
        text("SELECT gewerk, leistungen, einzugsgebiet, usp FROM briefings WHERE lead_id=:lid LIMIT 1"),
        {"lid": lead_id},
    ).fetchone()

    brand_json = getattr(lead, 'brand_design_json', None)
    brand = json.loads(brand_json) if brand_json else {}

    sitemap = db.execute(
        text("SELECT page_name, '' as slug FROM sitemap_pages WHERE lead_id=:lid ORDER BY position"),
        {"lid": lead_id},
    ).fetchall()
    sitemap_list = [{"name": r[0], "path": f"/{r[1]}" if r[1] else "/"} for r in sitemap]

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    gewerk  = briefing[0] if briefing else "Handwerksbetrieb"
    region  = briefing[2] if briefing else ""
    usp     = briefing[3] if briefing else ""
    company = getattr(lead, 'company_name', '') or ''
    phone   = getattr(lead, 'phone', '') or ''

    # Optimierung #4 — falls bereits KI-Content (Optimierung #3) fuer diese
    # Seite existiert, binden wir ihn in den Prompt ein. Claude erfindet
    # dann nichts Neues, sondern uebernimmt die Texte exakt in die Bloecke.
    ki_content_section = ""
    if ki_h1 or ki_hero_text or ki_abschnitt_text:
        ki_content_section = (
            "\nBEREITS GENERIERTER KI-CONTENT "
            "(diese Texte MUESSEN verwendet werden — nicht neu erfinden):\n"
            f"- H1/Hauptueberschrift: {ki_h1 or '—'}\n"
            f"- Hero-Text: {ki_hero_text or '—'}\n"
            f"- Haupttext: {ki_abschnitt_text or '—'}\n"
            f"- CTA-Text: {ki_cta or 'Jetzt anfragen'}\n"
            "Nutze diese Texte EXAKT fuer die entsprechenden Bloecke. "
            "Nur wenn ein Feld leer ist, erfinde einen passenden Text.\n\n"
        )

    prompt = (
        f"Du bist ein Webdesigner der eine Website-Seite als Block-JSON entwirft.\n\n"
        f"UNTERNEHMEN: {company} | Branche: {gewerk} | Region: {region} | USP: {usp} | Tel: {phone}\n"
        f"SEITE: {page_name} ({page_type}) | Keyword: {keyword or '—'} | Zweck: {zweck or '—'}\n"
        f"STIL: {brand.get('style_keyword','Modern')} | {brand.get('design_brief',{}).get('fuer_ki_prompt','')}\n"
        f"SEITEN FUER LINKS: {json.dumps(sitemap_list, ensure_ascii=False)}\n"
        f"{ki_content_section}"
        "VERFUEGBARE BLOECKE: hero, leistungen-grid, usp-balken, ueber-uns, cta-banner, kontakt-form, footer\n\n"
        "REGELN:\n"
        "- Startseite: hero + usp-balken + leistungen-grid + cta-banner + footer\n"
        "- Kontakt: cta-banner + kontakt-form + footer\n"
        "- Leistung: hero + leistungen-grid + ueber-uns + cta-banner + footer\n"
        "- Alle internen Links NUR aus der Seiten-Liste\n"
        f"- Telefon fuer cta2_link: tel:{phone}\n\n"
        "Antworte NUR als JSON-Array:\n"
        '[{"type":"hero","data":{"headline":"...","subline":"...","cta_text":"Jetzt anfragen",'
        f'"cta_link":"/kontakt","cta2_text":"Anrufen","cta2_link":"tel:{phone}"}}}}'
        ',{"type":"footer","data":{"firma":"' + company + '"}}]'
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 4000,
                      "messages": [{"role": "user", "content": prompt}]},
            )
        resp.raise_for_status()
        text_resp = resp.json()["content"][0]["text"].strip()
        text_resp = re.sub(r'^```json\s*', '', text_resp)
        text_resp = re.sub(r'\s*```$', '', text_resp)
        blocks = json.loads(text_resp)
        if not isinstance(blocks, list):
            raise ValueError("Keine Liste")

        return {
            "page_id":   page_id,
            "page_name": page_name,
            "blocks":    blocks,
            "brand": {
                "primary_color":   getattr(lead, 'brand_primary_color',   '#008EAA'),
                "secondary_color": getattr(lead, 'brand_secondary_color', '#004F59'),
                "font_primary":    getattr(lead, 'brand_font_primary',    'Inter'),
                "border_radius":   brand.get('design_brief', {}).get('radius_token', '8px'),
            }
        }

    except json.JSONDecodeError as e:
        raise HTTPException(500, f"JSON-Parse-Fehler: {str(e)[:100]}")
    except Exception as e:
        raise HTTPException(500, f"Fehler: {str(e)[:200]}")

# sitemap-suggest removed — use /api/sitemap/{lead_id}/generate instead


# ── Netlify Kunden-Account ────────────────────────────────────────────────────

@router.get("/{project_id}/netlify/status")
async def netlify_customer_status(
    project_id: int, db: Session = Depends(get_db), _=Depends(require_any_auth)
):
    """Gibt Netlify-Deploy-Status fuer ein Kundenprojekt zurueck.

    Seit der Vereinheitlichung (Bug #1) liest `has_token` NICHT mehr aus
    `projects.netlify_token`, sondern prueft die zentrale Env-Var
    `NETLIFY_API_TOKEN`. Die DB-Spalte bleibt bestehen, wird aber ignoriert.
    """
    row = db.execute(
        text("SELECT netlify_site_id, netlify_site_url FROM projects WHERE id=:id"),
        {"id": project_id},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Projekt nicht gefunden")
    has_token = bool((os.getenv("NETLIFY_API_TOKEN") or "").strip())
    return {
        "has_token": has_token,
        "site_id":   row[0],
        "url":       row[1],
        "state":     "ready" if row[1] else None,
    }


@router.post("/{project_id}/netlify/save-token")
async def netlify_save_token(
    project_id: int, data: dict,
    db: Session = Depends(get_db), _=Depends(require_any_auth),
):
    """DEPRECATED (Bug #1 Fix).

    Projekt-spezifische Netlify-Tokens werden nicht mehr unterstuetzt. Der
    Token wird jetzt zentral ueber die Env-Variable `NETLIFY_API_TOKEN`
    verwaltet (siehe `services/netlify_service.py`). Dieser Endpunkt bleibt
    nur noch existent, um alte Frontend-Calls mit einer klaren
    Fehlermeldung abzufangen.
    """
    raise HTTPException(
        status_code=410,
        detail=(
            "Dieser Endpunkt ist deaktiviert. Projekt-spezifische "
            "Netlify-Tokens werden nicht mehr unterstuetzt — der Token "
            "wird zentral ueber die Umgebungsvariable NETLIFY_API_TOKEN "
            "auf dem Backend gesetzt."
        ),
    )


@router.post("/{project_id}/netlify/customer-create-site")
async def netlify_customer_create_site(
    project_id: int,
    db: Session = Depends(get_db), _=Depends(require_any_auth),
):
    """Erstellt eine Netlify-Site fuer ein Kundenprojekt. Token wird aus Env geladen."""
    from services.netlify_service import create_site

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead = project.lead if project else None
    name = (getattr(lead, "company_name", "") or f"projekt-{project_id}").lower().replace(" ", "-")
    import re as _r
    name = _r.sub(r"[^a-z0-9-]", "", name)[:40]

    try:
        result = await create_site(name)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Netlify customer-create-site failed (project {project_id}): {e}")
        raise HTTPException(502, f"Netlify-Site konnte nicht angelegt werden: {str(e)[:200]}")

    site_id  = result.get("site_id")
    site_url = result.get("site_url", "")

    db.execute(
        text("UPDATE projects SET netlify_site_id=:sid, netlify_site_url=:url WHERE id=:id"),
        {"sid": site_id, "url": site_url, "id": project_id},
    )
    db.commit()
    return {"site_id": site_id, "url": site_url, "name": result.get("name")}


@router.post("/{project_id}/netlify/customer-deploy")
async def netlify_customer_deploy(
    project_id: int, data: dict,
    db: Session = Depends(get_db), _=Depends(require_any_auth),
):
    """Deployt HTML fuer ein Kundenprojekt auf die bereits angelegte Site.
    Token wird aus Env geladen, nur `netlify_site_id` wird aus der DB gelesen.
    """
    from services.netlify_service import deploy_html

    row = db.execute(
        text("SELECT netlify_site_id FROM projects WHERE id=:id"),
        {"id": project_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(400, "Keine Netlify-Site fuer dieses Projekt angelegt")
    site_id = row[0]

    html = (data.get("html") or "").strip()
    if not html:
        raise HTTPException(400, "HTML fehlt")

    try:
        result = await deploy_html(site_id=site_id, html=html)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Netlify customer-deploy failed (project {project_id}): {e}")
        raise HTTPException(502, f"Deploy fehlgeschlagen: {str(e)[:200]}")

    return {
        "deploy_id":  result.get("deploy_id"),
        "deploy_url": result.get("deploy_url"),
        "state":      result.get("state"),
    }


@router.post("/{project_id}/netlify/set-domain")
async def netlify_set_domain(
    project_id: int, data: dict,
    db: Session = Depends(get_db), _=Depends(require_any_auth),
):
    """Setzt eine Custom-Domain fuer eine Kundenprojekt-Site.
    Token wird aus Env geladen, nur `netlify_site_id` wird aus der DB gelesen.
    """
    from services.netlify_service import set_custom_domain

    row = db.execute(
        text("SELECT netlify_site_id FROM projects WHERE id=:id"),
        {"id": project_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(400, "Keine Netlify-Site fuer dieses Projekt angelegt")
    site_id = row[0]

    domain = (data.get("domain") or "").strip()
    if not domain:
        raise HTTPException(400, "Domain fehlt")

    try:
        result = await set_custom_domain(site_id, domain)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Netlify set-domain failed (project {project_id}): {e}")
        raise HTTPException(502, f"Domain konnte nicht gesetzt werden: {str(e)[:200]}")

    return {
        "cname_target":        (result.get("ssl_url") or "").replace("https://", ""),
        "domain":              result.get("custom_domain", domain),
        "required_dns_record": result.get("required_dns_record"),
    }


# ── Tor 1: Admin-Freigabe fuer Briefing ───────────────────────────────────────

@router.post("/{project_id}/approve-briefing")
def approve_briefing(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Admin gibt das eingereichte Briefing frei und entsperrt Phase 2.

    Setzt briefing_approved_at + briefing_approved_by auf dem Projekt und
    startet die KI-Sitemap-Generierung als Background-Thread (direkter
    Funktionsaufruf auf generate_sitemap_impl, kein HTTP-Roundtrip, keine
    interne Auth-Umgehung). Der Admin landet sofort wieder im UI, die
    Sitemap erscheint dort nach wenigen Sekunden durch normales Polling.
    """
    import threading
    from datetime import datetime as _dt
    from database import SessionLocal as _SL

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    if not project.briefing_submitted_at:
        raise HTTPException(
            400,
            "Das Briefing fuer dieses Projekt wurde noch nicht eingereicht. "
            "Warte bis der Kunde es abschickt.",
        )

    # Idempotent: zweite Freigabe ist No-Op, aber gibt den aktuellen Stand zurueck.
    already_approved = project.briefing_approved_at is not None
    if not already_approved:
        project.briefing_approved_at = _dt.utcnow()
        project.briefing_approved_by = getattr(current_user, "email", None) or str(
            getattr(current_user, "id", "admin")
        )
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"approve_briefing Commit fehlgeschlagen: {e}")
            raise HTTPException(500, f"Freigabe fehlgeschlagen: {str(e)[:200]}")

    # Auto-Start der Sitemap-KI in einem daemon-Thread. Nur beim ERSTEN
    # Approve — Wiederholungen triggern nichts Neues.
    sitemap_started = False
    lead_id = project.lead_id
    if lead_id and not already_approved:
        def _auto_start_sitemap(lid: int):
            import time as _time
            _time.sleep(2)  # kurz warten, damit der Frontend-UI-Refresh durch ist
            _db = _SL()
            try:
                from routers.sitemap import generate_sitemap_impl
                result = generate_sitemap_impl(lid, _db)
                logger.info(
                    f"Auto-Sitemap nach Briefing-Freigabe: Lead {lid} — "
                    f"{len(result.get('pages', []))} Seiten, source={result.get('source')}"
                )
            except Exception as e:
                logger.error(f"Auto-Sitemap fehlgeschlagen fuer Lead {lid}: {e}")
            finally:
                _db.close()

        threading.Thread(
            target=_auto_start_sitemap, args=(lead_id,), daemon=True
        ).start()
        sitemap_started = True
        logger.info(
            f"Briefing freigegeben: Projekt {project_id} (Lead {lead_id}) "
            f"durch {project.briefing_approved_by} — Auto-Sitemap geplant"
        )

    return {
        "approved": True,
        "already_approved": already_approved,
        "sitemap_started": sitemap_started,
        "briefing_approved_at": project.briefing_approved_at.isoformat(),
        "briefing_approved_by": project.briefing_approved_by,
    }


# ── Tor 2: Content-Freigabe durch den Kunden (Baustein 3) ─────────────────────
#
# Flow:
#   1. Admin ruft POST /request-content-approval → Token + Mail + sent_at
#   2a. Kunde klickt Link aus der Mail → GET /approve-content/{token}
#   2b. Kunde loggt ins Portal ein → POST /approve-content-portal
#   3. Beide Wege setzen content_approved_at/_by, benachrichtigen Admin und
#      setzen project.status auf "phase_4" (Design-Phase).


def _get_admin_notification_email_proj(db: Session) -> Optional[str]:
    """Admin-Mail fuer Content-Approval-Benachrichtigungen.

    Dreistufige Kaskade analog zu briefings._get_admin_notification_email:
    SystemSettings-Key 'admin_notification_email' → env ADMIN_NOTIFICATION_EMAIL
    → erster superadmin-User als Fallback.
    """
    try:
        row = db.execute(
            text("SELECT value FROM system_settings WHERE key = :k"),
            {"k": "admin_notification_email"},
        ).fetchone()
        if row and row[0]:
            return row[0].strip()
    except Exception:
        pass
    env_val = os.environ.get("ADMIN_NOTIFICATION_EMAIL", "").strip()
    if env_val:
        return env_val
    try:
        row = db.execute(
            text("SELECT email FROM users WHERE role = 'superadmin' ORDER BY id LIMIT 1")
        ).fetchone()
        if row and row[0]:
            return row[0]
    except Exception:
        pass
    return None


def _send_content_approval_admin_notification(
    project_id: int,
    lead_id: Optional[int],
    company_name: str,
    channel: str,
    db: Session,
) -> None:
    """Informiere den Admin dass der Kunde freigegeben hat. Best-effort —
    Fehler werden geloggt, kein Raise (damit der eigentliche Freigabe-
    Pfad nicht wegen Mail-Problemen scheitert)."""
    try:
        to = _get_admin_notification_email_proj(db)
        if not to:
            logger.warning(
                "Content-Approval: Keine Admin-E-Mail konfiguriert — "
                "Benachrichtigung uebersprungen."
            )
            return

        from automations.email_templates import render_template
        from datetime import datetime as _dt
        rendered = render_template("content_approval_admin_notification", {
            "company_name":     company_name or f"Lead #{lead_id or '?'}",
            "lead_id":          lead_id or "—",
            "project_id":       project_id,
            "approved_at":      _dt.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "approval_channel": channel,
        })
        # Plain-Text-Body des Templates in minimales HTML wrappen,
        # damit die kanonische send_email einen html_body bekommt.
        body_text = rendered["body"]
        html_body = (
            "<pre style=\"font-family:-apple-system,sans-serif;font-size:14px;"
            "white-space:pre-wrap\">" + body_text + "</pre>"
        )

        from services.email import send_email
        ok = send_email(
            to_email=to,
            subject=rendered["subject"],
            html_body=html_body,
            text_body=body_text,
        )
        if ok:
            logger.info(
                f"Content-Approval: Admin-Benachrichtigung an {to} (Projekt {project_id}, Kanal: {channel})"
            )
        else:
            logger.warning(
                f"Content-Approval: Admin-Mail an {to} fehlgeschlagen (Projekt {project_id}) — "
                "SMTP-Konfiguration pruefen."
            )
    except Exception as e:
        logger.error(f"Content-Approval: Admin-Mail fehlgeschlagen: {e}")


def _advance_project_to_design_phase(project: Project, db: Session) -> str:
    """Nach Content-Freigabe: project.status auf Design-Phase setzen.

    Minimal: Status auf "phase_4" setzen. Kein expliziter Claude-Call fuer
    die Design-Generierung — der Admin triggert das manuell aus dem UI,
    wie vor Baustein 3 auch. Die Freigabe dient als Statussignal im
    ProzessFlow, nicht als Auto-Orchestrator.
    """
    prev_status = project.status or "phase_1"
    # Nur vorwaertsbewegen, nie zurueck
    try:
        num = int(str(prev_status).replace("phase_", "")) if "phase_" in str(prev_status) else 3
    except (ValueError, TypeError):
        num = 3
    next_num = max(num + 1, 4)
    project.status = f"phase_{next_num}"
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"_advance_project_to_design_phase Commit-Fehler: {e}")
        return prev_status
    return project.status


@router.post("/{project_id}/request-content-approval")
def request_content_approval(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Admin schickt dem Kunden einen Freigabe-Link fuer die Content-Phase.

    Generiert einen tokenisierten Link und schickt ihn per E-Mail an die
    auf dem Lead hinterlegte Adresse. Der Token ist single-use: der public
    Endpoint GET /approve-content/{token} setzt ihn beim erfolgreichen
    Approve auf NULL, damit der Link nicht erneut verwendet werden kann.
    """
    from services.qr_service import generate_token
    from datetime import datetime as _dt

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    if project.content_approved_at is not None:
        raise HTTPException(
            400,
            "Content wurde bereits freigegeben — ein erneuter Request ist nicht noetig.",
        )

    # Neuen Token generieren (ueberschreibt alte, noch ungenutzte Tokens,
    # damit ein erneutes Senden den alten Link invalidiert — wichtiger
    # Security-Punkt falls die alte Mail abgefangen worden waere).
    token = generate_token()
    project.content_approval_token = token
    project.content_approval_sent_at = _dt.utcnow()
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"request_content_approval Commit fehlgeschlagen: {e}")
        raise HTTPException(500, f"Freigabe-Request fehlgeschlagen: {str(e)[:200]}")

    frontend_url = os.environ.get("FRONTEND_URL", "https://kompagnon-frontend.onrender.com")
    approval_url = f"{frontend_url}/approve-content/{token}"

    # Empfaenger: Lead.email
    lead = db.query(Lead).filter(Lead.id == project.lead_id).first() if project.lead_id else None
    email_to = (lead.email if lead else None) or ""
    contact_name = (lead.contact_name if lead else None) or (
        lead.display_name if lead else None
    ) or (lead.company_name if lead else None) or "liebe Kundin / lieber Kunde"
    company = (lead.company_name or lead.display_name or "") if lead else ""

    email_sent = False
    if email_to:
        try:
            from automations.email_templates import render_template
            rendered = render_template("content_approval_request", {
                "company_name": company or f"Lead #{project.lead_id or '?'}",
                "contact_name": contact_name,
                "approval_url": approval_url,
            })
            body_text = rendered["body"]
            html_body = (
                "<pre style=\"font-family:-apple-system,sans-serif;font-size:14px;"
                "white-space:pre-wrap\">" + body_text + "</pre>"
            )
            from services.email import send_email
            email_sent = send_email(
                to_email=email_to,
                subject=rendered["subject"],
                html_body=html_body,
                text_body=body_text,
            )
            if email_sent:
                logger.info(
                    f"Content-Approval: Request-Mail an {email_to} (Projekt {project_id})"
                )
            else:
                logger.warning(
                    f"Content-Approval: Request-Mail an {email_to} fehlgeschlagen "
                    f"(Projekt {project_id}) — SMTP-Konfiguration pruefen."
                )
        except Exception as e:
            logger.error(
                f"Content-Approval: Request-Mail an {email_to} fehlgeschlagen: {e}"
            )
    else:
        logger.warning(
            f"Content-Approval: Lead {project.lead_id} hat keine E-Mail — "
            f"Token wurde generiert, aber keine Mail verschickt."
        )

    return {
        "token_generated": True,
        "email_sent": email_sent,
        "approval_url": approval_url,
        "content_approval_sent_at": project.content_approval_sent_at.isoformat(),
    }


@router.get("/approve-content/{token}")
def approve_content_via_token(
    token: str,
    db: Session = Depends(get_db),
):
    """Oeffentlicher Endpoint (kein Auth): Kunde klickt Link aus Mail.

    Der Token ist single-use — nach erfolgreicher Freigabe wird er auf
    NULL gesetzt, sodass ein erneuter Aufruf mit demselben Token 404
    liefert ("ungueltig oder bereits verwendet"). Das Frontend zeigt
    darauf eine klare Fehlermeldung.
    """
    from datetime import datetime as _dt

    if not token or len(token) < 8:
        raise HTTPException(404, "Dieser Link ist ungueltig oder wurde bereits verwendet.")

    project = db.query(Project).filter(
        Project.content_approval_token == token,
        Project.content_approved_at.is_(None),
    ).first()
    if not project:
        raise HTTPException(404, "Dieser Link ist ungueltig oder wurde bereits verwendet.")

    project.content_approved_at = _dt.utcnow()
    project.content_approved_by = "kunde_via_email"
    project.content_approval_token = None  # Token einmalig
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"approve_content_via_token Commit fehlgeschlagen: {e}")
        raise HTTPException(500, f"Freigabe fehlgeschlagen: {str(e)[:200]}")

    # Projekt-Status in Design-Phase schieben
    new_status = _advance_project_to_design_phase(project, db)

    # Admin informieren
    lead = db.query(Lead).filter(Lead.id == project.lead_id).first() if project.lead_id else None
    company = (lead.company_name or lead.display_name or "") if lead else ""
    _send_content_approval_admin_notification(
        project_id=project.id,
        lead_id=project.lead_id,
        company_name=company,
        channel="E-Mail-Link",
        db=db,
    )

    return {
        "approved": True,
        "company_name": company or "Ihr Projekt",
        "project_id": project.id,
        "new_status": new_status,
    }


@router.post("/{project_id}/approve-content-portal")
def approve_content_via_portal(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_auth),
):
    """Portal-Endpoint: der eingeloggte Kunde gibt die Inhalte frei.

    Authentifizierter Gegenpart zum tokenisierten Link — nur Nutzer mit
    role='kunde' UND passender lead_id duerfen das Projekt ihres eigenen
    Leads freigeben.
    """
    from datetime import datetime as _dt

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    user_role = getattr(current_user, "role", None)
    user_lead_id = getattr(current_user, "lead_id", None)
    if user_role != "kunde":
        raise HTTPException(
            403,
            "Nur Kunden koennen ueber das Portal freigeben. Admins nutzen die E-Mail-Anfrage.",
        )
    if not user_lead_id or user_lead_id != project.lead_id:
        raise HTTPException(403, "Kein Zugriff auf dieses Projekt.")

    if project.content_approved_at is not None:
        return {
            "approved": True,
            "already_approved": True,
            "content_approved_at": project.content_approved_at.isoformat(),
            "content_approved_by": project.content_approved_by,
        }

    project.content_approved_at = _dt.utcnow()
    project.content_approved_by = getattr(current_user, "email", None) or "kunde_via_portal"
    project.content_approval_token = None  # falls noch ein Token offen war
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"approve_content_via_portal Commit fehlgeschlagen: {e}")
        raise HTTPException(500, f"Freigabe fehlgeschlagen: {str(e)[:200]}")

    new_status = _advance_project_to_design_phase(project, db)

    lead = db.query(Lead).filter(Lead.id == project.lead_id).first() if project.lead_id else None
    company = (lead.company_name or lead.display_name or "") if lead else ""
    _send_content_approval_admin_notification(
        project_id=project.id,
        lead_id=project.lead_id,
        company_name=company,
        channel="Kundenportal",
        db=db,
    )

    return {
        "approved": True,
        "already_approved": False,
        "content_approved_at": project.content_approved_at.isoformat(),
        "content_approved_by": project.content_approved_by,
        "new_status": new_status,
    }
