"""
Kampagne API — öffentlicher Endpunkt für Postkarten-Kampagnen.
POST /api/kampagne/audit-anfrage — kein Auth-Schutz.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import AuditResult, Lead, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kampagne", tags=["kampagne"])


class AuditAnfrageRequest(BaseModel):
    domain: str
    email: str
    mobil: str
    kampagne_quelle: str = "postkarte"


@router.post("/audit-anfrage")
async def audit_anfrage(
    req: AuditAnfrageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Öffentlicher Endpunkt für Postkarten-Kampagne.
    Legt Lead an (oder aktualisiert bestehenden) und startet Audit im Hintergrund.
    """
    try:
        domain = req.domain.strip().lower()
        # Normalize to full URL for audit
        if not domain.startswith(("http://", "https://")):
            website_url = f"https://{domain}"
        else:
            website_url = domain

        # ── a) Lead suchen oder anlegen ──────────────────────────────────────
        existing = (
            db.query(Lead)
            .filter(Lead.website_url.ilike(f"%{domain}%"))
            .first()
        )

        if existing:
            # Aktualisiere Kontaktdaten
            try:
                db.execute(
                    text(
                        "UPDATE leads SET email = :email, "
                        "mobile = :mobil, "
                        "whatsapp_nummer = :mobil, "
                        "kampagne_quelle = :quelle, "
                        "updated_at = NOW() "
                        "WHERE id = :id"
                    ),
                    {
                        "email": req.email,
                        "mobil": req.mobil,
                        "quelle": req.kampagne_quelle,
                        "id": existing.id,
                    },
                )
                db.commit()
            except Exception as upd_err:
                logger.warning(f"kampagne: update fehlgeschlagen: {upd_err}")
                db.rollback()
            lead_id = existing.id
            logger.info(f"kampagne: lead {lead_id} aktualisiert ({domain})")
        else:
            # Neuen Lead anlegen via raw SQL (bypass ORM relationship init)
            result = db.execute(
                text(
                    "INSERT INTO leads "
                    "(company_name, website_url, email, notes, status, lead_source, "
                    "analysis_score, geo_score, created_at, updated_at) "
                    "VALUES "
                    "(:company_name, :website_url, :email, :notes, 'new', :lead_source, "
                    "0, 0, NOW(), NOW()) "
                    "RETURNING id"
                ),
                {
                    "company_name": domain,
                    "website_url": website_url,
                    "email": req.email,
                    "notes": f"Mobil: {req.mobil}",
                    "lead_source": req.kampagne_quelle,
                },
            )
            row = result.fetchone()
            db.commit()
            lead_id = row[0]
            # Versuche mobile + whatsapp_nummer + kampagne_quelle zu setzen
            try:
                db.execute(
                    text(
                        "UPDATE leads SET mobile = :mobil, whatsapp_nummer = :mobil, "
                        "kampagne_quelle = :quelle WHERE id = :id"
                    ),
                    {"mobil": req.mobil, "quelle": req.kampagne_quelle, "id": lead_id},
                )
                db.commit()
            except Exception:
                db.rollback()
            logger.info(f"kampagne: neuer lead {lead_id} angelegt ({domain})")

        # ── b) Audit im Hintergrund starten ──────────────────────────────────
        try:
            from routers.audit import _normalise_url, _run_audit_background

            url = _normalise_url(website_url)

            # Scrape für company_name
            company_name = domain
            try:
                from services.scraper import scrape_website
                scraped = await scrape_website(url)
                company_name = scraped.get("company_name", "") or domain
            except Exception:
                pass

            audit = AuditResult(
                lead_id=lead_id,
                website_url=url,
                company_name=company_name,
                contact_name="",
                city="",
                trade="",
                status="pending",
            )
            db.add(audit)
            db.commit()
            db.refresh(audit)

            background_tasks.add_task(_run_audit_background, audit.id)
            logger.info(f"kampagne: audit {audit.id} gestartet für lead {lead_id}")
        except Exception as audit_err:
            logger.error(f"kampagne: audit-start fehlgeschlagen: {audit_err}")
            # Audit-Fehler nicht an Benutzer weitergeben — Lead ist bereits gespeichert

        return {"success": True, "lead_id": lead_id}

    except Exception as e:
        logger.error(f"kampagne audit-anfrage error: {type(e).__name__}: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}
