"""
UserCards API — unified endpoint replacing /api/leads and /api/customers.
All three prefixes (/api/usercards, /api/leads, /api/customers) are served
by the same handlers defined here.

GET    /api/usercards/            list all cards
POST   /api/usercards/            create a card
GET    /api/usercards/{id}        get single card (full detail + audits)
PUT    /api/usercards/{id}        full update
PATCH  /api/usercards/{id}        partial update
DELETE /api/usercards/{id}        delete card
GET    /api/usercards/{id}/pagespeed   stored PageSpeed values
POST   /api/usercards/{id}/pagespeed   run PageSpeed measurement
GET    /api/usercards/{id}/audits      all audits for this card
GET    /api/usercards/{id}/profile     full profile (audits + projects + history)
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import AuditResult, Project, UserCard, User, get_db, SessionLocal
from routers.auth_router import optional_auth, require_any_auth, require_innendienst
from services.audit_pagespeed import (
    PSI_ENDPOINT,
    auth_headers as pagespeed_auth_headers,
)

# Vorgabe: geschlossen — siehe routers/leads.py. Diese Routen tragen
# dieselben Kundendaten wie der Lead-Router und waren ebenso offen.
# Vorgabe: Innendienst. `require_any_auth` fragt nur, *ob* jemand angemeldet
# ist — und damit bekam ein Kunde am 18.08.2026 ueber `GET /api/usercards/`
# und den Alias `GET /api/customers/` den vollstaendigen Bestand. Dieselbe
# Luecke wie am 17.08. beim Lead-Router; dieses Modul blieb uebrig.
#
# Was ein Kunde wirklich braucht, ist genau eine Route — das eigene Profil,
# das sein Dashboard laedt. Die haengt unten am `kunden_router`.
router = APIRouter(prefix="/api/usercards", tags=["usercards"],
                   dependencies=[Depends(require_innendienst)])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class UserCardCreate(BaseModel):
    company_name: str
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    website_url: str = None
    city: str = ""
    trade: str = ""
    lead_source: str = None
    notes: str = None
    status: str = "new"
    legacy_type: str = "lead"


class UserCardUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website_url: Optional[str] = None
    city: Optional[str] = None
    trade: Optional[str] = None
    lead_source: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    display_name: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    postal_code: Optional[str] = None
    legal_form: Optional[str] = None
    vat_id: Optional[str] = None
    register_number: Optional[str] = None
    register_court: Optional[str] = None
    ceo_first_name: Optional[str] = None
    ceo_last_name: Optional[str] = None
    analysis_score: Optional[int] = None
    geo_score: Optional[int] = None
    # Customer management fields
    next_touchpoint_date: Optional[datetime] = None
    next_touchpoint_type: Optional[str] = None
    upsell_status: Optional[str] = None
    upsell_package: Optional[str] = None
    recurring_revenue: Optional[float] = None
    legacy_type: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _card_to_dict(card: UserCard) -> dict:
    """Serialise a UserCard to a JSON-safe dict (no screenshot blob)."""
    return {
        "id": card.id,
        "company_name": card.company_name or "",
        "display_name": card.display_name or "",
        "contact_name": card.contact_name or "",
        "phone": card.phone or "",
        "email": card.email or "",
        "website_url": card.website_url or "",
        "city": card.city or "",
        "trade": card.trade or "",
        "status": card.status or "new",
        "lead_source": card.lead_source or "",
        "analysis_score": card.analysis_score or 0,
        "geo_score": card.geo_score or 0,
        "notes": card.notes or "",
        "website_screenshot": None,   # excluded from list — too heavy
        "street": card.street or "",
        "house_number": card.house_number or "",
        "postal_code": card.postal_code or "",
        "legal_form": card.legal_form or "",
        "vat_id": card.vat_id or "",
        "register_number": card.register_number or "",
        "register_court": card.register_court or "",
        "ceo_first_name": card.ceo_first_name or "",
        "ceo_last_name": card.ceo_last_name or "",
        # Customer management
        "next_touchpoint_date": card.next_touchpoint_date.isoformat() if card.next_touchpoint_date else None,
        "next_touchpoint_type": card.next_touchpoint_type or "",
        "upsell_status": card.upsell_status or "none",
        "upsell_package": card.upsell_package or "",
        "recurring_revenue": card.recurring_revenue or 0.0,
        # Meta
        "legacy_type": card.legacy_type or "lead",
        "created_at": str(card.created_at)[:10] if card.created_at else "",
        "updated_at": str(card.updated_at)[:10] if card.updated_at else "",
    }


def _pagespeed_payload(card: UserCard) -> dict:
    return {
        "mobile_score":  card.pagespeed_mobile_score,
        "desktop_score": card.pagespeed_desktop_score,
        "lcp_mobile":    card.pagespeed_lcp_mobile,
        "cls_mobile":    card.pagespeed_cls_mobile,
        "inp_mobile":    card.pagespeed_inp_mobile,
        "fcp_mobile":    card.pagespeed_fcp_mobile,
        "checked_at":    card.pagespeed_checked_at.isoformat() if card.pagespeed_checked_at else None,
    }


def _audit_dict(a: AuditResult) -> dict:
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
    try:
        d["top_issues"] = json.loads(a.top_issues) if a.top_issues else []
    except (json.JSONDecodeError, TypeError):
        d["top_issues"] = []
    try:
        d["recommendations"] = json.loads(a.recommendations) if a.recommendations else []
    except (json.JSONDecodeError, TypeError):
        d["recommendations"] = []
    return d


def _get_card_or_404(card_id: int, db: Session) -> UserCard:
    card = db.query(UserCard).filter(UserCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="UserCard nicht gefunden")
    return card


def _check_kunde_access(card_id: int, current_user: User | None) -> None:
    """Raise 403 if the authenticated user is a Kunde accessing someone else's card."""
    if current_user and current_user.role == "kunde":
        if current_user.lead_id != card_id:
            raise HTTPException(status_code=403, detail="Zugriff verweigert")


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("/")
def list_usercards(
    status: str = Query(None),
    legacy_type: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(200),
    db: Session = Depends(get_db),
    current_user: User = Depends(optional_auth),
):
    """List all user cards, optionally filtered by status or legacy_type."""
    query = db.query(UserCard)
    # Kunde role: only own card
    if current_user and current_user.role == "kunde":
        if not current_user.lead_id:
            return []
        query = query.filter(UserCard.id == current_user.lead_id)
    if status:
        query = query.filter(UserCard.status == status)
    if legacy_type:
        query = query.filter(UserCard.legacy_type == legacy_type)
    cards = query.order_by(UserCard.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for card in cards:
        try:
            result.append(_card_to_dict(card))
        except Exception:
            continue
    return result


@router.post("/")
def create_usercard(data: UserCardCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a new user card."""
    card = UserCard(
        company_name=data.company_name,
        contact_name=data.contact_name,
        phone=data.phone,
        email=data.email,
        website_url=data.website_url,
        city=data.city,
        trade=data.trade,
        lead_source=data.lead_source,
        notes=data.notes,
        status=data.status,
        legacy_type=data.legacy_type,
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    if card.website_url:
        try:
            from services.lead_enrichment import enrich_lead_sync
            background_tasks.add_task(enrich_lead_sync, card.id)
        except ImportError:
            pass

    return _card_to_dict(card)


# Was ein Kunde braucht: das eigene Profil, das `CustomerDashboard.jsx` laedt.
# Eigener Router, wie beim Lead-Router — die Route prueft selbst, ob die Karte
# ihm gehoert (`_check_kunde_access`).
kunden_router = APIRouter(prefix="/api/usercards", tags=["usercards-kunde"],
                          dependencies=[Depends(require_any_auth)])


@kunden_router.get("/{card_id}/profile")
def get_usercard_profile(card_id: int, db: Session = Depends(get_db), current_user: User = Depends(optional_auth)):
    """Full card profile with audits, projects, and score history."""
    _check_kunde_access(card_id, current_user)
    card = _get_card_or_404(card_id, db)

    audits = (
        db.query(AuditResult)
        .filter(AuditResult.lead_id == card_id)
        .order_by(AuditResult.created_at.desc())
        .all()
    )
    projects = db.query(Project).filter(Project.lead_id == card_id).all()
    latest_audit = audits[0] if audits else None

    score_history = [
        {"date": a.created_at.strftime("%d.%m.%Y") if a.created_at else "", "score": a.total_score, "level": a.level}
        for a in reversed(audits)
    ]

    return {
        "lead": {
            "id": card.id,
            "company_name": card.company_name,
            "contact_name": card.contact_name,
            "phone": card.phone,
            "email": card.email,
            "website_url": card.website_url,
            "city": card.city,
            "trade": card.trade,
            "status": card.status,
            "lead_source": card.lead_source,
            "notes": card.notes,
            "created_at": card.created_at.strftime("%d.%m.%Y") if card.created_at else "",
            "website_screenshot": (
                f"data:image/jpeg;base64,{card.website_screenshot}"
                if card.website_screenshot else None
            ),
            "street":          card.street or "",
            "house_number":    card.house_number or "",
            "postal_code":     card.postal_code or "",
            "legal_form":      card.legal_form or "",
            "vat_id":          card.vat_id or "",
            "register_number": card.register_number or "",
            "register_court":  card.register_court or "",
            "ceo_first_name":  card.ceo_first_name or "",
            "ceo_last_name":   card.ceo_last_name or "",
            "display_name":    card.display_name or "",
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
    }


@router.get("/{card_id}/audits")
def get_usercard_audits(card_id: int, db: Session = Depends(get_db), current_user: User = Depends(optional_auth)):
    """Get all completed audits for a card, newest first."""
    _check_kunde_access(card_id, current_user)
    _get_card_or_404(card_id, db)
    audits = (
        db.query(AuditResult)
        .filter(AuditResult.lead_id == card_id, AuditResult.status == "completed")
        .order_by(AuditResult.created_at.desc())
        .all()
    )
    return [_audit_dict(a) for a in audits]


@router.get("/{card_id}/pagespeed")
def get_usercard_pagespeed(card_id: int, db: Session = Depends(get_db), current_user: User = Depends(optional_auth)):
    """Return stored PageSpeed values without a new API call."""
    _check_kunde_access(card_id, current_user)
    card = _get_card_or_404(card_id, db)
    return _pagespeed_payload(card)


@router.post("/{card_id}/pagespeed")
async def run_usercard_pagespeed(card_id: int, db: Session = Depends(get_db)):
    """Run Google PageSpeed Insights (mobile + desktop) and persist results."""
    card = _get_card_or_404(card_id, db)
    if not card.website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")
    website_url = card.website_url

    # DB-Verbindung vor externem PageSpeed-Call freigeben
    db.close()

    # Schluessel als Kopfzeile, nicht in der URL — httpx protokolliert die
    # vollstaendige Anfrage-URL (L-98). Eine Stelle, vier Aufrufer.
    base = PSI_ENDPOINT
    params_base = {"url": website_url}
    kopf = pagespeed_auth_headers()

    async with httpx.AsyncClient(timeout=60.0) as client:
        mobile_resp, desktop_resp = await asyncio.gather(
            client.get(base, params={**params_base, "strategy": "mobile"}, headers=kopf),
            client.get(base, params={**params_base, "strategy": "desktop"}, headers=kopf),
        )

    def _score(resp) -> int | None:
        try:
            return round((resp.json()["categories"]["performance"]["score"] or 0) * 100)
        except Exception:
            return None

    def _audit_val(resp, key) -> float | None:
        try:
            return resp.json()["lighthouseResult"]["audits"][key]["numericValue"]
        except Exception:
            return None

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        card = _get_card_or_404(card_id, db2)
        card.pagespeed_mobile_score  = _score(mobile_resp)
        card.pagespeed_desktop_score = _score(desktop_resp)
        card.pagespeed_lcp_mobile    = _audit_val(mobile_resp, "largest-contentful-paint")
        card.pagespeed_cls_mobile    = _audit_val(mobile_resp, "cumulative-layout-shift")
        card.pagespeed_inp_mobile    = _audit_val(mobile_resp, "interaction-to-next-paint")
        card.pagespeed_fcp_mobile    = _audit_val(mobile_resp, "first-contentful-paint")
        card.pagespeed_checked_at    = datetime.utcnow()
        db2.commit()
        db2.refresh(card)
        return _pagespeed_payload(card)
    finally:
        db2.close()


@router.get("/{card_id}")
def get_usercard(card_id: int, db: Session = Depends(get_db), current_user: User = Depends(optional_auth)):
    """Get a single user card by ID."""
    _check_kunde_access(card_id, current_user)
    card = _get_card_or_404(card_id, db)
    d = _card_to_dict(card)
    # Include screenshot on single-record fetch
    d["website_screenshot"] = (
        f"data:image/jpeg;base64,{card.website_screenshot}"
        if card.website_screenshot else None
    )
    return d


@router.put("/{card_id}")
@router.patch("/{card_id}")
def update_usercard(card_id: int, data: UserCardUpdate, db: Session = Depends(get_db)):
    """Update a user card (partial or full). Accepts both PUT and PATCH."""
    card = _get_card_or_404(card_id, db)
    for field, value in data.dict(exclude_none=True).items():
        if hasattr(card, field):
            setattr(card, field, value)
    card.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(card)
    return {"success": True, "id": card.id}


@router.delete("/{card_id}")
def delete_usercard(card_id: int, db: Session = Depends(get_db)):
    """Delete a user card and all associated audit results."""
    card = _get_card_or_404(card_id, db)
    db.query(AuditResult).filter(AuditResult.lead_id == card_id).delete()
    db.delete(card)
    db.commit()
    return {"success": True, "message": f"UserCard {card_id} gelöscht"}


# ── Keine Alias-Router mehr (21.08.2026) ─────────────────────────────────────
#
# Hier standen zwei Router, die dieselben Funktionen zusaetzlich unter
# `/api/leads` und `/api/customers` anboten — „damit Aufrufe an beide Praefixe
# transparent funktionieren". Gemessen beim Auftrennen der Nahtstellen
# (Modulkarte):
#
#   * Die `/api/leads`-Aliasse waren **vollstaendig tot**. Der echte
#     `leads.router` ist frueher eingebunden und gewinnt jede dieser Routen.
#   * Der `/api/customers`-Alias war **nicht** tot — er ueberdeckte
#     `routers/customers.py`. `GET /api/customers/` lieferte deshalb
#     **UserCards statt Customers**: zwei verschiedene Entitaeten auf einer
#     Adresse, und die Antwort haing an der Reihenfolge in `main.py`.
#     Nachgewiesen am laufenden Server mit einer UserCard und null Customers.
#   * Nebenwirkung: Der Alias trug `require_innendienst`, `customers.py` nur
#     `require_any_auth`. Die Ueberdeckung hat die Sicherheitsarbeit gemacht.
#     `customers.py` traegt jetzt selbst die richtige Sperre.
#
# Kein Aufrufer im Repo benutzte die Aliasse — weder Frontend noch
# Browser-Tests noch Dokumentation. `tests/test_router_kollisionen.py` haelt
# die Adressen von nun an eindeutig.
