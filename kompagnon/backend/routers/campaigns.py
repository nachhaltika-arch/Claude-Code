"""
Campaign Manager
GET    /api/campaigns/           - list (with lead counts)
GET    /api/campaigns/stats      - source breakdown for dashboard
POST   /api/campaigns/           - create
GET    /api/campaigns/{id}       - detail
PUT    /api/campaigns/{id}       - update
DELETE /api/campaigns/{id}       - archive (soft-delete)
GET    /api/campaigns/{id}/leads - leads attributed to campaign
"""
import re
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from database import get_db
from routers.auth_router import get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


SOURCE_CONFIG = {
    "facebook":   {"label": "Facebook",   "medium": "social", "icon": "📘"},
    "linkedin":   {"label": "LinkedIn",   "medium": "social", "icon": "💼"},
    "google_ads": {"label": "Google Ads", "medium": "cpc",    "icon": "🔍"},
    "briefkarte": {"label": "Briefkarte", "medium": "print",  "icon": "📬"},
    "instagram":  {"label": "Instagram",  "medium": "social", "icon": "📸"},
    "email":      {"label": "E-Mail",     "medium": "email",  "icon": "✉️"},
    "sonstige":   {"label": "Sonstige",   "medium": "direct", "icon": "📌"},
}


def _slug(name: str) -> str:
    s = (name or "").lower().strip()
    for a, b in [("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")]:
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:200] or "kampagne"


def _unique_slug(base: str, db: Session) -> str:
    slug = base
    counter = 2
    while db.execute(text("SELECT id FROM campaigns WHERE slug = :s"), {"s": slug}).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def _build_url(row):
    """Baut die vollständige Tracking-URL auf."""
    target = (row.target_url if hasattr(row, "target_url") else row.get("target_url")) or "https://kompagnon.eu"
    source = row.source if hasattr(row, "source") else row.get("source")
    slug   = row.slug   if hasattr(row, "slug")   else row.get("slug")
    medium = (row.medium if hasattr(row, "medium") else row.get("medium")) or "direct"

    # Briefkarte: eigene Landing-Page
    if source == "briefkarte":
        return f"https://kompagnon.eu/kampagne/{slug}"

    sep = "&" if "?" in (target or "") else "?"
    return f"{target}{sep}utm_source={source}&utm_medium={medium}&utm_campaign={slug}"


def _serialize(row):
    d = dict(row._mapping)
    cfg = SOURCE_CONFIG.get(d.get("source"), {})
    d["source_label"] = cfg.get("label", d.get("source"))
    d["source_icon"]  = cfg.get("icon", "📌")
    d["tracking_url"] = _build_url(row)
    return d


# ── Pydantic models ─────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    source: str
    medium: Optional[str] = None
    description: Optional[str] = None
    target_url: Optional[str] = "https://kompagnon.eu"


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_url: Optional[str] = None
    is_active: Optional[bool] = None


# ── Endpoints ───────────────────────────────────────────────────────

@router.get("/")
def list_campaigns(db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.execute(text("""
        SELECT c.*,
          COUNT(l.id) AS lead_count,
          SUM(CASE WHEN l.status='won' THEN 1 ELSE 0 END) AS won_count
        FROM campaigns c
        LEFT JOIN leads l ON l.kampagne_id = c.id
        WHERE c.archived_at IS NULL
        GROUP BY c.id
        ORDER BY c.created_at DESC
    """)).fetchall()
    return [_serialize(r) for r in rows]


@router.get("/stats")
def campaign_stats(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Leads pro Quelle für Dashboard."""
    rows = db.execute(text("""
        SELECT
          COALESCE(l.utm_source, l.kampagne_quelle, 'direkt') AS source,
          COUNT(*) AS lead_count,
          SUM(CASE WHEN l.status='won' THEN 1 ELSE 0 END) AS won_count
        FROM leads l
        GROUP BY COALESCE(l.utm_source, l.kampagne_quelle, 'direkt')
        ORDER BY lead_count DESC
    """)).fetchall()
    out = []
    for r in rows:
        d = dict(r._mapping)
        cfg = SOURCE_CONFIG.get(d.get("source"), {})
        d["source_label"] = cfg.get("label", d.get("source") or "Direkt")
        d["source_icon"]  = cfg.get("icon", "📌")
        d["lead_count"]   = int(d.get("lead_count") or 0)
        d["won_count"]    = int(d.get("won_count") or 0)
        out.append(d)
    return out


@router.post("/")
def create_campaign(
    data: CampaignCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if data.source not in SOURCE_CONFIG:
        raise HTTPException(400, f"Unbekannte Quelle: {data.source}")

    medium = data.medium or SOURCE_CONFIG[data.source]["medium"]
    slug = _unique_slug(_slug(data.name), db)

    result = db.execute(text("""
        INSERT INTO campaigns (name, slug, source, medium, description, target_url, created_by)
        VALUES (:name, :slug, :source, :medium, :description, :target_url, :created_by)
        RETURNING id
    """), {
        "name":        data.name,
        "slug":        slug,
        "source":      data.source,
        "medium":      medium,
        "description": data.description,
        "target_url":  data.target_url or "https://kompagnon.eu",
        "created_by":  current_user.id,
    })
    campaign_id = result.fetchone()[0]
    db.commit()
    return get_campaign(campaign_id, db, current_user)


@router.get("/{campaign_id}")
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    row = db.execute(text("""
        SELECT c.*,
          COUNT(l.id) AS lead_count,
          SUM(CASE WHEN l.status='won' THEN 1 ELSE 0 END) AS won_count
        FROM campaigns c
        LEFT JOIN leads l ON l.kampagne_id = c.id
        WHERE c.id = :id
        GROUP BY c.id
    """), {"id": campaign_id}).fetchone()
    if not row:
        raise HTTPException(404, "Kampagne nicht gefunden")
    return _serialize(row)


@router.put("/{campaign_id}")
def update_campaign(
    campaign_id: int,
    data: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    fields = []
    params = {"id": campaign_id}
    if data.name is not None:
        fields.append("name = :name")
        params["name"] = data.name
    if data.description is not None:
        fields.append("description = :description")
        params["description"] = data.description
    if data.target_url is not None:
        fields.append("target_url = :target_url")
        params["target_url"] = data.target_url
    if data.is_active is not None:
        fields.append("is_active = :is_active")
        params["is_active"] = data.is_active
    if fields:
        db.execute(text(f"UPDATE campaigns SET {', '.join(fields)} WHERE id = :id"), params)
        db.commit()
    return get_campaign(campaign_id, db, current_user)


@router.delete("/{campaign_id}")
def archive_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    db.execute(
        text("UPDATE campaigns SET archived_at = NOW() WHERE id = :id"),
        {"id": campaign_id},
    )
    db.commit()
    return {"archived": campaign_id}


@router.get("/{campaign_id}/leads")
def campaign_leads(
    campaign_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Alle Leads die dieser Kampagne zugeordnet sind."""
    rows = db.execute(text("""
        SELECT id, company_name, email, phone, status, created_at,
               utm_source, utm_medium, utm_campaign
        FROM leads WHERE kampagne_id = :id
        ORDER BY created_at DESC
    """), {"id": campaign_id}).fetchall()
    return [dict(r._mapping) for r in rows]
