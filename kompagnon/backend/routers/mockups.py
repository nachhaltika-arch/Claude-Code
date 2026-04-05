"""
Mockup Version History
GET  /api/mockups/{lead_id}              - All versions grouped by sitemap_page_id
GET  /api/mockups/{lead_id}?page_id=X   - Versions for one page only
POST /api/mockups/{lead_id}             - Save a new version
GET  /api/mockups/version/{version_id}  - Single version detail
DELETE /api/mockups/version/{version_id} - Delete a version
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Session, declarative_base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db, Lead
from routers.sitemap import SitemapPage

router = APIRouter(prefix="/api/mockups", tags=["mockups"])

# ── ORM model ─────────────────────────────────────────────────────────────────
from database import Base

class MockupVersion(Base):
    __tablename__ = "mockup_versions"
    __table_args__ = {"extend_existing": True}

    id              = Column(Integer, primary_key=True, index=True)
    lead_id         = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    sitemap_page_id = Column(Integer, ForeignKey("sitemap_pages.id", ondelete="CASCADE"), nullable=True, index=True)
    page_name       = Column(String(150), default="")
    version_name    = Column(String(150), default="")
    html_content    = Column(Text, default="")
    created_at      = Column(DateTime, default=datetime.utcnow)
    created_by      = Column(String(100), default="")


# ── Pydantic ───────────────────────────────────────────────────────────────────
class MockupVersionCreate(BaseModel):
    sitemap_page_id: Optional[int] = None
    page_name:       str = ""
    version_name:    str = ""
    html_content:    str = ""
    created_by:      str = ""


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
    """Return versions grouped by sitemap_page_id. Pass ?page_id= to filter."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    q = db.query(MockupVersion).filter(MockupVersion.lead_id == lead_id)
    if page_id is not None:
        q = q.filter(MockupVersion.sitemap_page_id == page_id)
        versions = q.order_by(MockupVersion.created_at.desc()).all()
        return [_version_dict(v) for v in versions]

    # Grouped response
    versions = q.order_by(MockupVersion.created_at.desc()).all()

    # Build page_id → page_name map from sitemap_pages
    page_ids = list({v.sitemap_page_id for v in versions if v.sitemap_page_id})
    pages_map: dict[int, str] = {}
    if page_ids:
        rows = db.query(SitemapPage).filter(SitemapPage.id.in_(page_ids)).all()
        pages_map = {p.id: p.page_name for p in rows}

    groups: dict[Optional[int], dict] = {}
    for v in versions:
        pid = v.sitemap_page_id
        if pid not in groups:
            groups[pid] = {
                "page_id":   pid,
                "page_name": pages_map.get(pid, v.page_name or "Ohne Seite"),
                "versions":  [],
            }
        groups[pid]["versions"].append(_version_dict(v))

    return {"pages": list(groups.values())}


@router.post("/{lead_id}")
def create_version(
    lead_id: int,
    body: MockupVersionCreate,
    db: Session = Depends(get_db),
):
    """Save a new mockup version for a lead (optionally linked to a sitemap page)."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    v = MockupVersion(
        lead_id=lead_id,
        sitemap_page_id=body.sitemap_page_id,
        page_name=body.page_name,
        version_name=body.version_name,
        html_content=body.html_content,
        created_by=body.created_by,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return {"id": v.id, "status": "created"}


@router.get("/version/{version_id}")
def get_version(version_id: int, db: Session = Depends(get_db)):
    """Return full html_content of a single version."""
    v = db.query(MockupVersion).filter(MockupVersion.id == version_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Version nicht gefunden")
    return {**_version_dict(v), "html_content": v.html_content}


@router.delete("/version/{version_id}")
def delete_version(version_id: int, db: Session = Depends(get_db)):
    v = db.query(MockupVersion).filter(MockupVersion.id == version_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Version nicht gefunden")
    db.delete(v)
    db.commit()
    return {"status": "deleted"}
