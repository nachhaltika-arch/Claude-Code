"""
Kampagne API — öffentlicher Endpunkt für Postkarten-Kampagnen.
POST /api/kampagne/audit-anfrage — kein Auth-Schutz.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import AuditResult, Lead, get_db, SessionLocal

logger = logging.getLogger(__name__)

# Rate limiter — uses same key_func (IP-based) as main.py instance
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/kampagne", tags=["kampagne"])


class AuditAnfrageRequest(BaseModel):
    domain: str
    email: str
    mobil: str
    kampagne_quelle: str = "postkarte"
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


@router.post("/audit-anfrage")
@limiter.limit("3/minute")
async def audit_anfrage(
    request: Request,
    req: AuditAnfrageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Öffentlicher Endpunkt für Postkarten-Kampagne.
    Legt Lead an (oder aktualisiert bestehenden) und startet Audit im Hintergrund.
    """
    domain = req.domain.strip().lower()
    # Normalize to full URL for audit
    if not domain.startswith(("http://", "https://")):
        website_url = f"https://{domain}"
    else:
        website_url = domain

    # SSRF-Schutz — öffentlicher Kampagnen-Endpunkt darf keine
    # internen Hosts / Metadata-Services triggern.
    # Außerhalb des try/except, damit HTTPException als 400 durchgeht.
    from services.url_validator import validate_url
    website_url = validate_url(website_url)

    try:

        # ── UTM-Daten + Kampagne auflösen ────────────────────────────────────
        utm_source   = (req.utm_source   or req.kampagne_quelle or "").strip()
        utm_medium   = (req.utm_medium   or "").strip()
        utm_campaign = (req.utm_campaign or req.kampagne_quelle or "").strip()
        kampagne_id = None
        try:
            if utm_campaign:
                cr = db.execute(
                    text("SELECT id, source, medium FROM campaigns WHERE slug = :s"),
                    {"s": utm_campaign},
                ).fetchone()
                if cr:
                    kampagne_id = cr.id
                    if not utm_source:
                        utm_source = cr.source
                    if not utm_medium:
                        utm_medium = cr.medium or ""
        except Exception as ce:
            logger.warning(f"kampagne: Kampagnen-Lookup fehlgeschlagen: {ce}")

        # ── a) Lead suchen oder anlegen ──────────────────────────────────────
        existing = (
            db.query(Lead)
            .filter(Lead.website_url.ilike(f"%{domain}%"))
            .first()
        )

        if existing:
            # Aktualisiere Kontaktdaten + UTM-Attribution
            try:
                db.execute(
                    text(
                        "UPDATE leads SET email = :email, "
                        "mobile = :mobil, "
                        "whatsapp_nummer = :mobil, "
                        "kampagne_quelle = :quelle, "
                        "kampagne_id = COALESCE(kampagne_id, :cid), "
                        "utm_source = COALESCE(utm_source, :usrc), "
                        "utm_medium = COALESCE(utm_medium, :umed), "
                        "utm_campaign = COALESCE(utm_campaign, :ucmp), "
                        "updated_at = NOW() "
                        "WHERE id = :id"
                    ),
                    {
                        "email":  req.email,
                        "mobil":  req.mobil,
                        "quelle": req.kampagne_quelle,
                        "cid":    kampagne_id,
                        "usrc":   utm_source or None,
                        "umed":   utm_medium or None,
                        "ucmp":   utm_campaign or None,
                        "id":     existing.id,
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
            # Versuche mobile + whatsapp + UTM-Attribution zu setzen
            try:
                db.execute(
                    text(
                        "UPDATE leads SET mobile = :mobil, whatsapp_nummer = :mobil, "
                        "kampagne_quelle = :quelle, kampagne_id = :cid, "
                        "utm_source = :usrc, utm_medium = :umed, utm_campaign = :ucmp "
                        "WHERE id = :id"
                    ),
                    {
                        "mobil":  req.mobil,
                        "quelle": req.kampagne_quelle,
                        "cid":    kampagne_id,
                        "usrc":   utm_source or None,
                        "umed":   utm_medium or None,
                        "ucmp":   utm_campaign or None,
                        "id":     lead_id,
                    },
                )
                db.commit()
            except Exception:
                db.rollback()
            logger.info(f"kampagne: neuer lead {lead_id} angelegt ({domain})")

        # DB-Verbindung vor externem Scrape freigeben
        db.close()

        # ── b) Audit im Hintergrund starten ──────────────────────────────────
        try:
            from routers.audit import _normalise_url, _run_audit_background

            url = _normalise_url(website_url)

            # Scrape für company_name — OHNE offene DB-Verbindung
            company_name = domain
            try:
                from services.scraper import scrape_website
                scraped = await scrape_website(url)
                company_name = scraped.get("company_name", "") or domain
            except Exception:
                pass

            # Neue Session zum Speichern des Audits
            db2 = SessionLocal()
            try:
                audit = AuditResult(
                    lead_id=lead_id,
                    website_url=url,
                    company_name=company_name,
                    contact_name="",
                    city="",
                    trade="",
                    status="pending",
                )
                db2.add(audit)
                db2.commit()
                db2.refresh(audit)
                audit_id = audit.id
            finally:
                db2.close()

            background_tasks.add_task(_run_audit_background, audit_id)
            logger.info(f"kampagne: audit {audit_id} gestartet für lead {lead_id}")
        except Exception as audit_err:
            logger.error(f"kampagne: audit-start fehlgeschlagen: {audit_err}")
            # Audit-Fehler nicht an Benutzer weitergeben — Lead ist bereits gespeichert

        return {"success": True, "lead_id": lead_id}

    except Exception as e:
        logger.error(f"kampagne audit-anfrage error: {type(e).__name__}: {e}")
        try:
            db.rollback()
        except Exception:
            pass
        return {"success": False, "error": str(e)}
