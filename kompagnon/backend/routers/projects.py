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
# Die Go-live-Kette liegt seit dem 22.08.2026 in `projects_anlegen.py`
# (L-25) — 271 Zeilen. Zwei Routen hier stossen sie an: der
# Phasenwechsel und der Handausloeser.
from routers.projects_anlegen import _golive_automation
import logging
import threading
import os
import json as _json_mod
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from services.ki_aufruf import frag_modell

logger = logging.getLogger(__name__)






# `_fernet_available()` stand hier und ist am 23.08.2026 entfallen (L-25):
# kein Aufruf im Bestand, kein Import von aussen. Sie meldete, ob
# `CREDENTIALS_KEY` gesetzt ist — das beantwortet inzwischen der Startbericht.


from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from database import Project, ProjectChecklist, TimeTracking, Lead, Customer, ProjectScrapeJob, get_db, SessionLocal
from services.margin_calculator import MarginCalculator
from services.base_urls import public_base_url
from routers.auth_router import (
    require_admin,
    require_any_auth,
    require_innendienst,
    get_current_user,
)
from automations.scheduler import (
    get_scheduler,
    job_tag_5_followup,
    job_tag_14_funktionscheck,
    job_tag_21_bewertungsanfrage,
    job_tag_30_geo_check,
    job_tag_30_upsell,
)

logger = logging.getLogger(__name__)

# Eine Erlaubnisliste je Route ist die falsche Richtung: Wer eine Route
# hinzufügt und die Abhängigkeit vergisst, öffnet sie. Genau das war hier
# passiert — 19 von 60 Routen hingen ohne Anmeldung, darunter das Schreiben
# beliebiger Projektspalten und das Auslösen der Automatik. Deshalb hängt die
# Anmeldung jetzt am Router, und was öffentlich sein muss, steht unten
# ausdrücklich im `public_router`. Gleiche Bauart wie in `routers/leads.py`.
# Die drei Router stehen seit dem 22.08.2026 in `projects_router.py` — sie
# werden von den herausgeloesten Modulen mitbenutzt (L-25). Ein Router je
# Zugangsart, damit nicht zwei auf derselben Adresse liegen.
from routers.projects_router import kunden_router, public_router, router
# Die Datenformate stehen seit dem 23.08.2026 in `projects_modelle.py`
# (L-25) — 165 Zeilen ohne Logik, die man nachschlaegt statt durchblaettert.
from routers.projects_modelle import (  # noqa: F401
    ChecklistItemResponse, ChecklistItemUpdate, LeistungsseitenCreate,
    MarginResponse, PhaseChangeRequest, ProjectResponse,
    ProjectUpdateRequest, TimeLogRequest,
)
# Gemeinsame Helfer aller Module unter `/api/projects` — seit dem
# 22.08.2026 in `projects_helfer.py`, damit die herausgeloesten Module
# nicht an dieser Datei haengen (L-25).
from routers.projects_helfer import (  # noqa: F401
    _get_fernet,
    eigenes_projekt_pruefen,
    safe_json_parse,
)



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




@kunden_router.get("/")
def list_projects(
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(100),
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
                # Der Status kommt **vom Server**, nicht aus der Oberflaeche:
                # Die Schwellen (78 % / 70 %) stehen in `MarginCalculator`,
                # und eine zweite Quelle fuer dieselbe Zahl ist der Fehler,
                # der bei den Paketpreisen schon einmal zugeschlagen hat.
                # Gerechnet wird hier nichts — nur der gespeicherte Wert
                # eingeordnet; `calculate_margin` je Zeile waere bei 200
                # Projekten eine Abfrage je Projekt.
                # Die Stunden werden **mitgegeben**: Ohne erfasste Zeit ist
                # die Marge keine Messung, sondern der Festpreis minus
                # Werkzeugkosten — und ein gruenes Abzeichen darueber waere
                # eine Behauptung (26.08.2026, L-105).
                'margin_status': MarginCalculator.status_fuer(row[7] or 0,
                                                             row[4] or 0),
                'scope_creep_flags': row[8] or 0,
                'created_at': str(row[9])[:10] if row[9] else '',
            })
        except Exception:
            continue
    return result


def _content_analysiert_am(db, lead_id):
    """Der juengste Auslesezeitpunkt des Crawlers fuer diesen Betrieb.

    `None`, wenn nie gelesen wurde — und das ist keine Aussage ueber die
    Website, sondern ueber uns. Ein Fehler beim Lesen ergibt ebenfalls `None`
    und eine Protokollzeile: Ein Zeitstempel zu erfinden waere schlimmer als
    keiner.
    """
    if not lead_id:
        return None
    try:
        zeile = db.execute(
            text("SELECT MAX(scraped_at) FROM website_content_cache "
                 "WHERE customer_id = :c"),
            {"c": lead_id},
        ).fetchone()
    except Exception as fehler:      # noqa: BLE001
        logger.warning("Auslesezeitpunkt fuer Betrieb %s nicht lesbar: %s",
                       lead_id, fehler)
        return None
    return zeile[0].isoformat() if zeile and zeile[0] else None


@kunden_router.get("/{project_id}")
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
                "gbp_checklist_json, briefing_approved_at, "
                "netlify_site_url, netlify_last_deploy, steps_confirmed "
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
    eigenes_projekt_pruefen(db, project_id, current_user)

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
        'briefing_approved_at':     row[25].isoformat() if row[25] else None,
        'netlify_site_url':         row[26] or None,
        'netlify_last_deploy':      row[27].isoformat() if row[27] else None,
        'steps_confirmed':          row[28] or '{}',
        # **Wann der Crawler diese Website zuletzt ausgelesen hat.**
        #
        # Vorher las die Prozesskette `project.scrape_full_at` — ein Feld, das
        # diese Antwort **nie enthielt**. Die Kette bekam `undefined` und der
        # Schritt „Content-Vollanalyse" stand ewig auf offen, obwohl der Lauf
        # (damals als Hintergrundaufgabe beim Anlegen) tatsaechlich
        # stattgefunden hatte. Ein Wert, der nicht ueber die Schnittstelle
        # geht, ist fuer die Oberflaeche nicht vorhanden.
        #
        # Seit dem 26.08.2026 gibt es nur noch **einen** Scraper, und das ist
        # der, den die Oberflaeche ruft (`/api/crawler/…`). Sein Zeitstempel
        # steht in `website_content_cache`, dort nach Betrieb abgelegt.
        'content_analysiert_am': _content_analysiert_am(db, lead_id),
    }


@router.post("/{project_id}/confirm-step")
def confirm_step(
    project_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    import json as _json
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    step_id = (body.get("step_id") or "").strip()
    if not step_id:
        raise HTTPException(400, "step_id fehlt")
    raw = getattr(project, "steps_confirmed", "{}") or "{}"
    try:
        confirmed = _json.loads(raw)
    except Exception:
        confirmed = {}
    confirmed[step_id] = {"confirmed": True, "confirmed_at": datetime.utcnow().isoformat()}
    project.steps_confirmed = _json.dumps(confirmed, ensure_ascii=False)
    db.commit()
    return {"saved": True, "step_id": step_id, "confirmed": confirmed}


@router.get("/{project_id}/confirmed-steps")
def get_confirmed_steps(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    import json as _json
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    raw = getattr(project, "steps_confirmed", "{}") or "{}"
    try:
        confirmed = _json.loads(raw)
    except Exception:
        confirmed = {}
    return confirmed


@router.post("/{project_id}/leistungsseiten")
def create_leistungsseite(
    project_id: int,
    body: LeistungsseitenCreate,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Speichert einen Leistungsseiten-Fragebogen (Teil 1 Stub).

    Der Datensatz wird als Eintrag in steps_confirmed["leistungsseiten"]
    (Array) abgelegt. Die tatsaechliche Seiten-Generierung folgt in Teil 2.
    """
    import json as _json
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    raw = getattr(project, "steps_confirmed", "{}") or "{}"
    try:
        confirmed = _json.loads(raw)
    except Exception:
        confirmed = {}
    if not isinstance(confirmed, dict):
        confirmed = {}

    existing = confirmed.get("leistungsseiten")
    if not isinstance(existing, list):
        existing = []

    entry = body.model_dump() if hasattr(body, "model_dump") else body.dict()
    entry["saved_at"] = datetime.utcnow().isoformat()
    existing.append(entry)
    confirmed["leistungsseiten"] = existing

    project.steps_confirmed = _json.dumps(confirmed, ensure_ascii=False)
    db.commit()

    return {
        "success": True,
        "message": "Fragebogen gespeichert",
        "leistung": body.leistung,
        "status": "fragebogen_ausgefuellt",
    }


# **Standen bis zum 23.08.2026 im Abschnitt „Projekte entfernen“** und sind
# beim Schnitt beinahe mit ausgezogen — sie gehoeren aber zu `PUT`
# darunter: `BLOCKED_KEYS` begrenzt, was ueberhaupt geschrieben werden
# darf, `spalten_der_projekttabelle` sagt, was es gibt. Dass sie dort
# lagen, sagt nichts darueber, wozu sie gehoeren (L-25).
BLOCKED_KEYS = {
    "id", "pid", "project_id", "projects_id",
    "created_at", "updated_at", "lead_id"
}

# Die tatsächlichen Spalten der Tabelle `projects`, einmal je Verbindung
# erfragt. Das Modell taugt hier nicht als Maßstab: Die Tabelle hat Spalten,
# die im ORM fehlen — genau deshalb schreibt diese Route mit Roh-SQL.
_SPALTEN_JE_DATENBANK: dict = {}


def spalten_der_projekttabelle(db: Session) -> frozenset:
    """Gibt die Spaltennamen der Tabelle `projects` zurück."""
    bind = db.get_bind()
    kennung = str(bind.url)
    bekannt = _SPALTEN_JE_DATENBANK.get(kennung)
    if bekannt is not None:
        return bekannt

    from sqlalchemy import inspect as _inspect
    spalten = frozenset(s["name"] for s in _inspect(bind).get_columns("projects"))
    _SPALTEN_JE_DATENBANK[kennung] = spalten
    return spalten


# Zurueck bei den uebrigen `/{project_id}`-Routen, nicht im Loeschmodul:
# Das wird frueher geladen, und ein Platzhalter dort verdeckte jeden
# festen Pfad danach (L-25, 23.08.2026).
@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Entfernt ein Projekt samt allem, was ohne es keinen Inhalt hat.

    Das Versandprotokoll bleibt erhalten — nur sein Verweis wird gelöst.
    Der Betrieb (`leads`) bleibt unberührt: Gelöscht wird das Projekt, nicht
    der Kunde.
    """
    from services.projekt_loeschen import entfernen

    vorhanden = db.execute(
        text("SELECT id FROM projects WHERE id = :id"), {"id": project_id}
    ).fetchone()
    if not vorhanden:
        raise HTTPException(404, "Projekt nicht gefunden")

    bericht = entfernen(db, [project_id])
    db.commit()
    return bericht


@router.put("/{project_id}")
def update_project(
    project_id: int,
    body: dict,
    db: Session = Depends(get_db),
):
    """Update project fields via raw SQL — avoids ORM column-mapping issues.

    Die Schlüssel des Rumpfes werden zu Spaltennamen im SQL. Ungeprüft heißt
    das: Der Aufrufer bestimmt, was im UPDATE steht. Deshalb muss jeder
    Schlüssel eine echte Spalte der Tabelle sein — was das nicht ist, wird
    abgewiesen statt still eingesetzt.
    """
    from sqlalchemy import text as _text

    erlaubte_spalten = spalten_der_projekttabelle(db)
    unbekannt = sorted(
        k for k in body
        if k not in BLOCKED_KEYS and k not in erlaubte_spalten
    )
    if unbekannt:
        raise HTTPException(
            status_code=400,
            detail=f"Unbekannte Felder: {', '.join(unbekannt)}",
        )

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
            portal = public_base_url() + "/portal/login"
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
    """Admin: generate approval token, store it, send email with frontend link."""
    import uuid
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    notifications_on = getattr(project, "email_notifications_enabled", True)
    to_email = getattr(project, "customer_email", None) or ""

    if not notifications_on or not to_email:
        return {"success": False, "message": "Keine E-Mail hinterlegt"}

    company = getattr(project, "company_name", "") or f"Projekt #{project_id}"

    # Generate and persist approval token (Tor 2)
    token = str(uuid.uuid4())
    db.execute(
        text("UPDATE projects SET content_approval_token=:t WHERE id=:id"),
        {"t": token, "id": project_id},
    )
    db.commit()

    frontend_url = public_base_url()
    approval_url = f"{frontend_url}/approve-content/{token}"

    try:
        from services.email import send_email as _send_email
        subject = f"Freigabe benötigt: {body.topic} — {company}"
        html = f"""
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:560px;margin:0 auto;color:#1A2C32">
  <div style="background:#008EAA;padding:24px 32px;border-radius:12px 12px 0 0">
    <div style="color:white;font-size:20px;font-weight:700">KOMPAGNON</div>
    <div style="color:rgba(255,255,255,.8);font-size:14px;margin-top:4px">Freigabe erforderlich</div>
  </div>
  <div style="background:#fff;padding:32px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px">
    <p>Guten Tag,</p>
    <p>für Ihr Projekt <strong>{company}</strong> benötigen wir Ihre Freigabe:</p>
    <div style="background:#f4f6f8;border-left:4px solid #008EAA;padding:14px 18px;border-radius:0 8px 8px 0;margin:20px 0">
      <div style="font-weight:700;font-size:15px">{body.topic}</div>
      {f'<div style="margin-top:8px;font-size:14px;color:#64748b">{body.notes}</div>' if body.notes else ''}
    </div>
    <p>Bitte klicken Sie auf den folgenden Button, um Ihre Freigabe zu erteilen:</p>
    <div style="text-align:center;margin:28px 0">
      <a href="{approval_url}"
         style="background:#008EAA;color:white;padding:14px 32px;border-radius:8px;
                text-decoration:none;font-weight:700;font-size:16px;display:inline-block">
        Jetzt freigeben ✓
      </a>
    </div>
    <p style="font-size:12px;color:#94a3b8">
      Alternativ: <a href="{approval_url}" style="color:#008EAA">{approval_url}</a>
    </p>
    <p>Mit freundlichen Grüßen,<br><strong>Ihr KOMPAGNON-Team</strong></p>
  </div>
</div>"""
        threading.Thread(target=_send_email, args=(to_email, subject, html), daemon=True).start()
    except Exception as exc:
        logger.warning(f"Freigabe-E-Mail fehlgeschlagen für Projekt {project_id}: {exc}")
        return {"success": False, "message": f"E-Mail-Versand fehlgeschlagen: {exc}"}

    return {"success": True, "message": "Freigabe-E-Mail gesendet", "token": token}


# ── Go-Live Automation ────────────────────────────────────────────────────────

_GOLIVE_STATUSES = {"phase_6", "6", 6, "go_live", "live", "golive", "phase6"}










# ── Screenshots ──────────────────────────────────────────────────────────────












