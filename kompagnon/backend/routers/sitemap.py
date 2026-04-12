"""
Sitemap CRUD + AI generation + PDF export
GET    /api/sitemap/{lead_id}           → flat list of pages for a lead
POST   /api/sitemap/{lead_id}/pages     → create page
PUT    /api/sitemap/pages/{page_id}     → update page
DELETE /api/sitemap/pages/{page_id}     → delete page
PUT    /api/sitemap/{lead_id}/reorder   → save order (array of {id, position, parent_id})
POST   /api/sitemap/{lead_id}/generate  → KI-Vorlage generieren
GET    /api/sitemap/{lead_id}/pdf       → PDF-Export
"""
import json
import logging
import os
import re
import unicodedata
from datetime import datetime
from io import BytesIO
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from reportlab.platypus.flowables import HRFlowable
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from database import Base, Briefing, Lead, get_db
from routers.auth_router import require_any_auth, optional_auth

logger = logging.getLogger(__name__)

# ── PDF brand tokens (shared with briefing_pdf.py) ────────────────────────────
_TEAL       = colors.HexColor("#008EAA")
_DARK_TEAL  = colors.HexColor("#004F59")
_LIGHT_GREY = colors.HexColor("#F4F7F8")
_MID_GREY   = colors.HexColor("#8A9BA8")
_TEXT_DARK  = colors.HexColor("#1A2C32")
_WHITE      = colors.white
_FOOTER_TXT = "KOMPAGNON Communications BP GmbH · kompagnon.eu"
_PAGE_W, _PAGE_H = A4
_MARGIN = 18 * mm


def _register_fonts():
    try:
        import reportlab
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        fp = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
        pdfmetrics.registerFont(TTFont("DV",      os.path.join(fp, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DV-Bold", os.path.join(fp, "DejaVuSans-Bold.ttf")))
        return "DV", "DV-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


_FONT, _FONT_B = _register_fonts()


def _t(text: str) -> str:
    if not text:
        return ""
    return unicodedata.normalize("NFC", str(text))

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
    mockup_html      = Column(Text,        nullable=True)
    ist_pflichtseite = Column(Boolean,     default=False)
    gjs_html         = Column(Text,        default='')
    gjs_css          = Column(Text,        default='')
    gjs_data         = Column(Text,        default='{}')
    created_at       = Column(DateTime,    server_default=func.now())


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
    # ist_pflichtseite is intentionally excluded – always forced to False in handler


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
    # ist_pflichtseite is intentionally excluded – cannot be changed via API


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
        "status":           p.status or "geplant",
        "mockup_html":      p.mockup_html or "",
        "gjs_html":         p.gjs_html or "",
        "ist_pflichtseite": bool(p.ist_pflichtseite),
        "created_at":       str(p.created_at)[:16] if p.created_at else "",
    }


# ── Pflichtseiten ──────────────────────────────────────────────────────────────

PFLICHTSEITEN = [
    {"page_name": "Impressum",                 "page_type": "rechtlich", "position": 90, "zweck": "Gesetzlich vorgeschriebene Pflichtangaben"},
    {"page_name": "Datenschutzerklärung",      "page_type": "rechtlich", "position": 91, "zweck": "Informationen zur Datenverarbeitung gemäß DSGVO"},
    {"page_name": "Barrierefreiheitserklärung","page_type": "rechtlich", "position": 92, "zweck": "Konformitätserklärung gemäß BFSG / BITV 2.0"},
    {"page_name": "AGB",                       "page_type": "rechtlich", "position": 93, "zweck": "Allgemeine Geschäftsbedingungen"},
]


def _ensure_pflichtseiten(lead_id: int, db: Session) -> None:
    """Insert missing Pflichtseiten for a lead (idempotent)."""
    existing_names = {
        p.page_name
        for p in db.query(SitemapPage.page_name)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.ist_pflichtseite.is_(True))
        .all()
    }
    for pf in PFLICHTSEITEN:
        if pf["page_name"] not in existing_names:
            db.add(SitemapPage(
                lead_id=lead_id,
                page_name=pf["page_name"],
                page_type=pf["page_type"],
                position=pf["position"],
                zweck=pf["zweck"],
                status="geplant",
                ist_pflichtseite=True,
            ))
    db.commit()


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/{lead_id}")
def get_sitemap(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Return all sitemap pages for a lead as a flat list (parent_id indicates hierarchy)."""
    _ensure_pflichtseiten(lead_id, db)
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
    data = body.model_dump()
    data["ist_pflichtseite"] = False  # user-created pages are never Pflichtseiten
    page = SitemapPage(lead_id=lead_id, **data)
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
    updates = body.model_dump(exclude_unset=True)
    if page.ist_pflichtseite:
        # Only content fields may be changed; structural fields are locked
        allowed = {"zweck", "notizen", "status"}
        updates = {k: v for k, v in updates.items() if k in allowed}
    for field, value in updates.items():
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
    if page.ist_pflichtseite:
        raise HTTPException(status_code=403, detail="Pflichtseiten können nicht gelöscht werden")
    db.delete(page)
    db.commit()


# ── GrapesJS editor endpoints ─────────────────────────────────────────────────

pages_router = APIRouter(prefix="/api/pages", tags=["pages"])


class GjsData(BaseModel):
    html:    str  = ""
    css:     str  = ""
    gjsData: dict = {}


@pages_router.get("/{page_id}/editor")
def get_editor_data(
    page_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    page = db.query(SitemapPage).filter(SitemapPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")
    gjs_data = {}
    try:
        gjs_data = json.loads(page.gjs_data or '{}')
    except Exception:
        pass
    return {"html": page.gjs_html or "", "css": page.gjs_css or "", "gjsData": gjs_data}


@pages_router.post("/{page_id}/editor")
def save_editor_data(
    page_id: int,
    body: GjsData,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_auth),
):
    # Script-Inhalte erkennen und im Audit-Log festhalten.
    # Kein Sanitizing — Admins duerfen legitim <script>-Tags einbinden
    # (z.B. Google Analytics). Transparenz + CSP-Header beim Deploy
    # uebernehmen die Defense-in-Depth.
    has_scripts = bool(re.search(r'<script[\s>]', body.html or "", re.IGNORECASE))
    has_iframes = bool(re.search(r'<iframe[\s>]', body.html or "", re.IGNORECASE))
    has_event_handlers = bool(re.search(
        r'\bon\w+\s*=', body.html or "", re.IGNORECASE
    ))

    if has_scripts or has_iframes or has_event_handlers:
        logger.warning(
            "Script-Inhalt gespeichert | "
            f"page_id={page_id} | "
            f"user={getattr(current_user, 'email', 'unknown')} | "
            f"scripts={has_scripts} | "
            f"iframes={has_iframes} | "
            f"event_handlers={has_event_handlers}"
        )

    page = db.query(SitemapPage).filter(SitemapPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")
    page.gjs_html = body.html
    page.gjs_css  = body.css
    page.gjs_data = json.dumps(body.gjsData, ensure_ascii=False)
    db.commit()
    return {"ok": True}


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


# ── Fallback template ─────────────────────────────────────────────────────────

_FALLBACK_PAGES = [
    {"page_name": "Startseite", "page_type": "startseite", "position": 0, "parent_id": None, "zweck": "Erster Eindruck, klare Botschaft",     "ziel_keyword": "", "cta_text": "Jetzt anfragen",   "cta_ziel": "kontakt"},
    {"page_name": "Leistungen", "page_type": "leistung",   "position": 1, "parent_id": None, "zweck": "Übersicht aller Leistungen",            "ziel_keyword": "", "cta_text": "Mehr erfahren",    "cta_ziel": "kontakt"},
    {"page_name": "Leistung 1", "page_type": "leistung",   "position": 2, "parent_id": 1,    "zweck": "Detail-Seite erste Leistung",           "ziel_keyword": "", "cta_text": "Angebot anfordern","cta_ziel": "kontakt"},
    {"page_name": "Leistung 2", "page_type": "leistung",   "position": 3, "parent_id": 1,    "zweck": "Detail-Seite zweite Leistung",          "ziel_keyword": "", "cta_text": "Angebot anfordern","cta_ziel": "kontakt"},
    {"page_name": "Über uns",   "page_type": "vertrauen",  "position": 4, "parent_id": None, "zweck": "Vertrauen aufbauen, Team vorstellen",   "ziel_keyword": "", "cta_text": "Kontakt aufnehmen","cta_ziel": "kontakt"},
    {"page_name": "Kontakt",    "page_type": "conversion", "position": 5, "parent_id": None, "zweck": "Leadgenerierung, Kontaktformular",      "ziel_keyword": "", "cta_text": "Nachricht senden", "cta_ziel": "kontakt"},
]


def _insert_pages(lead_id: int, raw_pages: list, db: Session) -> list:
    """Persist a list of page dicts, return serialized results."""
    created = []
    id_map: dict[int, int] = {}  # old position-based index → new DB id (for parent linking)

    for i, p in enumerate(raw_pages):
        page = SitemapPage(
            lead_id=lead_id,
            page_name=str(p.get("page_name", "Seite"))[:100],
            page_type=str(p.get("page_type", "info"))[:50],
            position=int(p.get("position", i)),
            parent_id=None,  # resolve after first pass
            zweck=p.get("zweck") or "",
            ziel_keyword=str(p.get("ziel_keyword") or "")[:150],
            cta_text=str(p.get("cta_text") or "")[:100],
            cta_ziel=str(p.get("cta_ziel") or "kontakt")[:50],
            notizen=p.get("notizen") or "",
            status="geplant",
        )
        db.add(page)
        db.flush()  # get page.id
        id_map[i] = page.id
        created.append((page, p.get("parent_id")))

    # Second pass: resolve parent_id references
    for page, raw_parent in created:
        if isinstance(raw_parent, int) and raw_parent in id_map:
            page.parent_id = id_map[raw_parent]

    db.commit()
    for page, _ in created:
        db.refresh(page)
    return [_serialize(page) for page, _ in created]


# ── ENDPOINT: KI-Vorlage generieren ──────────────────────────────────────────

@router.post("/{lead_id}/generate")
async def generate_sitemap(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generate sitemap pages via Claude AI (or fallback template)."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    # Step 1: Pflichtseiten immer zuerst sicherstellen
    _ensure_pflichtseiten(lead_id, db)

    briefing   = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    gewerk     = (briefing.gewerk     if briefing and briefing.gewerk     else lead.trade)   or "Handwerk"
    leistungen = (briefing.leistungen if briefing and briefing.leistungen else "")           or ""
    city       = lead.city or "Deutschland"

    # Step 2: Nur Nicht-Pflichtseiten löschen
    db.query(SitemapPage).filter(
        SitemapPage.lead_id == lead_id,
        SitemapPage.ist_pflichtseite.is_(False),
    ).delete()
    db.commit()

    # Step 3: KI oder Fallback
    api_key = os.getenv("ANTHROPIC_API_KEY")
    source = "fallback"
    if not api_key:
        _insert_pages(lead_id, _FALLBACK_PAGES, db)
    else:
        prompt = (
            "Du bist ein Website-Stratege für Handwerksbetriebe.\n"
            "Erstelle eine Sitemap mit 5-8 INHALTLICHEN Seiten für diesen Betrieb.\n"
            "NICHT einschließen: Impressum, Datenschutz, AGB, Barrierefreiheit – "
            "diese werden automatisch ergänzt.\n"
            f"Gewerk: {gewerk}, Stadt: {city}, Leistungen: {leistungen}\n"
            "Antworte NUR als JSON-Array:\n"
            '[{ "page_name": "", "page_type": "startseite|leistung|info|vertrauen|conversion", '
            '"zweck": "", "ziel_keyword": "", "cta_text": "", "cta_ziel": "kontakt|formular|tel", '
            '"position": 0, "parent_id": null }]'
        )
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key, max_retries=0, timeout=60.0)
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = "\n".join(
                    line for line in raw.splitlines()
                    if not line.strip().startswith("```")
                ).strip()
            # Truncated JSON repair: close open strings/objects/arrays
            try:
                raw_pages = json.loads(raw)
            except json.JSONDecodeError:
                repaired = raw.rstrip().rstrip(",")
                if not repaired.endswith("]"):
                    # Close any unterminated string
                    if repaired.count('"') % 2 != 0:
                        repaired += '"'
                    # Close unterminated object
                    open_braces = repaired.count("{") - repaired.count("}")
                    repaired += "}" * max(0, open_braces)
                    # Close array
                    if not repaired.endswith("]"):
                        repaired += "]"
                raw_pages = json.loads(repaired)
            if not isinstance(raw_pages, list) or not raw_pages:
                raise ValueError("Ungültige Antwortstruktur")
            _insert_pages(lead_id, raw_pages, db)
            source = "ai"
        except Exception as exc:
            logger.warning("Sitemap KI-Generierung fehlgeschlagen, Fallback: %s", exc)
            _insert_pages(lead_id, _FALLBACK_PAGES, db)

    # Gesamte Sitemap (Inhalt + Pflichtseiten) zurückgeben
    all_pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id)
        .order_by(SitemapPage.position)
        .all()
    )
    return {"pages": [_serialize(p) for p in all_pages], "source": source}


# ── ENDPOINT: PDF-Export ──────────────────────────────────────────────────────

def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont(_FONT, 7)
    canvas.setFillColor(_MID_GREY)
    canvas.drawString(_MARGIN, 10 * mm, _FOOTER_TXT)
    canvas.drawRightString(_PAGE_W - _MARGIN, 10 * mm, f"Seite {doc.page}")
    canvas.restoreState()


def _styles() -> dict:
    return {
        "cover_brand":   ParagraphStyle("sm_cover_brand",   fontName=_FONT_B, fontSize=32, textColor=_TEAL,      alignment=TA_CENTER, spaceAfter=6),
        "cover_title":   ParagraphStyle("sm_cover_title",   fontName=_FONT_B, fontSize=20, textColor=_TEXT_DARK,  alignment=TA_CENTER, spaceAfter=4),
        "cover_company": ParagraphStyle("sm_cover_company", fontName=_FONT_B, fontSize=15, textColor=_DARK_TEAL,  alignment=TA_CENTER, spaceAfter=4),
        "cover_sub":     ParagraphStyle("sm_cover_sub",     fontName=_FONT,   fontSize=10, textColor=_MID_GREY,   alignment=TA_CENTER, spaceAfter=2),
        "section_head":  ParagraphStyle("sm_section_head",  fontName=_FONT_B, fontSize=11, textColor=_WHITE,      spaceAfter=0, leftIndent=4),
        "body":          ParagraphStyle("sm_body",          fontName=_FONT,   fontSize=9,  textColor=_TEXT_DARK,  leading=14),
        "step_text":     ParagraphStyle("sm_step_text",     fontName=_FONT_B, fontSize=11, textColor=_TEXT_DARK,  spaceAfter=4),
        "step_sub":      ParagraphStyle("sm_step_sub",      fontName=_FONT,   fontSize=9,  textColor=_MID_GREY,   spaceAfter=8, leading=13),
    }


_PFLICHT_DESC = {
    "Impressum":                  "Gesetzliche Anbieterkennzeichnung nach § 5 TMG",
    "Datenschutzerklärung":       "Informationspflicht gemäß Art. 13/14 DSGVO",
    "Barrierefreiheitserklärung": "Konformitätserklärung gemäß BFSG / BITV 2.0",
    "AGB":                        "Allgemeine Geschäftsbedingungen / Vertragsgrundlage",
}


def _generate_sitemap_pdf(pages: list, company_name: str) -> bytes:
    content_pages = [p for p in pages if not p.get("ist_pflichtseite")]
    pflicht_pages = [p for p in pages if p.get("ist_pflichtseite")]

    _RED       = colors.HexColor("#C0392B")
    _LIGHT_RED = colors.HexColor("#FDECEA")

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=_MARGIN, rightMargin=_MARGIN,
        topMargin=_MARGIN,  bottomMargin=20 * mm,
        title=f"Seitenstruktur – {company_name}",
        author="KOMPAGNON",
    )
    S = _styles()
    story = []
    col_w = _PAGE_W - 2 * _MARGIN

    # ── PAGE 1: Cover ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 40 * mm))
    story.append(Paragraph("KOMPAGNON", S["cover_brand"]))
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="60%", thickness=2, color=_TEAL, hAlign="CENTER"))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Seitenstruktur", S["cover_title"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(_t(company_name), S["cover_company"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(datetime.now().strftime("%d. %B %Y"), S["cover_sub"]))
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="60%", thickness=1, color=_LIGHT_GREY, hAlign="CENTER"))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Vertraulich – erstellt im Strategy Workshop", S["cover_sub"]))
    story.append(PageBreak())

    # ── PAGE 2: Inhaltliche Seiten ────────────────────────────────────────────
    def _section_header(label: str, bg=_TEAL) -> Table:
        t = Table([[Paragraph(label, S["section_head"])]], colWidths=[col_w])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ]))
        return t

    story.append(_section_header("Inhaltliche Seiten"))
    story.append(Spacer(1, 4 * mm))

    id_set = {p["id"] for p in content_pages}
    col_widths = [60 * mm, 55 * mm, 40 * mm, 30 * mm]
    tbl_data = [[
        Paragraph("<b>Seitenname</b>",  S["body"]),
        Paragraph("<b>Zweck</b>",       S["body"]),
        Paragraph("<b>Keyword</b>",     S["body"]),
        Paragraph("<b>CTA</b>",         S["body"]),
    ]]
    for p in content_pages:
        is_child = p.get("parent_id") and p["parent_id"] in id_set
        name = ("  \u2514 " if is_child else "") + _t(p["page_name"])
        tbl_data.append([
            Paragraph(name,                              S["body"]),
            Paragraph(_t(p.get("zweck", "")),            S["body"]),
            Paragraph(_t(p.get("ziel_keyword", "")),     S["body"]),
            Paragraph(_t(p.get("cta_text", "")),         S["body"]),
        ])

    tbl = Table(tbl_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  _LIGHT_GREY),
        ("GRID",           (0, 0), (-1, -1), 0.4, _MID_GREY),
        ("TOPPADDING",     (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _LIGHT_GREY]),
    ]))
    story.append(tbl)
    story.append(PageBreak())

    # ── PAGE 3: Rechtlich erforderliche Seiten ────────────────────────────────
    story.append(_section_header("Rechtlich erforderliche Seiten", bg=_DARK_TEAL))
    story.append(Spacer(1, 4 * mm))

    pf_widths = [70 * mm, 115 * mm]
    pf_data = [[
        Paragraph("<b>Seite</b>",        S["body"]),
        Paragraph("<b>Beschreibung</b>", S["body"]),
    ]]
    for p in pflicht_pages:
        desc = _PFLICHT_DESC.get(p["page_name"], p.get("zweck", ""))
        pf_data.append([
            Paragraph(_t(p["page_name"]), S["body"]),
            Paragraph(_t(desc),           S["body"]),
        ])

    pf_tbl = Table(pf_data, colWidths=pf_widths, repeatRows=1)
    pf_tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  _LIGHT_GREY),
        ("GRID",           (0, 0), (-1, -1), 0.4, _MID_GREY),
        ("TOPPADDING",     (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _LIGHT_GREY]),
    ]))
    story.append(pf_tbl)
    story.append(Spacer(1, 6 * mm))

    # Roter Hinweis-Kasten
    warn_style = ParagraphStyle(
        "sm_warn", fontName=_FONT_B, fontSize=9, textColor=_RED, leading=14,
    )
    warn_tbl = Table(
        [[Paragraph(
            "Diese Seiten sind gesetzlich vorgeschrieben und werden von KOMPAGNON "
            "mit rechtskonformem Inhalt befüllt.",
            warn_style,
        )]],
        colWidths=[col_w],
    )
    warn_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _LIGHT_RED),
        ("BOX",           (0, 0), (-1, -1), 1.5, _RED),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    story.append(warn_tbl)
    story.append(PageBreak())

    # ── PAGE 4: Nächste Schritte ──────────────────────────────────────────────
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Nächste Schritte nach Freigabe der Sitemap", S["cover_title"]))
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=_TEAL))
    story.append(Spacer(1, 8 * mm))

    next_steps = [
        ("1. Freigabe der Seitenstruktur",
         "Gemeinsam prüfen und bestätigen Sie die geplante Seitenstruktur. "
         "Ergänzungen oder Streichungen werden in dieser Phase vorgenommen."),
        ("2. Keyword-Recherche & SEO-Konzept",
         "Für jede Seite werden die wichtigsten Suchbegriffe recherchiert und "
         "eine SEO-Grundstrategie erarbeitet."),
        ("3. Wireframes & Inhaltsplanung",
         "Auf Basis der Sitemap entstehen Wireframes, die den Aufbau jeder Seite "
         "visualisieren. Gleichzeitig wird der benötigte Content geplant."),
        ("4. Design & Umsetzung",
         "Das finale Design wird entwickelt und anschließend umgesetzt. "
         "Sie erhalten regelmäßige Zwischenstände zur Freigabe."),
    ]
    for title, sub in next_steps:
        story.append(Paragraph(_t(title), S["step_text"]))
        story.append(Paragraph(_t(sub),   S["step_sub"]))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


@router.get("/{lead_id}/pdf")
def export_sitemap_pdf(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(optional_auth),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    _ensure_pflichtseiten(lead_id, db)
    pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id)
        .order_by(SitemapPage.position)
        .all()
    )
    serialized = [_serialize(p) for p in pages]
    company_name = lead.display_name or lead.company_name or f"Lead #{lead_id}"
    pdf_bytes = _generate_sitemap_pdf(serialized, company_name)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="sitemap-{lead_id}.pdf"'},
    )
