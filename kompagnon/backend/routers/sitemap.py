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
import unicodedata
from datetime import datetime
from io import BytesIO
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
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
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, text
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


# ── Hormozi-Section-Katalog (Wireframe-Library-Mapping) ──────────────────────
# Bridge zwischen Sitemap (Stage 2) und Wireframes (Stage 3). AI wählt aus
# dieser Liste pro Page; jeder Key entspricht später einer React-Komponente
# in kompagnon/frontend/src/wireframes/sections/. Begründung pro Section
# steht in docs/conversion-spec-shk.md.
SECTION_CATALOG = {
    # Hero-Varianten
    "hero_value_equation": "Hero mit Hormozi-Outcome+Time+Effort-Versprechen (Startseite)",
    "hero_service":        "Hero für Service-Detail-Page mit klarem Outcome",
    "hero_minimal":        "Kompakter Hero — für Über uns / Kontakt / Rechtliches",

    # Conversion-Sections
    "problem":             "Pain-Point-Section — typische Schmerzen der Zielgruppe",
    "offer_stack":         "Hormozi-Wertbox: EUR-Positionen + Gesamtwert + Anker",
    "process_steps":       "4-6 nummerierte Schritte mit Zeitangabe (Friction-Reducer)",
    "guarantee_block":     "5 AGB-konforme Garantien (Risk Reversal)",
    "urgency_block":       "Echte Stichtage (BAFA/GEG/Slot-Cap) — Honest Scarcity",

    # Trust / Social Proof
    "trust_strip":         "Logo-Streifen (Innung, Hersteller, Zertifikate, Bewertungen)",
    "fallstudien_3":       "3 Fallstudien-Cards mit Ort/Heizlast/Einsparung-Zahlen",

    # Info-/Content-Sections
    "service_grid":        "Übersicht aller Services — für Startseite/Leistungen",
    "team":                "Team/Meister-Vorstellung mit Fotos",
    "faq":                 "Allgemeine FAQ — 8-12 Fragen",
    "faq_service":         "Service-spezifische FAQ (Einwand-Behandlung mit Zahlen)",
    "content_richtext":    "Reiner Fließtext-Block — für Info-/Rechtsseiten",

    # CTA
    "cta_inline":          "Inline-CTA zwischen Sections",
    "cta_final":           "Finale CTA + Sticky-Mobile-Bottom-Bar (Pflicht auf Conversion-Pages)",
    "contact_form":        "Kontakt-Formular mit Telefon/Mail/WhatsApp",

    # Footer/Legal
    "footer_legal":        "Footer mit Pflicht-Links (Impressum, Datenschutz, AGB)",
}

# Fallback / Default-Section-Sets falls AI keine Sections liefert.
# Reihenfolge ist relevant — wird 1:1 als Render-Order genommen.
DEFAULT_SECTIONS_BY_PAGETYPE: dict[str, list[str]] = {
    "startseite":  ["hero_value_equation", "problem", "service_grid", "offer_stack",
                    "trust_strip", "fallstudien_3", "guarantee_block", "faq", "cta_final"],
    "leistung":    ["hero_service", "problem", "offer_stack", "process_steps",
                    "fallstudien_3", "trust_strip", "guarantee_block", "faq_service", "cta_final"],
    "vertrauen":   ["hero_minimal", "team", "fallstudien_3", "trust_strip", "cta_inline"],
    "conversion":  ["hero_minimal", "offer_stack", "guarantee_block", "urgency_block",
                    "contact_form", "cta_final"],
    "info":        ["hero_minimal", "content_richtext", "faq", "cta_inline"],
    "ground":      ["hero_minimal", "service_grid", "faq", "contact_form"],
    "rechtlich":   ["hero_minimal", "content_richtext"],
}


def _resolve_sections(page_dict: dict) -> list[str]:
    """Pick a section list from the AI output, falling back to the page-type default.
    Filters unknown keys against SECTION_CATALOG so we never persist garbage."""
    raw = page_dict.get("sections")
    if isinstance(raw, list) and raw:
        cleaned = [str(s) for s in raw if isinstance(s, str) and s in SECTION_CATALOG]
        if cleaned:
            return cleaned
    page_type = str(page_dict.get("page_type") or "info")
    return DEFAULT_SECTIONS_BY_PAGETYPE.get(page_type, DEFAULT_SECTIONS_BY_PAGETYPE["info"])


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
    # KI-generierter Content (Batch-Generierung)
    ki_h1                = Column(Text,         nullable=True)
    ki_hero_text         = Column(Text,         nullable=True)
    ki_abschnitt_text    = Column(Text,         nullable=True)
    ki_cta               = Column(String(100),  nullable=True)
    ki_meta_title        = Column(String(70),   nullable=True)
    ki_meta_description  = Column(String(160),  nullable=True)
    content_generated    = Column(Boolean,      default=False)
    content_generated_at = Column(DateTime,     nullable=True)
    # Hormozi-Spec Section-Plan (Wireframe-Stage 3): JSON-Array von Section-Keys.
    # Wird vom Sitemap-Generator je nach page_type/Branche gefüllt, z.B.
    # ["hero_value_equation","problem","offer_stack","trust_strip","fallstudien_3",
    #  "guarantee_block","faq","cta_final"]
    sections_json        = Column(Text,         nullable=True)
    # Phase-1 Crawl-Import: woher stammt die Page?
    # 'manual' (CRUD), 'ki_generated' (KI-Vorschlag), 'crawled' (Bestand)
    source               = Column(String(20),   default='manual')
    original_url         = Column(Text,         nullable=True)
    # JSON-Array von sitemap_page-IDs, die diese (KI-vorgeschlagene) Page
    # aus dem gecrawlten Bestand konsolidiert / ersetzt
    replaces_page_ids    = Column(Text,         nullable=True)
    # Relume-Parität R1: Per-Page-KI-Prompt + User-Color-Tag
    ai_prompt            = Column(Text,         nullable=True)
    color_tag            = Column(String(7),    nullable=True)
    # Relume-Parität R2 Feature 4: 'primary' (live) | 'variant' (Alternative)
    variant              = Column(String(20),   default='primary')


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
    page_name:    Optional[str]       = None
    parent_id:    Optional[int]       = None
    position:     Optional[int]       = None
    page_type:    Optional[str]       = None
    zweck:        Optional[str]       = None
    ziel_keyword: Optional[str]       = None
    cta_text:     Optional[str]       = None
    cta_ziel:     Optional[str]       = None
    notizen:      Optional[str]       = None
    status:       Optional[str]       = None
    mockup_html:  Optional[str]       = None
    # Hormozi-Spec Section-Plan — erlaubt Frontend-Editor (Lücke 1 vs Relume).
    # Werte werden gegen SECTION_CATALOG gefiltert; unbekannte Keys verworfen.
    sections:     Optional[List[str]] = None
    # Relume-Parität R1: per-Page-KI-Prompt + User-Color-Tag.
    ai_prompt:    Optional[str]       = None
    color_tag:    Optional[str]       = None
    # ist_pflichtseite is intentionally excluded – cannot be changed via API


class ReorderItem(BaseModel):
    id:        int
    position:  int
    parent_id: Optional[int] = None


# ── Serializer ─────────────────────────────────────────────────────────────────

def _serialize(p: SitemapPage) -> dict:
    raw_sections = getattr(p, "sections_json", None)
    sections: List[str] = []
    if raw_sections:
        try:
            parsed = json.loads(raw_sections)
            if isinstance(parsed, list):
                sections = [str(s) for s in parsed if s]
        except (json.JSONDecodeError, TypeError):
            sections = []
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
        # KI-generierter Content
        "ki_h1":               getattr(p, "ki_h1",               None) or "",
        "ki_hero_text":        getattr(p, "ki_hero_text",        None) or "",
        "ki_abschnitt_text":   getattr(p, "ki_abschnitt_text",   None) or "",
        "ki_cta":              getattr(p, "ki_cta",              None) or "",
        "ki_meta_title":       getattr(p, "ki_meta_title",       None) or "",
        "ki_meta_description": getattr(p, "ki_meta_description", None) or "",
        "content_generated":   bool(getattr(p, "content_generated", False)),
        # Hormozi-Spec Section-Plan (Wireframe-Mapping)
        "sections":            sections,
        # Phase-1 Crawl-Import-Metadaten
        "source":              getattr(p, "source",       None) or "manual",
        "original_url":        getattr(p, "original_url", None) or "",
        "replaces_page_ids":   _parse_id_list(getattr(p, "replaces_page_ids", None)),
        # Relume-Parität R1
        "ai_prompt":           getattr(p, "ai_prompt", None) or "",
        "color_tag":           getattr(p, "color_tag", None) or "",
        # Relume-Parität R2 Feature 4
        "variant":             getattr(p, "variant", None) or "primary",
    }


def _parse_id_list(raw: Optional[str]) -> List[int]:
    """Parse a JSON-encoded INT-array; tolerate junk by returning []."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(parsed, list):
        return []
    out: List[int] = []
    for item in parsed:
        try:
            out.append(int(item))
        except (TypeError, ValueError):
            continue
    return out


# ── Pflichtseiten ──────────────────────────────────────────────────────────────

# Immer-Pflichtseiten (für jeden Kunden)
PFLICHTSEITEN_IMMER = [
    {
        "page_name": "Impressum",
        "page_type": "rechtlich",
        "position": 90,
        "zweck": "Gesetzlich vorgeschriebene Pflichtangaben gemäß §5 TMG",
        "ziel_keyword": "Impressum",
        "bedingung": None,
    },
    {
        "page_name": "Datenschutzerklärung",
        "page_type": "rechtlich",
        "position": 91,
        "zweck": "Informationen zur Datenverarbeitung gemäß DSGVO",
        "ziel_keyword": "Datenschutz",
        "bedingung": None,
    },
]

# Bedingte Pflichtseiten (nur unter Voraussetzungen)
PFLICHTSEITEN_BEDINGT = [
    {
        "page_name": "Barrierefreiheitserklärung",
        "page_type": "rechtlich",
        "position": 92,
        "zweck": "Konformitätserklärung gemäß BFSG / BITV 2.0 — erforderlich für öffentliche Stellen und B2C-Websites ab 28.06.2025",
        "ziel_keyword": "Barrierefreiheit",
        "bedingung": "bfsg",
    },
    {
        "page_name": "AGB",
        "page_type": "rechtlich",
        "position": 93,
        "zweck": "Allgemeine Geschäftsbedingungen — erforderlich bei Online-Shop / E-Commerce",
        "ziel_keyword": "AGB",
        "bedingung": "ecommerce",
    },
]

# Alle Pflichtseiten kombiniert (für Abwärtskompatibilität)
PFLICHTSEITEN = PFLICHTSEITEN_IMMER + PFLICHTSEITEN_BEDINGT

# Optionale Zusatzseiten (Vorschlagskatalog)
OPTIONALE_SEITEN = [
    # Basis-Seiten
    {"page_name": "Startseite",     "page_type": "startseite", "position":  1, "zweck": "Hauptseite des Auftritts — erster Eindruck, Hero-Bereich, USP, CTA",                    "ziel_keyword": "Startseite Home",               "empfohlen_fuer": ["alle"],                                           "gruppe": "basis"},
    {"page_name": "Leistungen",     "page_type": "leistung",   "position":  2, "zweck": "Übersicht aller angebotenen Leistungen — zentraler SEO-Treiber",                         "ziel_keyword": "Leistungen Angebote",            "empfohlen_fuer": ["alle"],                                           "gruppe": "basis"},
    {"page_name": "Über uns",       "page_type": "info",       "position":  3, "zweck": "Geschichte, Team und Werte des Unternehmens — baut Vertrauen auf",                       "ziel_keyword": "Über uns Unternehmen",           "empfohlen_fuer": ["alle"],                                           "gruppe": "basis"},
    {"page_name": "Kontakt",        "page_type": "conversion", "position":  4, "zweck": "Kontaktformular, Adresse, Öffnungszeiten — Hauptkonversionspunkt",                       "ziel_keyword": "Kontakt Anfrage",                "empfohlen_fuer": ["alle"],                                           "gruppe": "basis"},
    {"page_name": "Landingpage",    "page_type": "conversion", "position":  5, "zweck": "Kampagnen-spezifische Zielseite für Ads / Aktionen — hohe Konversionsrate",              "ziel_keyword": "Angebot Aktion",                 "empfohlen_fuer": ["alle"],                                           "gruppe": "basis"},
    # Vertrauen & Inhalte
    {"page_name": "FAQ",            "page_type": "info",       "position": 10, "zweck": "Häufige Fragen und Antworten — stärkt Vertrauen, reduziert Supportaufwand",              "ziel_keyword": "FAQ häufige Fragen",             "empfohlen_fuer": ["alle"],                                           "gruppe": "inhalte"},
    {"page_name": "Blog / News",    "page_type": "info",       "position": 11, "zweck": "Aktuelle Beiträge, Neuigkeiten und Expertise — gut für SEO und Reichweite",              "ziel_keyword": "News Aktuelles Blog",            "empfohlen_fuer": ["alle"],                                           "gruppe": "inhalte"},
    {"page_name": "Galerie",        "page_type": "vertrauen",  "position": 12, "zweck": "Fotos abgeschlossener Projekte — visueller Beweis der Qualität",                         "ziel_keyword": "Galerie Referenzbilder Projekte","empfohlen_fuer": ["handwerk", "bau", "garten", "maler", "fotograf"], "gruppe": "inhalte"},
    {"page_name": "Referenzen",     "page_type": "vertrauen",  "position": 13, "zweck": "Kundenstimmen und abgeschlossene Projekte — Social Proof",                               "ziel_keyword": "Referenzen Kundenprojekte",      "empfohlen_fuer": ["alle"],                                           "gruppe": "inhalte"},
    {"page_name": "Team",           "page_type": "vertrauen",  "position": 14, "zweck": "Mitarbeitervorstellung — schafft Nähe, Vertrauen und Persönlichkeit",                    "ziel_keyword": "Team Mitarbeiter Experten",      "empfohlen_fuer": ["alle"],                                           "gruppe": "inhalte"},
    # Conversion & Spezial
    {"page_name": "Preise",         "page_type": "conversion", "position": 20, "zweck": "Preistransparenz — reduziert Anfragehürde, qualifiziert Leads vorab",                   "ziel_keyword": "Preise Kosten Angebot",          "empfohlen_fuer": ["dienstleistung", "beratung", "coaching"],         "gruppe": "conversion"},
    {"page_name": "Karriere / Jobs","page_type": "info",       "position": 21, "zweck": "Offene Stellen und Ausbildungsplätze — Fachkräftegewinnung",                            "ziel_keyword": "Jobs Karriere Ausbildung",       "empfohlen_fuer": ["alle"],                                           "gruppe": "conversion"},
    {"page_name": "Online-Shop",    "page_type": "conversion", "position": 22, "zweck": "Produkte online kaufen — E-Commerce-Integration",                                       "ziel_keyword": "Shop Produkte bestellen kaufen", "empfohlen_fuer": ["handel", "ecommerce"],                            "gruppe": "conversion"},
    {"page_name": "Notfallservice", "page_type": "conversion", "position": 23, "zweck": "24h Notdienst — wichtig für Handwerker mit Bereitschaftsdienst",                        "ziel_keyword": "Notfall Notdienst 24h",          "empfohlen_fuer": ["elektriker", "sanitaer", "heizung", "schlosserei"],"gruppe": "conversion"},
    {"page_name": "Terminbuchung",  "page_type": "conversion", "position": 24, "zweck": "Online-Terminbuchung — reduziert Telefon-Aufwand, erhöht Konversion",                  "ziel_keyword": "Termin buchen online",           "empfohlen_fuer": ["dienstleistung", "beratung", "handwerk"],         "gruppe": "conversion"},
]


def _ensure_pflichtseiten(lead_id: int, db: Session) -> None:
    """Insert missing Immer-Pflichtseiten for a lead (idempotent). Bedingte Pflichtseiten are added via /suggest."""
    pflicht_count = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.ist_pflichtseite.is_(True))
        .count()
    )
    if pflicht_count >= len(PFLICHTSEITEN_IMMER):
        return

    existing_names = {
        p.page_name
        for p in db.query(SitemapPage).filter(SitemapPage.lead_id == lead_id).all()
    }
    for seite in PFLICHTSEITEN_IMMER:
        if seite["page_name"] not in existing_names:
            default_sections = DEFAULT_SECTIONS_BY_PAGETYPE.get(
                seite["page_type"], DEFAULT_SECTIONS_BY_PAGETYPE["info"]
            )
            db.add(SitemapPage(
                lead_id=lead_id,
                page_name=seite["page_name"],
                page_type=seite["page_type"],
                position=seite["position"],
                zweck=seite.get("zweck", ""),
                ziel_keyword=seite.get("ziel_keyword", ""),
                status="geplant",
                ist_pflichtseite=True,
                sections_json=json.dumps(default_sections, ensure_ascii=False),
                variant="primary",
            ))
    db.commit()


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/{lead_id}")
def get_sitemap(
    lead_id: int,
    variant: str = "primary",
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Return sitemap pages for a lead in the given variant slot.

    `variant` query param:
      - 'primary' (default): live sitemap incl. Pflichtseiten + Bestand + KI
      - 'variant': nur die KI-Alternativ-Vorschläge (kein Pflicht/Bestand)
    """
    if variant not in ("primary", "variant"):
        variant = "primary"
    # Pflichtseiten nur im primary-Slot sicherstellen
    if variant == "primary":
        _ensure_pflichtseiten(lead_id, db)
    pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.variant == variant)
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
        allowed = {"zweck", "notizen", "status", "sections", "ai_prompt", "color_tag"}
        updates = {k: v for k, v in updates.items() if k in allowed}
    # color_tag muss Hex-Format sein oder leerer String — sonst verwerfen
    if "color_tag" in updates:
        ct = updates["color_tag"]
        if ct and not (isinstance(ct, str) and len(ct) == 7 and ct.startswith("#")):
            updates["color_tag"] = None
    # `sections` ist Frontend-friendly (List[str]) — Backend-Spalte ist
    # `sections_json` (JSON-String). Validierung gegen SECTION_CATALOG, damit
    # kein Garbage in der DB landet.
    if "sections" in updates:
        raw_sections = updates.pop("sections") or []
        cleaned = [str(s) for s in raw_sections if isinstance(s, str) and s in SECTION_CATALOG]
        page.sections_json = json.dumps(cleaned, ensure_ascii=False)
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
    _=Depends(require_any_auth),
):
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
    {"page_name": "Startseite",                 "page_type": "startseite", "position": 0,  "parent_id": None, "zweck": "Erster Eindruck, klare Botschaft",                                               "ziel_keyword": "", "cta_text": "Jetzt anfragen",    "cta_ziel": "kontakt"},
    {"page_name": "Leistungen",                 "page_type": "leistung",   "position": 1,  "parent_id": None, "zweck": "Übersicht aller Leistungen",                                                      "ziel_keyword": "", "cta_text": "Mehr erfahren",     "cta_ziel": "kontakt"},
    {"page_name": "Leistung 1",                 "page_type": "leistung",   "position": 2,  "parent_id": 1,    "zweck": "Detail-Seite erste Leistung",                                                     "ziel_keyword": "", "cta_text": "Angebot anfordern", "cta_ziel": "kontakt"},
    {"page_name": "Leistung 2",                 "page_type": "leistung",   "position": 3,  "parent_id": 1,    "zweck": "Detail-Seite zweite Leistung",                                                    "ziel_keyword": "", "cta_text": "Angebot anfordern", "cta_ziel": "kontakt"},
    {"page_name": "Über uns",                   "page_type": "vertrauen",  "position": 4,  "parent_id": None, "zweck": "Vertrauen aufbauen, Team vorstellen",                                             "ziel_keyword": "", "cta_text": "Kontakt aufnehmen", "cta_ziel": "kontakt"},
    {"page_name": "Kontakt",                    "page_type": "conversion", "position": 5,  "parent_id": None, "zweck": "Leadgenerierung, Kontaktformular",                                                "ziel_keyword": "", "cta_text": "Nachricht senden",  "cta_ziel": "kontakt"},
    {"page_name": "Über uns & Informationen",   "page_type": "ground",     "position": 99, "parent_id": None, "zweck": "Maschinenlesbare Informationsseite für KI-Systeme (GEO-Optimierung)",             "ziel_keyword": "",  "cta_text": "Jetzt Kontakt aufnehmen", "cta_ziel": "kontakt", "notizen": "Ground Page — GEO/KI-Optimierung"},
]


def _insert_pages(
    lead_id: int,
    raw_pages: list,
    db: Session,
    source: str = "ki_generated",
    variant: str = "primary",
) -> list:
    """Persist a list of page dicts, return serialized results.

    `source` is written into sitemap_pages.source. Defaults to 'ki_generated'
    because all current callers are the AI generator (or its fallback). Each
    raw_page may include a `replaces_page_ids` list — if present and non-empty,
    it is JSON-encoded into sitemap_pages.replaces_page_ids (Phase-3 mapping
    of "this AI suggestion replaces these crawled bestand pages").
    `variant` ('primary' | 'variant') determines which slot the pages live in
    — see the R2-Variants doc on the column.
    """
    created = []
    id_map: dict[int, int] = {}  # old position-based index → new DB id (for parent linking)

    for i, p in enumerate(raw_pages):
        sections = _resolve_sections(p)
        replaces_raw = p.get("replaces_page_ids")
        replaces_json: Optional[str] = None
        if isinstance(replaces_raw, list) and replaces_raw:
            cleaned_ids: list[int] = []
            for item in replaces_raw:
                try:
                    cleaned_ids.append(int(item))
                except (TypeError, ValueError):
                    continue
            if cleaned_ids:
                replaces_json = json.dumps(cleaned_ids)
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
            sections_json=json.dumps(sections, ensure_ascii=False),
            source=source,
            replaces_page_ids=replaces_json,
            variant=variant,
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
    body: dict = Body(default={}),
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generate sitemap pages via Claude AI (or fallback template).

    Optional body:
      - "page_count": N — geclamped auf 3..15. Default: KI entscheidet (5-8).
      - "as_variant": bool — true = parallele Alternative, false = neue Live.
    """
    as_variant = bool((body or {}).get("as_variant"))
    target_variant = "variant" if as_variant else "primary"
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    # Tor 1: Briefing muss vom Kunden freigegeben sein
    proj_row = db.execute(
        text(
            "SELECT briefing_approved_at FROM projects "
            "WHERE lead_id=:lid ORDER BY id DESC LIMIT 1"
        ),
        {"lid": lead_id},
    ).fetchone()
    if not proj_row or not proj_row[0]:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "BRIEFING_NOT_APPROVED",
                "message": "Das Briefing wurde noch nicht freigegeben. Bitte zuerst eine Freigabe-E-Mail senden und die Kundenfreigabe einholen.",
            },
        )

    # Step 1: Pflichtseiten nur bei primary-Generation sicherstellen.
    # Pflichtseiten leben ausschließlich im Primary-Slot — der Variant-Tab
    # zeigt nur die KI-Alternativvorschläge.
    if not as_variant:
        _ensure_pflichtseiten(lead_id, db)

    briefing      = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    gewerk        = (getattr(briefing, "gewerk",        None) if briefing else None) or getattr(lead, "trade", None) or "Handwerk"
    leistungen    = (getattr(briefing, "leistungen",    None) if briefing else None) or ""
    einzugsgebiet = (getattr(briefing, "einzugsgebiet", None) if briefing else None) or getattr(lead, "city", None) or "Deutschland"
    usp           = (getattr(briefing, "usp",           None) if briefing else None) or ""
    zielgruppe    = (getattr(briefing, "zielgruppe",    None) if briefing else None) or "Privatkunden und Gewerbekunden"
    wunschseiten  = (getattr(briefing, "wunschseiten",  None) if briefing else None) or ""
    city          = getattr(lead, "city", None) or "Deutschland"
    company       = getattr(lead, "company_name", None) or getattr(lead, "display_name", None) or ""

    # Gecrawlte Seiten der alten Website laden
    old_pages_summary = ""
    try:
        from sqlalchemy import text as _text
        crawled = db.execute(
            _text("""
                SELECT url, h1, title
                FROM website_content_cache
                WHERE customer_id = :lid
                ORDER BY scraped_at DESC
                LIMIT 12
            """),
            {"lid": lead_id},
        ).fetchall()
        if crawled:
            old_pages_summary = "Seiten der alten Website (gecrawlt):\n" + "\n".join(
                [f"- {r[2] or r[1] or r[0]}" for r in crawled[:10]]
            )
    except Exception:
        old_pages_summary = ""

    # Step 2: Frühere KI-Vorschläge im Ziel-Slot (primary oder variant) löschen.
    # Bestand und manuelle Pages bleiben erhalten. Bei variant-Generation wird
    # primary nicht angefasst.
    db.query(SitemapPage).filter(
        SitemapPage.lead_id == lead_id,
        SitemapPage.ist_pflichtseite.is_(False),
        SitemapPage.source == "ki_generated",
        SitemapPage.variant == target_variant,
    ).delete(synchronize_session=False)
    db.commit()

    # Phase 3: Bestand (source='crawled') als Prompt-Input für die KI lesen.
    # Pro Bestandsseite gibt der Prompt id/name/type/url, damit die KI im
    # Output `replaces_page_ids: [<bestands-id>, ...]` setzen kann.
    # Bestand lebt immer in primary, deshalb keine variant-Filter hier.
    crawled_pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.source == "crawled")
        .order_by(SitemapPage.position, SitemapPage.id)
        .all()
    )
    bestand_section = ""
    if crawled_pages:
        lines = ["BESTANDS-SEITEN (Phase-1 Crawl der aktuellen Website):"]
        for cp in crawled_pages[:30]:
            url = cp.original_url or ""
            ptype = cp.page_type or "sonstige"
            lines.append(f"  ID {cp.id} | {cp.page_name} | {ptype} | {url}")
        bestand_section = "\n".join(lines)

    # Step 3: KI oder Fallback
    api_key = os.getenv("ANTHROPIC_API_KEY")
    source = "fallback"
    if not api_key:
        _insert_pages(lead_id, _FALLBACK_PAGES, db, variant=target_variant)
    else:
        wunschseiten_hint = (
            f"\nDer Kunde hat folgende Seiten gewünscht: {wunschseiten}"
            if wunschseiten else ""
        )
        old_pages_hint = (
            f"\n{old_pages_summary}"
            if old_pages_summary else ""
        )
        bestand_hint = f"\n\n{bestand_section}" if bestand_section else ""
        bestand_mapping_rule = (
            "\n- Wenn BESTANDS-SEITEN vorhanden sind: pro neuer Inhaltsseite "
            "OPTIONAL `replaces_page_ids: [<id>, ...]` setzen mit den IDs der "
            "Bestandsseiten, die diese neue Seite konsolidiert oder ersetzt. "
            "Leer lassen / weglassen wenn die neue Seite keinen Bestandsbezug hat. "
            "Eine Bestandsseite darf von mehreren neuen Pages referenziert werden."
            if bestand_section else ""
        )
        # Section-Katalog kompakt für den Prompt (key: kurzbeschreibung)
        section_catalog_text = "\n".join(
            f"  - {key}: {desc}" for key, desc in SECTION_CATALOG.items()
        )
        # User-gewählte Seitenanzahl (R1) — geclamped auf vernünftige Range.
        try:
            page_count = int((body or {}).get("page_count") or 0)
        except (TypeError, ValueError):
            page_count = 0
        if page_count < 3 or page_count > 15:
            page_count_text = "5-8"
        else:
            page_count_text = str(page_count)
        prompt = (
            "Du bist ein Website-Stratege für deutsche Handwerksbetriebe.\n"
            f"Erstelle eine optimale Sitemap mit {page_count_text} INHALTLICHEN Seiten für diesen Betrieb.\n"
            "Pro Seite gibst du auch an, WELCHE Conversion-Sections (siehe Section-Katalog unten) "
            "in welcher Reihenfolge auf der Seite stehen sollen — basierend auf Hormozi-Conversion-Spec.\n\n"
            "WICHTIG — NICHT einschließen (werden automatisch ergänzt):\n"
            "Impressum, Datenschutz, AGB, Barrierefreiheit, Cookie-Hinweise\n\n"
            f"UNTERNEHMEN:\n"
            f"- Firma: {company}\n"
            f"- Gewerk/Branche: {gewerk}\n"
            f"- Leistungen: {leistungen}\n"
            f"- Region/Einzugsgebiet: {einzugsgebiet}\n"
            f"- USP (Alleinstellungsmerkmal): {usp or '–'}\n"
            f"- Zielgruppe: {zielgruppe}\n"
            f"{wunschseiten_hint}"
            f"{old_pages_hint}"
            f"{bestand_hint}\n\n"
            "SECTION-KATALOG (du wählst pro Page eine geordnete Liste aus diesen Keys):\n"
            f"{section_catalog_text}\n\n"
            "REGELN FÜR DIE SITEMAP:\n"
            "- Position 0 = Startseite (immer)\n"
            "- Jede Hauptleistung bekommt eine eigene Seite (page_type='leistung')\n"
            "- Vertrauensseite einplanen (Referenzen, Team, Über uns)\n"
            "- Kontaktseite immer als letzte Inhaltsseite\n"
            "- ziel_keyword auf die wichtigsten SEO-Begriffe abstimmen\n"
            "- Branchenspezifisch denken: Was sucht die Zielgruppe wirklich?"
            f"{bestand_mapping_rule}\n\n"
            "REGELN FÜR DIE SECTION-AUSWAHL pro Page:\n"
            "- Startseite: hero_value_equation am Anfang, mind. offer_stack ODER service_grid, "
            "  trust_strip, fallstudien_3, guarantee_block, faq, cta_final am Ende. Reihenfolge wichtig.\n"
            "- Leistung: hero_service am Anfang, problem, offer_stack (Service-spezifisch), "
            "  process_steps, fallstudien_3, guarantee_block, faq_service, cta_final am Ende.\n"
            "- Vertrauen: hero_minimal, team, fallstudien_3, trust_strip, cta_inline.\n"
            "- Conversion (Landingpage): hero_minimal, offer_stack, guarantee_block, urgency_block, "
            "  contact_form, cta_final.\n"
            "- Ground (GEO): hero_minimal, service_grid, faq, contact_form.\n"
            "- Info-Seite: hero_minimal, content_richtext, faq, cta_inline.\n"
            "- Pro Seite mind. 4, max. 9 Sections. Keine Duplikate. cta_final immer am Ende von "
            "  Conversion-relevanten Pages.\n\n"
            "PFLICHT: Füge IMMER genau eine Seite mit page_type='ground' ein (position 99):\n"
            '{ "page_name": "Über uns & Informationen", "page_type": "ground", "position": 99, '
            '"zweck": "Maschinenlesbare Informationsseite für KI-Systeme (GEO-Optimierung)", '
            f'"ziel_keyword": "{gewerk} {einzugsgebiet} Informationen", '
            '"cta_text": "Jetzt Kontakt aufnehmen", "cta_ziel": "kontakt", "parent_id": null, '
            '"sections": ["hero_minimal","service_grid","faq","contact_form"] }\n\n'
            "Antworte NUR als JSON-Array — kein Markdown, keine Erklärungen:\n"
            '[{ "page_name": "", "page_type": "startseite|leistung|info|vertrauen|conversion|ground", '
            '"zweck": "", "ziel_keyword": "", "cta_text": "", "cta_ziel": "kontakt|formular|tel", '
            '"position": 0, "parent_id": null, '
            '"sections": ["hero_xxx","..."], '
            '"replaces_page_ids": [] }]'
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
            _insert_pages(lead_id, raw_pages, db, variant=target_variant)
            source = "ai"
        except Exception as exc:
            logger.warning("Sitemap KI-Generierung fehlgeschlagen, Fallback: %s", exc)
            _insert_pages(lead_id, _FALLBACK_PAGES, db, variant=target_variant)

    # Ensure at least one ground page exists regardless of AI/fallback source.
    # Bei variant-Generation übernehmen wir die ground-Page aus primary —
    # wir brauchen sie im Variant-Tab nicht zu duplizieren.
    if not as_variant:
        has_ground = db.query(SitemapPage).filter(
            SitemapPage.lead_id == lead_id,
            SitemapPage.page_type == "ground",
            SitemapPage.variant == "primary",
        ).first()
    else:
        has_ground = True  # skip — primary kümmert sich
    if not has_ground:
        _insert_pages(lead_id, [{
            "page_name": "Über uns & Informationen",
            "page_type": "ground",
            "position": 99,
            "zweck": "Maschinenlesbare Informationsseite für KI-Systeme (GEO-Optimierung)",
            "ziel_keyword": f"{gewerk} {city} Informationen",
            "cta_text": "Jetzt Kontakt aufnehmen",
            "cta_ziel": "kontakt",
            "notizen": "Ground Page — GEO/KI-Optimierung",
        }], db)

    # Sitemap des Ziel-Slots zurückgeben (primary inkl. Pflicht/Bestand,
    # variant nur die KI-Vorschläge der Alternative).
    all_pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.variant == target_variant)
        .order_by(SitemapPage.position)
        .all()
    )
    return {"pages": [_serialize(p) for p in all_pages], "source": source, "variant": target_variant}


# ── ENDPOINT: Continue-generating (R2 Relume-Parität) ─────────────────────────

@router.post("/{lead_id}/generate-more")
async def generate_more_pages(
    lead_id: int,
    body: dict = Body(default={}),
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Append N additional content pages via Claude AI.

    Im Gegensatz zu /generate werden hier KEINE bestehenden Pages gelöscht.
    Body: {"additional_pages": N}, geclamped auf 1..10. Default 3.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    try:
        n = int((body or {}).get("additional_pages") or 3)
    except (TypeError, ValueError):
        n = 3
    n = max(1, min(10, n))

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="KI-API nicht konfiguriert")

    # generate-more arbeitet nur am primary-Slot — wer Alternativen will, nimmt
    # /generate mit as_variant=true.
    existing = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.variant == "primary")
        .order_by(SitemapPage.position)
        .all()
    )
    existing_summary = "\n".join(f"- {p.page_name} ({p.page_type})" for p in existing) or "(leer)"

    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    company   = getattr(lead, "company_name", "") or ""
    gewerk    = (getattr(briefing, "gewerk", None) if briefing else None) or getattr(lead, "trade", None) or "Handwerk"
    leistungen = (getattr(briefing, "leistungen", None) if briefing else None) or ""

    prompt = (
        "Du bist ein Website-Stratege für deutsche Handwerksbetriebe.\n"
        f"Schlage GENAU {n} WEITERE Inhaltsseiten für die bestehende Sitemap vor.\n"
        "WICHTIG: KEINE Duplikate zu existierenden Seiten anlegen, KEINE Pflichtseiten "
        "(Impressum, Datenschutz, AGB, Barrierefreiheit) — die werden separat verwaltet.\n\n"
        f"UNTERNEHMEN:\n- Firma: {company}\n- Gewerk: {gewerk}\n- Leistungen: {leistungen}\n\n"
        f"BEREITS BESTEHENDE SEITEN:\n{existing_summary}\n\n"
        "Antworte NUR als JSON-Array (kein Markdown):\n"
        '[{ "page_name":"", "page_type":"leistung|info|vertrauen|conversion|sonstige", '
        '"zweck":"", "ziel_keyword":"", "cta_text":"", "cta_ziel":"kontakt", '
        '"sections":["hero_minimal","content_richtext","cta_inline"] }]'
    )

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key, max_retries=0, timeout=60.0)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = "\n".join(line for line in raw.splitlines() if not line.strip().startswith("```")).strip()
        new_pages = json.loads(raw)
        if not isinstance(new_pages, list) or not new_pages:
            raise ValueError("Erwarte nicht-leeres JSON-Array")
    except Exception as exc:
        logger.exception("generate-more failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"KI-Generation fehlgeschlagen: {exc}")

    max_pos = max((p.position or 0 for p in existing), default=0)
    for i, p_data in enumerate(new_pages):
        # parent bleibt None (top-level) — KI hat keine IDs zum Verlinken
        p_data["position"] = max_pos + 1 + i
        p_data["parent_id"] = None

    _insert_pages(lead_id, new_pages, db, source="ki_generated", variant="primary")

    all_pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.variant == "primary")
        .order_by(SitemapPage.position)
        .all()
    )
    return {"added": len(new_pages), "pages": [_serialize(p) for p in all_pages]}


# ── ENDPOINTS: Variant-Slot-Verwaltung (R2 Feature 4) ─────────────────────────

@router.post("/{lead_id}/promote-variant")
def promote_variant(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Macht aus dem 'variant'-Slot den neuen 'primary'-Slot.

    Schritte:
    1. Alle primary-Pages mit source='ki_generated' und !ist_pflichtseite löschen.
       Bestand (source='crawled') und manuelle Pages bleiben primary, weil
       sie variant-agnostisch sind.
    2. Alle 'variant'-Pages → variant='primary' setzen.
    """
    has_variant = db.query(SitemapPage).filter(
        SitemapPage.lead_id == lead_id,
        SitemapPage.variant == "variant",
    ).first()
    if not has_variant:
        raise HTTPException(status_code=400, detail="Keine Variante zum Übernehmen vorhanden")

    db.query(SitemapPage).filter(
        SitemapPage.lead_id == lead_id,
        SitemapPage.variant == "primary",
        SitemapPage.source == "ki_generated",
        SitemapPage.ist_pflichtseite.is_(False),
    ).delete(synchronize_session=False)

    db.query(SitemapPage).filter(
        SitemapPage.lead_id == lead_id,
        SitemapPage.variant == "variant",
    ).update({SitemapPage.variant: "primary"}, synchronize_session=False)

    db.commit()
    pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.variant == "primary")
        .order_by(SitemapPage.position)
        .all()
    )
    return {"promoted": True, "pages": [_serialize(p) for p in pages]}


@router.delete("/{lead_id}/discard-variant", status_code=204)
def discard_variant(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Verwirft alle 'variant'-Pages eines Leads. Primary bleibt unangetastet."""
    db.query(SitemapPage).filter(
        SitemapPage.lead_id == lead_id,
        SitemapPage.variant == "variant",
    ).delete(synchronize_session=False)
    db.commit()


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


# ── Phase-1 Crawl-Import: Bestands-Website → sitemap_pages ────────────────────

# URL-Path-Keywords, die eine Pflichtseite kennzeichnen.
# Wert = (page_type, ist_pflichtseite).
_PFLICHT_KEYWORDS: dict[str, tuple[str, bool]] = {
    "impressum":             ("rechtlich", True),
    "datenschutz":           ("rechtlich", True),
    "datenschutzerklaerung": ("rechtlich", True),
    "agb":                   ("rechtlich", True),
    "barrierefreiheit":      ("rechtlich", True),
    "widerruf":              ("rechtlich", True),
}

# Page-Type-Heuristik: tuple_of_keywords → page_type
_TYPE_HEURISTICS: list[tuple[tuple[str, ...], str]] = [
    (("leistung", "service", "angebot", "produkt"),                  "leistung"),
    (("kontakt", "contact", "anfrage"),                              "conversion"),
    (("ueber", "about", "team", "unternehmen"),                      "vertrauen"),
    (("referenz", "projekt", "fallstudie", "case"),                  "vertrauen"),
    (("blog", "news", "aktuell", "magazin", "beitrag", "artikel", "info"), "info"),
]


def _humanize_slug(slug: str) -> str:
    """`wallbox-installation` → `Wallbox Installation`."""
    return slug.replace("-", " ").replace("_", " ").strip().title()


def _classify_path(segments: list[str]) -> tuple[str, bool]:
    """Map URL-path segments to (page_type, ist_pflichtseite)."""
    joined = "/".join(segments).lower()
    for kw, val in _PFLICHT_KEYWORDS.items():
        if kw in joined:
            return val
    for keywords, ptype in _TYPE_HEURISTICS:
        if any(kw in joined for kw in keywords):
            return ptype, False
    return "sonstige", False


def _import_urls_as_pages(
    lead_id: int,
    start_url: str,
    urls: list[str],
    db: Session,
) -> int:
    """Convert a flat URL list into a SitemapPage hierarchy.

    Hierarchy comes from URL-path depth: `/leistungen/wallbox` becomes a child
    of `/leistungen` (or root if `/leistungen` is missing). Pages are written
    in path-depth order so parent IDs are available before children reference
    them.
    """
    from urllib.parse import urlparse

    base_netloc = urlparse(start_url).netloc.lower().replace("www.", "")

    # Normalize + dedupe by path
    seen: set[str] = set()
    items: list[tuple[str, str, list[str], int]] = []
    for raw in urls:
        parsed = urlparse(raw)
        netloc = parsed.netloc.lower().replace("www.", "")
        if netloc != base_netloc:
            continue
        path = parsed.path.rstrip("/").lower()
        if path in seen:
            continue
        seen.add(path)
        segments = [s for s in path.split("/") if s]
        items.append((raw, path, segments, len(segments)))

    # Root first, then by path alphabetically
    items.sort(key=lambda x: (x[3], x[1]))

    path_to_id: dict[str, int] = {}
    pos = 0
    for url, path, segments, _depth in items:
        if not segments:
            page_name, page_type, ist_pflicht, parent_id = "Startseite", "startseite", False, None
        else:
            page_name = _humanize_slug(segments[-1])
            page_type, ist_pflicht = _classify_path(segments)
            parent_path = "/" + "/".join(segments[:-1]) if len(segments) > 1 else ""
            parent_id = path_to_id.get(parent_path)

        page = SitemapPage(
            lead_id=lead_id,
            parent_id=parent_id,
            position=pos,
            page_name=page_name[:100] or "Seite",
            page_type=page_type,
            ist_pflichtseite=ist_pflicht,
            status="live",
            source="crawled",
            original_url=url,
            variant="primary",
        )
        db.add(page)
        db.flush()
        path_to_id[path] = page.id
        pos += 1

    return len(items)


@router.post("/{lead_id}/import-existing")
def import_existing_sitemap(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Crawl the lead's website and import the live page structure.

    Source preference:
      1. Reuse existing CrawlResult rows for this lead (fast).
      2. Otherwise live-crawl via `crawler_service.crawl_website` (~10-30s, max 30 pages).

    Idempotent: existing `source='crawled'` rows for this lead are deleted
    first. Manual / KI-generated pages are kept.
    """
    from database import CrawlResult

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    start_url = (lead.website_url or "").strip()
    if not start_url:
        raise HTTPException(
            status_code=422,
            detail={"code": "NO_WEBSITE_URL",
                    "message": "Lead hat keine Website-URL hinterlegt — Bestand kann nicht gecrawlt werden."},
        )
    if not start_url.startswith("http"):
        start_url = "https://" + start_url

    cached_urls = [
        r.url for r in db.query(CrawlResult).filter(
            CrawlResult.customer_id == lead_id,
            CrawlResult.status_code == 200,
        ).all()
    ]

    used_cache = bool(cached_urls)
    if used_cache:
        urls = cached_urls
    else:
        from services.crawler_service import crawl_website
        try:
            results = crawl_website(start_url, max_pages=30)
        except Exception as e:
            logger.exception("Crawl für Lead %s fehlgeschlagen", lead_id)
            raise HTTPException(
                status_code=502,
                detail={"code": "CRAWL_FAILED",
                        "message": f"Crawl der Website fehlgeschlagen: {e}"},
            )
        urls = [r["url"] for r in results if r.get("status_code") == 200]

    if not urls:
        raise HTTPException(
            status_code=502,
            detail={"code": "NO_PAGES_FOUND",
                    "message": "Keine erreichbaren Seiten auf der Website gefunden."},
        )

    # Idempotenz: bestehende crawled-Pages für diesen Lead löschen
    db.query(SitemapPage).filter(
        SitemapPage.lead_id == lead_id,
        SitemapPage.source == "crawled",
    ).delete(synchronize_session=False)
    db.commit()

    imported = _import_urls_as_pages(lead_id, start_url, urls, db)
    db.commit()

    pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id)
        .order_by(SitemapPage.position, SitemapPage.id)
        .all()
    )
    return {
        "imported":   imported,
        "url_source": "cache" if used_cache else "live_crawl",
        "start_url":  start_url,
        "pages":      [_serialize(p) for p in pages],
    }


@router.get("/{lead_id}/suggest")
def suggest_pages(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Return bedingte Pflichtseiten + optional pages as suggestions for the admin to pick from."""
    existing_names = {
        p.page_name
        for p in db.query(SitemapPage).filter(SitemapPage.lead_id == lead_id).all()
    }

    bedingte = [
        {**s, "bereits_vorhanden": s["page_name"] in existing_names, "kategorie": "bedingt_pflicht"}
        for s in PFLICHTSEITEN_BEDINGT
    ]
    optional = [
        {**s, "bereits_vorhanden": s["page_name"] in existing_names, "kategorie": "optional"}
        for s in OPTIONALE_SEITEN
    ]

    return {"bedingte_pflichtseiten": bedingte, "optionale_seiten": optional}


@router.get("/{lead_id}/ki-empfehlung")
async def ki_seitenempfehlung(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Let Claude generate individual page recommendations based on this customer's briefing."""
    import os, httpx, json as _json

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    briefing   = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    existing   = [p.page_name for p in db.query(SitemapPage).filter(SitemapPage.lead_id == lead_id).all()]
    gewerk     = (getattr(briefing, "gewerk",      None) if briefing else None) or (getattr(lead, "trade", None) or "Handwerk")
    leistungen = (getattr(briefing, "leistungen",  None) if briefing else None) or ""
    usp        = (getattr(briefing, "usp",         None) if briefing else None) or ""
    zielgruppe = (getattr(briefing, "zielgruppe",  None) if briefing else None) or ""
    mitbewerber= (getattr(briefing, "mitbewerber", None) if briefing else None) or ""
    city       = getattr(lead, "city", None) or "Deutschland"
    company    = getattr(lead, "company_name", None) or ""

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    prompt = f"""Du bist ein Website-Stratege für Handwerksbetriebe.

KUNDE: {company}
Gewerk: {gewerk}
Stadt: {city}
Leistungen: {leistungen}
USP: {usp}
Zielgruppe: {zielgruppe}
Wettbewerber: {mitbewerber}

Bereits geplante Seiten: {', '.join(existing) or 'keine'}

Empfehle 3-5 spezifische Seiten die für DIESEN Betrieb besonders wichtig sind.
Berücksichtige Gewerk, USP und Zielgruppe — gib individuelle, nicht generische Empfehlungen.

Antworte NUR als JSON-Array:
[{{
  "page_name": "<Seitenname>",
  "page_type": "startseite|leistung|info|vertrauen|conversion|ground",
  "zweck": "<1-2 Sätze warum diese Seite für DIESEN Betrieb wichtig ist>",
  "ziel_keyword": "<Haupt-Keyword>",
  "position": <Zahl>,
  "ki_begruendung": "<Individueller Grund warum genau diese Seite für {company} sinnvoll ist>"
}}]"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1500,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        empfehlungen = _json.loads(raw)
        empfehlungen = [e for e in empfehlungen if e.get("page_name") not in existing]
        return {"empfehlungen": empfehlungen, "company": company, "gewerk": gewerk}
    except Exception as e:
        raise HTTPException(500, f"KI-Empfehlung fehlgeschlagen: {str(e)[:200]}")


@router.post("/{lead_id}/add-suggested")
def add_suggested_page(
    lead_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Add a suggested page (bedingt-Pflicht or optional) to the sitemap."""
    page_name = (body.get("page_name") or "").strip()
    if not page_name:
        raise HTTPException(400, "page_name fehlt")

    alle_vorschlaege = PFLICHTSEITEN_BEDINGT + OPTIONALE_SEITEN
    vorlage = next((s for s in alle_vorschlaege if s["page_name"] == page_name), None)
    ist_pflicht = bool(vorlage and vorlage.get("bedingung"))

    db.add(SitemapPage(
        lead_id=lead_id,
        page_name=page_name,
        page_type=body.get("page_type") or (vorlage["page_type"] if vorlage else "info"),
        position=body.get("position") or (vorlage["position"] if vorlage else 50),
        zweck=body.get("zweck") or (vorlage["zweck"] if vorlage else ""),
        ziel_keyword=body.get("ziel_keyword") or (vorlage["ziel_keyword"] if vorlage else ""),
        ist_pflichtseite=ist_pflicht,
        status="geplant",
    ))
    db.commit()
    return {"ok": True, "page_name": page_name}


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
