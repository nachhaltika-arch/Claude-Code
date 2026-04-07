"""
Briefings CRUD — flat project-briefing fields.
GET  /api/briefings/{lead_id}  → load (auto-creates if missing)
POST /api/briefings/{lead_id}  → create or overwrite
PUT  /api/briefings/{lead_id}  → partial update
"""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db, Briefing, Lead
from routers.auth_router import require_any_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/briefings", tags=["briefings"])

FLAT_FIELDS = [
    "project_id", "gewerk", "wz_code", "wz_title", "leistungen", "einzugsgebiet", "usp",
    "mitbewerber", "vorbilder", "farben", "wunschseiten", "stil",
    "logo_vorhanden", "fotos_vorhanden", "sonstige_hinweise", "status",
]


class BriefingBody(BaseModel):
    project_id: Optional[int] = None
    gewerk: Optional[str] = None
    wz_code: Optional[str] = None
    wz_title: Optional[str] = None
    leistungen: Optional[str] = None
    einzugsgebiet: Optional[str] = None
    usp: Optional[str] = None
    mitbewerber: Optional[str] = None
    vorbilder: Optional[str] = None
    farben: Optional[str] = None
    wunschseiten: Optional[str] = None
    stil: Optional[str] = None
    logo_vorhanden: Optional[bool] = None
    fotos_vorhanden: Optional[bool] = None
    sonstige_hinweise: Optional[str] = None
    status: Optional[str] = None


def _serialize(b: Briefing) -> dict:
    def _parse(val):
        if not val:
            return {}
        if isinstance(val, dict):
            return val
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return {}

    return {
        "id":                b.id,
        "lead_id":           b.lead_id,
        # Legacy JSON sections
        "projektrahmen":     _parse(getattr(b, "projektrahmen",  None)),
        "positionierung":    _parse(getattr(b, "positionierung", None)),
        "zielgruppe":        _parse(getattr(b, "zielgruppe",     None)),
        "wettbewerb":        _parse(getattr(b, "wettbewerb",     None)),
        "inhalte":           _parse(getattr(b, "inhalte",        None)),
        "funktionen":        _parse(getattr(b, "funktionen",     None)),
        "branding":          _parse(getattr(b, "branding",       None)),
        "struktur":          _parse(getattr(b, "struktur",       None)),
        "hosting":           _parse(getattr(b, "hosting",        None)),
        "seo":               _parse(getattr(b, "seo",            None)),
        "projektplan":       _parse(getattr(b, "projektplan",    None)),
        "freigaben":         _parse(getattr(b, "freigaben",      None)),
        # Flat fields
        "project_id":        getattr(b, "project_id",        None),
        "gewerk":            getattr(b, "gewerk",            "") or "",
        "wz_code":           getattr(b, "wz_code",           "") or "",
        "wz_title":          getattr(b, "wz_title",          "") or "",
        "leistungen":        getattr(b, "leistungen",        "") or "",
        "einzugsgebiet":     getattr(b, "einzugsgebiet",     "") or "",
        "usp":               getattr(b, "usp",               "") or "",
        "mitbewerber":       getattr(b, "mitbewerber",       "") or "",
        "vorbilder":         getattr(b, "vorbilder",         "") or "",
        "farben":            getattr(b, "farben",            "") or "",
        "wunschseiten":      getattr(b, "wunschseiten",      "") or "",
        "stil":              getattr(b, "stil",              "") or "",
        "logo_vorhanden":    bool(getattr(b, "logo_vorhanden",  False)),
        "fotos_vorhanden":   bool(getattr(b, "fotos_vorhanden", False)),
        "sonstige_hinweise": getattr(b, "sonstige_hinweise", "") or "",
        "status":            getattr(b, "status",            "entwurf") or "entwurf",
        "created_at":        str(b.created_at)[:16] if b.created_at else "",
        "updated_at":        str(b.updated_at)[:16] if b.updated_at else "",
    }


@router.get("/{lead_id}")
def get_briefing(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Load briefing for a lead; auto-creates if none exists."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        briefing = Briefing(lead_id=lead_id, status="entwurf")
        db.add(briefing)
        db.commit()
        db.refresh(briefing)
    return _serialize(briefing)


@router.post("/{lead_id}")
def create_briefing(
    lead_id: int,
    body: BriefingBody,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Create or fully overwrite the flat briefing fields for a lead."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        briefing = Briefing(lead_id=lead_id)
        db.add(briefing)

    data = body.model_dump(exclude_unset=False)
    for field in FLAT_FIELDS:
        val = data.get(field)
        if val is not None:
            setattr(briefing, field, val)

    briefing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(briefing)
    return _serialize(briefing)


@router.get("/{lead_id}/pdf")
def briefing_pdf(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generate and return briefing as PDF (application/pdf)."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing nicht gefunden")

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    company_name = (lead.display_name or lead.company_name) if lead else f"Lead #{lead_id}"

    from services.briefing_pdf import generate_briefing_pdf
    pdf_bytes = generate_briefing_pdf(briefing, company_name)

    filename = f"briefing-{lead_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.put("/{lead_id}")
def update_briefing(
    lead_id: int,
    body: BriefingBody,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Partial update — only fields present in the request body are changed."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing nicht gefunden")

    data = body.model_dump(exclude_unset=True)
    for field in FLAT_FIELDS:
        if field in data:
            setattr(briefing, field, data[field])

    briefing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(briefing)
    return _serialize(briefing)
