"""Ein Projekt entsteht und geht live (L-25).

**Warum eigene Datei, 22.08.2026.** `routers/projects.py` hatte 1.919 Zeilen
— und das **nach** der ersten Aufteilung im August, bei der schon
`projects_netlify`, `projects_content`, `projects_sichtbarkeit` und
`projects_public` entstanden sind. Drei Funktionen, zusammen 501 Zeilen: aus einem Betrieb ein Projekt
machen, die Go-live-Kette abarbeiten und Probedaten anlegen. Die
Go-live-Kette allein ist 271 Zeilen.

Transitiv gemessen samt Modulkonstanten: Geteilt ist nur `logger`. Der
Router kommt wie drueben aus `projects_router.py` — dort stehen die drei
Router mit ihren verschiedenen Sperren an einer Stelle.
"""
import os
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from database import Customer
from database import Lead
from database import Project
from database import ProjectScrapeJob
from database import get_db
from datetime import datetime
from routers.content_scraper_router import _run_content_scrape
from services.audit_pagespeed import api_key as pagespeed_api_key
from services.base_urls import public_base_url
from sqlalchemy.orm import Session
import logging

from routers.projects_router import router

# Aus der Erhebung geholt statt kopiert: Die Go-live-Kette macht das
# Bildschirmfoto **danach** — dieselbe Route, die der Innendienst
# auch von Hand ausloest.
from routers.projects_erhebung import screenshot_after
from services import produktkatalog

logger = logging.getLogger(__name__)


@router.post("/from-lead/{lead_id}", status_code=201)
def create_project_from_lead(
    lead_id: int,
    background_tasks: BackgroundTasks,
    body: dict = Body(default={}),
    db: Session = Depends(get_db),
):
    """
    Create a project from any lead (Nutzerkartei).

    Optional body fields (all skipped if omitted / invalid, falling back
    to DB defaults):
      - package_type:  'starter' | 'kompagnon' | 'premium'
      - project_type:  'standard' | 'impuls'
      - isb_antrag_datum:       ISO date "YYYY-MM-DD"
      - isb_bewilligung_datum:  ISO date "YYYY-MM-DD"
      - foerder_volumen:        number (€)
      - isb_tagewerke:          integer

    - 404 if lead not found
    - 409 if a project for this lead already exists
    - 201 + project JSON on success
    """
    # 1. Resolve lead
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    # 2. Guard against duplicates — return the existing project_id so the
    # caller can navigate to it instead of guessing or 404'ing.
    existing = db.query(Project).filter(Project.lead_id == lead_id).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "PROJECT_EXISTS",
                "message": "Für diesen Lead existiert bereits ein Projekt",
                "project_id": existing.id,
                "lead_id": lead_id,
            },
        )

    # 3. Guard: Website-URL ist Pflicht für Projekterstellung
    if not lead.website_url or not lead.website_url.strip():
        raise HTTPException(
            status_code=422,
            detail={
                "code": "MISSING_WEBSITE_URL",
                "message": "Projekterstellung nicht möglich: Für diesen Kunden ist keine Website-Domain hinterlegt. Bitte zuerst die Domain im Kundenprofil ergänzen.",
                "lead_id": lead_id,
                "field": "website_url",
            }
        )

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
    # Optional fields from body — whitelist + parse, fall back to DB defaults.
    body = body or {}
    # Gegen den Katalog pruefen, nicht gegen eine Liste im Quelltext: Hier
    # stand bis zum 23.08.2026 `("starter", "kompagnon", "premium")`. Beim
    # Wechsel auf die Websprint-Produkte waere daraus eine stille Falle
    # geworden — die neue Kennung faellt durch, die Angabe wird `None`, und
    # das Projekt bekommt den Spaltenstandard (L-97).
    package_type = body.get("package_type")
    if package_type not in produktkatalog.bekannte_slugs(db):
        package_type = None
    project_type = body.get("project_type")
    if project_type not in ("standard", "impuls"):
        project_type = None

    def _parse_date(val):
        if not val:
            return None
        try:
            return datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def _parse_num(val):
        if val in (None, "", "null"):
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _parse_int(val):
        if val in (None, "", "null"):
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    isb_antrag = _parse_date(body.get("isb_antrag_datum"))
    isb_bewilligung = _parse_date(body.get("isb_bewilligung_datum"))
    foerder_volumen = _parse_num(body.get("foerder_volumen"))
    isb_tagewerke = _parse_int(body.get("isb_tagewerke"))

    # Set extra columns via setattr so missing ORM fields don't crash
    extras = [
        ("company_name", company_name),
        ("website_url",  lead.website_url),
        ("contact_name", lead.contact_name),
        ("contact_email", lead.email),
    ]
    if package_type:
        extras.append(("package_type", package_type))
    if project_type:
        extras.append(("project_type", project_type))
    if isb_antrag is not None:
        extras.append(("isb_antrag_datum", isb_antrag))
    if isb_bewilligung is not None:
        extras.append(("isb_bewilligung_datum", isb_bewilligung))
    if foerder_volumen is not None:
        extras.append(("foerder_volumen", foerder_volumen))
    if isb_tagewerke is not None:
        extras.append(("isb_tagewerke", isb_tagewerke))
    for col, val in extras:
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
                api_key = pagespeed_api_key()

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
                    portal_url = public_base_url() + "/portal/login"

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

                    ok = send_email(
                        to_email  = customer_email,
                        subject   = f"🚀 Ihre Website ist live — {company}",
                        html_body = html,
                    )
                    if ok:
                        logger.info(f"Go-Live: E-Mail gesendet an {customer_email}")
                    else:
                        logger.warning(f"Go-Live: E-Mail an {customer_email} fehlgeschlagen")
                except Exception as e:
                    logger.error(f"Go-Live: E-Mail Fehler: {e}")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Go-Live Automation Fehler: {e}")


@router.post("/seed")
def seed_projects(db: Session = Depends(get_db)):
    """
    Admin: Create projects from leads that have none yet.
    Priority: status='won' leads first, then all others as fallback
    if projects table is completely empty.
    """
    project_count = db.query(Project).count()
    # Dieselbe Korrektur wie in `automations.py`: ueber die Phase statt ueber
    # einen einzelnen Statuswert. Ein von Hand auf „Kunde" gesetzter Betrieb
    # bekam sonst nie ein Projekt vorgeschlagen.
    from services.lebenszyklus import KUNDE

    won_leads = db.query(Lead).filter(
        Lead.lifecycle_phase == KUNDE,
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
