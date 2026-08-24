"""Das Blatt eines Betriebs: Profil, Auditverlauf, QR-Code (L-25).

**Warum eigene Datei, 23.08.2026.** `routers/leads.py` hatte 1.186 Zeilen, und
`GET /{lead_id}/profile` allein 139 davon — die groesste Einzelroute der Datei.
Sie beantwortet eine eigene Frage: „Was weiss das System ueber diesen einen
Betrieb?" Dazu gehoeren der Auditverlauf und der QR-Code, mit dem der Betrieb
seine Analyse abruft.

**Vor dem Schnitt nachgemessen:** `leads.py` hat **keine** Funktion auf
Modulebene, die keine Route waere — alle 22 sind Endpunkte. Diese hier teilen
mit dem Rest also nichts ausser dem Router und seiner Sperre.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database import Lead, Project, AuditResult, get_db, SessionLocal
from routers.auth_router import (
    INNENDIENST, require_admin, require_any_auth, require_innendienst,
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


@router.get("/{lead_id}/profile")
def get_lead_profile(lead_id: int, db: Session = Depends(get_db)):
    """Full lead profile with audits, projects, and score history."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    audits = (
        db.query(AuditResult)
        .filter(AuditResult.lead_id == lead_id)
        .order_by(AuditResult.created_at.desc())
        .all()
    )

    projects = db.query(Project).filter(Project.lead_id == lead_id).all()

    latest_audit = audits[0] if audits else None

    score_history = [
        {
            "date": a.created_at.strftime("%d.%m.%Y") if a.created_at else "",
            "score": a.total_score,
            "level": a.level,
        }
        for a in reversed(audits)
    ]

    def _audit_dict(a):
        d = {
            "id": a.id,
            "created_at": a.created_at.strftime("%d.%m.%Y %H:%M") if a.created_at else "",
            "total_score": a.total_score,
            "level": a.level,
            "status": a.status,
            "website_url": a.website_url,
            "company_name": a.company_name,
            "trade": a.trade,
            "city": a.city,
            "ai_summary": a.ai_summary,
            "ssl_ok": a.ssl_ok,
            "mobile_score": a.mobile_score,
            "lcp_value": a.lcp_value,
            "cls_value": a.cls_value,
            "inp_value": a.inp_value,
            "rc_score": a.rc_score, "tp_score": a.tp_score,
            "bf_score": a.bf_score, "si_score": a.si_score,
            "se_score": a.se_score, "ux_score": a.ux_score,
        }
        # Item-level scores
        for key in [
            "rc_impressum", "rc_datenschutz", "rc_cookie", "rc_bfsg", "rc_urheberrecht", "rc_ecommerce",
            "tp_lcp", "tp_cls", "tp_inp", "tp_mobile", "tp_bilder",
            "ho_anbieter", "ho_uptime", "ho_http", "ho_backup", "ho_cdn",
            "bf_kontrast", "bf_tastatur", "bf_screenreader", "bf_lesbarkeit",
            "si_ssl", "si_header", "si_drittanbieter", "si_formulare",
            "se_seo", "se_schema", "se_lokal",
            "ux_erstindruck", "ux_cta", "ux_navigation", "ux_vertrauen", "ux_content", "ux_kontakt",
        ]:
            d[key] = getattr(a, key, 0) or 0
        # GEO / KI-Sichtbarkeit fields
        d["llms_txt"] = getattr(a, "llms_txt", False) or False
        d["robots_ai_friendly"] = getattr(a, "robots_ai_friendly", False) or False
        d["structured_data"] = getattr(a, "structured_data", False) or False
        d["ai_mentions"] = getattr(a, "ai_mentions", 0) or 0
        # JSON fields
        try:
            d["top_issues"] = json.loads(a.top_issues) if a.top_issues else []
        except (json.JSONDecodeError, TypeError):
            d["top_issues"] = []
        try:
            d["recommendations"] = json.loads(a.recommendations) if a.recommendations else []
        except (json.JSONDecodeError, TypeError):
            d["recommendations"] = []
        return d

    return {
        "lead": {
            "id": lead.id,
            "company_name": lead.company_name,
            "contact_name": lead.contact_name,
            "phone": lead.phone,
            "mobile": getattr(lead, 'mobile', '') or '',
            "email": lead.email,
            "website_url": lead.website_url,
            "city": lead.city,
            "trade": lead.trade,
            "status": lead.status,
            "lead_source": lead.lead_source,
            # Woher der Betrieb kam und unter welcher Rechtsgrundlage wir ihn
            # fuehren — abgeleitet aus derselben gespeicherten Quelle, damit
            # es keine zweite Wahrheit gibt (L-59).
            "datenherkunft": lead_quellen.herkunft_fuer(lead.lead_source),
            "rechtsgrundlage": lead_quellen.rechtsgrundlage_fuer(lead.lead_source),
            "quelle_gefuehrt": lead_quellen.quelle_bekannt(lead.lead_source),
            "notes": lead.notes,
            "created_at": lead.created_at.strftime("%d.%m.%Y") if lead.created_at else "",
            "website_screenshot": f"data:image/jpeg;base64,{lead.website_screenshot}" if getattr(lead, 'website_screenshot', None) else None,
            "street": getattr(lead, 'street', '') or '',
            "house_number": getattr(lead, 'house_number', '') or '',
            "postal_code": getattr(lead, 'postal_code', '') or '',
            "legal_form": getattr(lead, 'legal_form', '') or '',
            "vat_id": getattr(lead, 'vat_id', '') or '',
            "register_number": getattr(lead, 'register_number', '') or '',
            "register_court": getattr(lead, 'register_court', '') or '',
            "ceo_first_name": getattr(lead, 'ceo_first_name', '') or '',
            "ceo_last_name": getattr(lead, 'ceo_last_name', '') or '',
            "geschaeftsfuehrer": getattr(lead, 'geschaeftsfuehrer', '') or '',
            "display_name": getattr(lead, 'display_name', '') or '',
        },
        # Befunde der Anreicherung. Bewusst ohne `or False`: `None` heißt
        # „noch nicht geprüft" und darf nicht als „fehlt" durchgehen (UX-06).
        "anreicherung": {
            "has_ssl": getattr(lead, 'has_ssl', None),
            "has_impressum": getattr(lead, 'has_impressum', None),
            "pagespeed_mobile": getattr(lead, 'pagespeed_mobile_score', None),
            "geprueft_am": (lead.enriched_at.strftime("%d.%m.%Y")
                            if getattr(lead, 'enriched_at', None) else None),
        },
        "current_score": latest_audit.total_score if latest_audit else None,
        "current_level": latest_audit.level if latest_audit else None,
        "score_history": score_history,
        "total_audits": len(audits),
        "audits": [_audit_dict(a) for a in audits],
        "projects": [
            {
                "id": p.id,
                "status": p.status,
                "start_date": p.start_date.strftime("%d.%m.%Y") if p.start_date else "",
                "target_go_live": p.target_go_live.strftime("%d.%m.%Y") if p.target_go_live else "",
                "margin_percent": p.margin_percent,
            }
            for p in projects
        ],
        "project_id": projects[0].id if projects else None,
    }


@router.get("/{lead_id}/audits")
def get_lead_audits(lead_id: int, db: Session = Depends(get_db)):
    """Get all audits linked to a lead, newest first."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    audits = (
        db.query(AuditResult)
        .filter(AuditResult.lead_id == lead_id, AuditResult.status == "completed")
        .order_by(AuditResult.created_at.desc())
        .all()
    )

    results = []
    for a in audits:
        try:
            top_issues = json.loads(a.top_issues) if a.top_issues else []
        except (json.JSONDecodeError, TypeError):
            top_issues = []
        results.append({
            "id": a.id,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "total_score": a.total_score,
            "level": a.level,
            "website_url": a.website_url,
            "top_issues": top_issues,
            "ai_summary": a.ai_summary,
        })
    return results


@router.get("/{lead_id}/qr-code")
def get_qr_code(lead_id: int, db: Session = Depends(get_db)):
    """Get or create QR code for customer portal access."""
    from services.qr_service import generate_token, generate_qr_code, get_portal_url

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Nicht gefunden")

    if not lead.customer_token:
        lead.customer_token = generate_token()
        lead.customer_token_created_at = datetime.utcnow()
        db.commit()
        db.refresh(lead)

    portal_url = get_portal_url(lead.customer_token)
    qr_b64 = generate_qr_code(portal_url)

    return {
        'token': lead.customer_token,
        'portal_url': portal_url,
        'qr_code_base64': qr_b64,
        'created_at': str(lead.customer_token_created_at)[:10] if lead.customer_token_created_at else '',
    }


@router.post("/{lead_id}/qr-code/refresh")
def refresh_qr_code(lead_id: int, db: Session = Depends(get_db)):
    """Generate a new QR code token, invalidating the old one."""
    from services.qr_service import generate_token, generate_qr_code, get_portal_url

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Nicht gefunden")

    lead.customer_token = generate_token()
    lead.customer_token_created_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)

    portal_url = get_portal_url(lead.customer_token)
    qr_b64 = generate_qr_code(portal_url)

    return {
        'token': lead.customer_token,
        'portal_url': portal_url,
        'qr_code_base64': qr_b64,
        'created_at': str(lead.customer_token_created_at)[:10],
    }
