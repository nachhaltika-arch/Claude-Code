"""
Mockup Version History
GET  /api/mockups/{lead_id}              - All versions, optional ?page_id=X filter
GET  /api/mockups/{lead_id}/{version_id} - Single version WITH html_content
POST /api/mockups/{lead_id}             - Save a new version
DELETE /api/mockups/version/{version_id} - Delete a version
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db, Lead, Base
from routers.sitemap import SitemapPage

router = APIRouter(prefix="/api/mockups", tags=["mockups"])

# ── ORM model ─────────────────────────────────────────────────────────────────

class MockupVersion(Base):
    __tablename__ = "mockup_versions"
    __table_args__ = {"extend_existing": True}

    id              = Column(Integer, primary_key=True, index=True)
    lead_id         = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    sitemap_page_id = Column(Integer, ForeignKey("sitemap_pages.id", ondelete="CASCADE"), nullable=True, index=True)
    page_name       = Column(String(150), default="Startseite")
    version_name    = Column(String(150), default="")
    html_content    = Column(Text, default="")
    created_at      = Column(DateTime, default=datetime.utcnow)
    created_by      = Column(String(100), default="")


# ── Pydantic ───────────────────────────────────────────────────────────────────

class MockupVersionCreate(BaseModel):
    sitemap_page_id: Optional[int] = None
    page_name: str = "Startseite"
    version_name: str
    html_content: str


# ── Helpers ────────────────────────────────────────────────────────────────────

def _version_dict(v: MockupVersion) -> dict:
    return {
        "id":              v.id,
        "sitemap_page_id": v.sitemap_page_id,
        "page_name":       v.page_name or "",
        "version_name":    v.version_name or "",
        "created_at":      str(v.created_at)[:16] if v.created_at else "",
        "created_by":      v.created_by or "",
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/{lead_id}")
def list_versions(
    lead_id: int,
    page_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Return versions for a lead, optionally filtered by page_id."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    q = db.query(MockupVersion).filter(MockupVersion.lead_id == lead_id)
    if page_id is not None:
        q = q.filter(MockupVersion.sitemap_page_id == page_id)

    versions = q.order_by(MockupVersion.created_at.desc()).all()
    return [_version_dict(v) for v in versions]


@router.get("/{lead_id}/{version_id}")
def get_version(lead_id: int, version_id: int, db: Session = Depends(get_db)):
    """Return full html_content of a single version."""
    v = db.query(MockupVersion).filter(
        MockupVersion.id == version_id,
        MockupVersion.lead_id == lead_id,
    ).first()
    if not v:
        raise HTTPException(status_code=404, detail="Version nicht gefunden")
    return {**_version_dict(v), "html_content": v.html_content}


@router.post("/{lead_id}")
def create_version(
    lead_id: int,
    body: MockupVersionCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Save a new mockup version; created_by taken from X-User header if present."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    created_by = request.headers.get("X-User") or request.headers.get("X-Username") or ""

    v = MockupVersion(
        lead_id=lead_id,
        sitemap_page_id=body.sitemap_page_id,
        page_name=body.page_name,
        version_name=body.version_name,
        html_content=body.html_content,
        created_by=created_by,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return {"id": v.id, "status": "created"}


@router.delete("/version/{version_id}")
def delete_version(version_id: int, db: Session = Depends(get_db)):
    v = db.query(MockupVersion).filter(MockupVersion.id == version_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Version nicht gefunden")
    db.delete(v)
    db.commit()
    return {"status": "deleted"}
