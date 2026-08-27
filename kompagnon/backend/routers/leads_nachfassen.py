"""Was nach dem Erstkontakt kommt: Mailstrecke und Leistungsbericht (L-25).

**Warum eigene Datei, 23.08.2026.** Zwei kleine Abschnitte aus `leads.py`, die
dasselbe Thema haben und mit dem Bestand nichts zu tun: Die Mailstrecke fasst
nach, der Bericht sagt, was dabei herauskam.

**Zusammenhang mit L-62:** Fuenf von acht Werten der Mailstrecken-Liste greifen
ins Leere. Der Befund liegt weiter offen — er ist hier jetzt an einer Stelle
zu finden statt zwischen Import und Domainpruefung.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database import Lead, Project, AuditResult, get_db, SessionLocal
from routers.auth_router import (
    require_admin, require_any_auth, require_innendienst,
    verlangt_recht,
    get_current_user,
)
from services import betriebsname, lead_quellen
from services.base_urls import self_base_url
from services.pdf_generator import branche_fuer_protokoll
from services.ratenbegrenzung import lead_grenzen
from services.lead_verlauf import verlauf_bauen
import asyncio
import httpx
import json
import logging
import os

logger = logging.getLogger(__name__)

# **Dieselbe Sperre wie in `leads.py`.** Der Bestand ist Innendienst; angemeldet
# zu sein reicht nicht, sonst bekommt ein Kunde Daten fremder Betriebe (Befund
# vom 17.08.2026). Sie haengt am Router, nicht an der einzelnen Route — wer
# eine Route hinzufuegt und die Abhaengigkeit vergisst, oeffnet sie sonst.
router = APIRouter(prefix="/api/leads", tags=["leads"],
                   dependencies=[Depends(require_innendienst)])


# ── E-Mail-Sequenz-Endpunkte ─────────────────────────────────────────────────

@router.post("/{lead_id}/sequence/start", dependencies=[Depends(require_any_auth)])
def sequence_start(lead_id: int, db: Session = Depends(get_db)):
    from services.sequence_runner import start_sequence_for_lead
    ok = start_sequence_for_lead(lead_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Lead not found or no email")
    return {"success": ok}


@router.post("/{lead_id}/sequence/pause", dependencies=[Depends(require_any_auth)])
def sequence_pause(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.sequence_paused = True
    db.commit()
    return {"success": True}


@router.post("/{lead_id}/sequence/stop", dependencies=[Depends(require_any_auth)])
def sequence_stop(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.sequence_active = False
    lead.sequence_paused = False
    lead.sequence_step = 0
    db.commit()
    return {"success": True}


@router.get("/{lead_id}/email-logs", dependencies=[Depends(require_any_auth)])
def get_email_logs(lead_id: int, db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT * FROM email_logs WHERE lead_id=:id ORDER BY sent_at DESC LIMIT 50"),
        {"id": lead_id},
    ).mappings().all()
    return [dict(r) for r in rows]


# ── Admin: manueller Performance-Report Trigger ──────────────────────────────

@router.post("/admin/trigger-performance-reports")
async def trigger_performance_reports(
    _=Depends(require_any_auth),
):
    """Manueller Trigger für den monatlichen Performance-Report (Admin-Test)."""
    from automations.scheduler import job_monthly_performance_report

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, job_monthly_performance_report)

    return {
        "message": "Performance-Report Job gestartet — prüfe Render-Logs",
        "note": "Läuft im Hintergrund, dauert 1-3 Min. je nach Anzahl Kunden",
    }
