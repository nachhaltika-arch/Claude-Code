"""
Sitemap CRUD
GET    /api/sitemap/{lead_id}           → flat list of pages for a lead
POST   /api/sitemap/{lead_id}/pages     → create page
PUT    /api/sitemap/pages/{page_id}     → update page
DELETE /api/sitemap/pages/{page_id}     → delete page
PUT    /api/sitemap/{lead_id}/reorder   → save order (array of {id, position, parent_id})
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from database import Base, get_db, engine
from routers.auth_router import require_any_auth

router = APIRouter(prefix="/api/sitemap", tags=["sitemap"])


# ── ORM model (defined here, not in database.py to keep the diff small) ──────

class SitemapPage(Base):
    __tablename__ = "sitemap_pages"
    __table_args__ = {"extend_existing": True}

    id            = Column(Integer, primary_key=True, index=True)
    lead_id       = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    parent_id     = Column(Integer, ForeignKey("sitemap_pages.id", ondelete="SET NULL"), nullable=True)
    position      = Column(Integer, default=0)
    page_name     = Column(String(100), nullable=False)
    page_type     = Column(String(50),  default="info")
    zweck         = Column(Text,        nullable=True)
    ziel_keyword  = Column(String(150), nullable=True)
    cta_text      = Column(String(100), nullable=True)
    cta_ziel      = Column(String(50),  default="kontakt")
    notizen       = Column(Text,        nullable=True)
    status        = Column(String(30),  default="geplant")
    mockup_html   = Column(Text,        nullable=True)
    created_at    = Column(DateTime,    server_default=func.now())


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class PageCreate(BaseModel):
    page_name:    str
    parent_id:    Optional[int]  = None
    position:     int            = 0
    page_type:    str            = "info"
    zweck:        Optional[str]  = None
    ziel_keyword: Optional[str]  = None
    cta_text:     Optional[str]  = None
    cta_ziel:     str            = "kontakt"
    notizen:      Optional[str]  = None
    status:       str            = "geplant"
    mockup_html:  Optional[str]  = None


class PageUpdate(BaseModel):
    page_name:    Optional[str]  = None
    parent_id:    Optional[int]  = None
    position:     Optional[int]  = None
    page_type:    Optional[str]  = None
    zweck:        Optional[str]  = None
    ziel_keyword: Optional[str]  = None
    cta_text:     Optional[str]  = None
    cta_ziel:     Optional[str]  = None
    notizen:      Optional[str]  = None
    status:       Optional[str]  = None
    mockup_html:  Optional[str]  = None


class ReorderItem(BaseModel):
    id:        int
    position:  int
    parent_id: Optional[int] = None


# ── Serializer ─────────────────────────────────────────────────────────────────

def _serialize(p: SitemapPage) -> dict:
    return {
        "id":           p.id,
        "lead_id":      p.lead_id,
        "parent_id":    p.parent_id,
        "position":     p.position,
        "page_name":    p.page_name,
        "page_type":    p.page_type,
        "zweck":        p.zweck or "",
        "ziel_keyword": p.ziel_keyword or "",
        "cta_text":     p.cta_text or "",
        "cta_ziel":     p.cta_ziel or "kontakt",
        "notizen":      p.notizen or "",
        "status":       p.status or "geplant",
        "mockup_html":  p.mockup_html or "",
        "created_at":   str(p.created_at)[:16] if p.created_at else "",
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/{lead_id}")
def get_sitemap(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Return all sitemap pages for a lead as a flat list (parent_id indicates hierarchy)."""
    pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id)
        .order_by(SitemapPage.position)
        .all()
    )
    return [_serialize(p) for p in pages]


@router.post("/{lead_id}/pages", status_code=201)
def create_page(
    lead_id: int,
    body: PageCreate,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    page = SitemapPage(lead_id=lead_id, **body.model_dump())
    db.add(page)
    db.commit()
    db.refresh(page)
    return _serialize(page)


@router.put("/pages/{page_id}")
def update_page(
    page_id: int,
    body: PageUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    page = db.query(SitemapPage).filter(SitemapPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(page, field, value)
    db.commit()
    db.refresh(page)
    return _serialize(page)


@router.delete("/pages/{page_id}", status_code=204)
def delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    page = db.query(SitemapPage).filter(SitemapPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")
    db.delete(page)
    db.commit()


@router.put("/{lead_id}/reorder")
def reorder_pages(
    lead_id: int,
    items: List[ReorderItem],
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Batch-update position and parent_id for all pages of a lead."""
    ids = [item.id for item in items]
    pages = {
        p.id: p
        for p in db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.id.in_(ids))
        .all()
    }
    for item in items:
        if item.id in pages:
            pages[item.id].position  = item.position
            pages[item.id].parent_id = item.parent_id
    db.commit()
    return {"updated": len(pages)}
