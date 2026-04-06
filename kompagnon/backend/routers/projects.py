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
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
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
    lead_id: int = None
    name: str = ""
    customer_name: str = ""
    status: str = ""
    current_phase: int = 1
    website_url: str = ""
    fixed_price: float = 2000
    actual_hours: float = 0
    hourly_rate: float = 45
    ai_tool_costs: float = 50
    margin_percent: float = 0
    scope_creep_flags: int = 0
    start_date: datetime = None
    target_go_live: datetime = None
    actual_go_live: datetime = None
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
    email_notifications_enabled: bool = None
    customer_email: str = None


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
    try:
        rows = db.execute(
            text(
                "SELECT id, lead_id, status, fixed_price, actual_hours, hourly_rate, "
                "ai_tool_costs, margin_percent, scope_creep_flags, created_at, "
                "company_name, website_url, contact_name "
                "FROM projects "
                + ("WHERE status = :status " if status else "")
                + "ORDER BY id DESC LIMIT :limit OFFSET :skip"
            ),
            {"status": status, "limit": limit, "skip": skip} if status else {"limit": limit, "skip": skip},
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
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get project detail via raw SQL — bypasses ORM column mapping issues."""
    try:
        row = db.execute(
            text(
                "SELECT id, lead_id, status, fixed_price, actual_hours, hourly_rate, "
                "ai_tool_costs, margin_percent, scope_creep_flags, start_date, "
                "target_go_live, created_at, company_name, website_url, contact_name "
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
    }


@router.put("/{project_id}")
def update_project(
    project_id: int,
    body: ProjectUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Update redesign fields on a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    old_status = project.status

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)

    # E-Mail bei Phasenwechsel
    new_status = project.status
    notifications_on = getattr(project, "email_notifications_enabled", True)
    to_email = getattr(project, "customer_email", None) or ""
    if (
        notifications_on
        and new_status != old_status
        and new_status
        and new_status.startswith("phase_")
        and to_email
    ):
        try:
            phase_num = int(new_status.split("_")[1])
            company = getattr(project, "company_name", "") or f"Projekt #{project.id}"
            send_phase_change_email(to=to_email, company=company, phase=phase_num)
        except Exception as exc:
            logger.warning(f"Phase-E-Mail fehlgeschlagen für Projekt {project_id}: {exc}")

    # Auto-Screenshot "after" beim Wechsel auf Go-Live (phase_6)
    if new_status == "phase_6" and old_status != "phase_6":
        background_tasks.add_task(_capture_project_screenshot_after, project_id)

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
    _: object = Depends(get_current_user),
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
            wordpress_hosting   = :wordpress_hosting,
            is_wordpress        = :is_wordpress,
            hosting_checked_at  = NOW()
        WHERE id = :project_id
    """), {
        "project_id":       project_id,
        "hosting_provider": data.get("hosting_provider"),
        "hosting_org":      data.get("hosting_org"),
        "hosting_ip":       data.get("ip_address"),
        "hosting_country":  data.get("country"),
        "dns_provider":     data.get("dns_provider"),
        "nameservers":      ",".join(data.get("nameservers") or []) or None,
        "domain_registrar": data.get("registrar"),
        "domain_created":   data.get("domain_created"),
        "domain_expires":   data.get("domain_expires"),
        "server_software":  data.get("server_software"),
        "wordpress_hosting": data.get("wordpress_hosting"),
        "is_wordpress":     data.get("is_wordpress"),
    })
    db.commit()

    row = db.execute(text("""
        SELECT hosting_provider, hosting_org, hosting_ip, hosting_country,
               dns_provider, nameservers, domain_registrar, domain_created,
               domain_expires, server_software, wordpress_hosting, is_wordpress,
               hosting_checked_at, website_url
        FROM projects WHERE id = :id
    """), {"id": project_id}).mappings().first()

    return dict(row)


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
               hosting_checked_at, website_url
        FROM projects WHERE id = :id
    """), {"id": project_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    return dict(row)
