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

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
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
from routers.auth_router import require_any_auth, optional_auth, require_innendienst
from services.ki_aufruf import frag_modell

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



router = APIRouter(prefix="/api/sitemap", tags=["sitemap"],
                   dependencies=[Depends(require_innendienst)])


# ── Hormozi-Section-Katalog (Wireframe-Library-Mapping) ──────────────────────
# Bridge zwischen Sitemap (Stage 2) und Wireframes (Stage 3). AI wählt aus
# dieser Liste pro Page; jeder Key entspricht später einer React-Komponente
# in kompagnon/frontend/src/wireframes/sections/. Begründung pro Section
# steht in docs/conversion-spec-shk.md.
SECTION_CATALOG = {
    # Frame (Header + Footer) — global anmutend, aber als reguläre Sections
    # geführt, damit pro Page anpassbar (z.B. Landingpage ohne Hauptnav).
    "header_nav":          "Sticky-Header: Logo + Hauptnavigation + ggf. CTA-Button",

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
    "startseite":  ["header_nav", "hero_value_equation", "problem", "service_grid", "offer_stack",
                    "trust_strip", "fallstudien_3", "guarantee_block", "faq", "cta_final", "footer_legal"],
    "leistung":    ["header_nav", "hero_service", "problem", "offer_stack", "process_steps",
                    "fallstudien_3", "trust_strip", "guarantee_block", "faq_service", "cta_final", "footer_legal"],
    "vertrauen":   ["header_nav", "hero_minimal", "team", "fallstudien_3", "trust_strip", "cta_inline", "footer_legal"],
    "conversion":  ["header_nav", "hero_minimal", "offer_stack", "guarantee_block", "urgency_block",
                    "contact_form", "cta_final", "footer_legal"],
    "info":        ["header_nav", "hero_minimal", "content_richtext", "faq", "cta_inline", "footer_legal"],
    "ground":      ["header_nav", "hero_minimal", "service_grid", "faq", "contact_form", "footer_legal"],
    "rechtlich":   ["header_nav", "hero_minimal", "content_richtext", "footer_legal"],
}




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
    # Phase 4 (2026-05-07): Page-Groups. Eine Gruppe kapselt mehrere Kind-Pages
    # mit identischer Section-Struktur. Kinder *erben* group_template_sections
    # automatisch wenn ihre eigene sections_json leer/null ist.
    is_group                 = Column(Boolean, default=False)
    group_template_sections  = Column(Text,    nullable=True)


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
    # Phase 4: Page-Groups. is_group toggelt die Karte zwischen Page und
    # Gruppen-Container; group_template_sections sind die geteilten Sections,
    # die alle Kind-Pages der Gruppe erben.
    is_group:                 Optional[bool]      = None
    group_template_sections:  Optional[List[str]] = None
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
        # Phase 4 — Page-Groups
        "is_group":                bool(getattr(p, "is_group", False)),
        "group_template_sections": _parse_str_list(getattr(p, "group_template_sections", None)),
    }


def _parse_str_list(raw: Optional[str]) -> List[str]:
    """Parse a JSON-encoded string-array; tolerate junk by returning []."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(parsed, list):
        return []
    return [str(s) for s in parsed if isinstance(s, str)]


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
        # Substring (lowercase) zur Existenz-Prüfung — fängt 'Impressum',
        # 'Impressum & Kontakt', 'impressum-koblenz', etc.
        "match_kw": "impressum",
    },
    {
        "page_name": "Datenschutzerklärung",
        "page_type": "rechtlich",
        "position": 91,
        "zweck": "Informationen zur Datenverarbeitung gemäß DSGVO",
        "ziel_keyword": "Datenschutz",
        "bedingung": None,
        "match_kw": "datenschutz",  # fängt 'Datenschutz' UND 'Datenschutzerklärung'
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
    """Insert missing Immer-Pflichtseiten for a lead (idempotent).

    Existing pages are matched by the `match_kw` substring (lowercase) — that
    way a crawled „Datenschutz" doesn't get a duplicate manual „Datenschutz-
    erklärung" inserted next to it. If a matching page exists but isn't yet
    flagged as Pflichtseite, we promote it in place.
    """
    all_pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id)
        .all()
    )
    for seite in PFLICHTSEITEN_IMMER:
        kw = seite.get("match_kw") or seite["page_name"].lower()
        match = next(
            (p for p in all_pages if kw in (p.page_name or "").lower()),
            None,
        )
        if match is not None:
            # Existiert bereits — als Pflichtseite markieren falls nicht schon.
            if not match.ist_pflichtseite:
                match.ist_pflichtseite = True
                if not match.page_type or match.page_type == "sonstige":
                    match.page_type = seite["page_type"]
            continue
        # Keine passende Seite vorhanden — neu anlegen.
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
        # Gesperrt ist die Struktur (Name, Position, Elternteil), nicht der
        # Inhalt. `mockup_html` gehoert dazu: Ein Impressum braucht genauso ein
        # Aussehen wie jede andere Seite, und die Design-Vorschau schreibt ihren
        # Entwurf genau dorthin. Ohne diesen Eintrag verwarf die API das Feld
        # und antwortete trotzdem mit 200 — die Oberflaeche meldete Erfolg.
        allowed = {"zweck", "notizen", "status", "sections", "ai_prompt",
                   "color_tag", "mockup_html"}
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
    # Phase 4: group_template_sections — gleiche Validierung wie sections.
    if "group_template_sections" in updates:
        raw_tpl = updates.pop("group_template_sections") or []
        cleaned_tpl = [str(s) for s in raw_tpl if isinstance(s, str) and s in SECTION_CATALOG]
        page.group_template_sections = json.dumps(cleaned_tpl, ensure_ascii=False)
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

# **Die Sperre haengt am Router (L-67, 22.08.2026).** Die fuenfzehn Routen
# hier fuehren die Seiten der Kundenprojekte samt Vorlagen — darunter
# `DELETE /{page_id}`, also das Entfernen einer Kundenseite. Sie verliessen
# sich auf `require_any_auth`; der `router` darueber traegt die Sperre seit
# jeher, dieser hier nicht.
#
# Vor der Sperre gemessen: `PageManager`, `PublicPageEditor` und
# `PageTemplateEditor` rufen die Adressen, alle unter
# `PrivateRoute roles={['admin']}`. Kein Aufruf aus dem Kundenportal.
pages_router = APIRouter(prefix="/api/pages", tags=["pages"],
                         dependencies=[Depends(require_innendienst)])


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




# ── ENDPOINT: KI-Vorlage generieren ──────────────────────────────────────────



# ── ENDPOINT: Continue-generating (R2 Relume-Parität) ─────────────────────────



# ── ENDPOINTS: Variant-Slot-Verwaltung (R2 Feature 4) ─────────────────────────





# ── ENDPOINT: PDF-Export ──────────────────────────────────────────────────────





_PFLICHT_DESC = {
    "Impressum":                  "Gesetzliche Anbieterkennzeichnung nach § 5 TMG",
    "Datenschutzerklärung":       "Informationspflicht gemäß Art. 13/14 DSGVO",
    "Barrierefreiheitserklärung": "Konformitätserklärung gemäß BFSG / BITV 2.0",
    "AGB":                        "Allgemeine Geschäftsbedingungen / Vertragsgrundlage",
}




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

# Datei-Endungen, die KEINE eigenen Inhaltsseiten sind — Assets vom Crawler
# rausfiltern (CSS-Bundles, Bilder, Webfonts, PDFs, Archive, Mediafiles).
_ASSET_EXTENSIONS: frozenset[str] = frozenset({
    ".css", ".js", ".mjs", ".map",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".avif", ".ico", ".bmp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".mp4", ".webm", ".mp3", ".wav", ".ogg",
    ".xml", ".json", ".txt",
})

# Page-Type-Heuristik: tuple_of_keywords → page_type
_TYPE_HEURISTICS: list[tuple[tuple[str, ...], str]] = [
    (("leistung", "service", "angebot", "produkt"),                  "leistung"),
    (("kontakt", "contact", "anfrage"),                              "conversion"),
    (("ueber", "about", "team", "unternehmen"),                      "vertrauen"),
    (("referenz", "projekt", "fallstudie", "case"),                  "vertrauen"),
    (("blog", "news", "aktuell", "magazin", "beitrag", "artikel", "info"), "info"),
]


















# ── Qualitätsschleife ──────────────────────────────────────────────────────────

@pages_router.post("/{page_id}/qualitaetspruefung")
async def qualitaetspruefung(
    page_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Prüft eine selbst gebaute Seite mit dem eigenen Katalog.

    Der Audit ist adressgetrieben, also bekommt die Seite zuerst eine Adresse:
    Sie wird auf die Vorschau-Site deployt, und das Audit läuft gegen diese
    Vorschau — nie gegen die Domain des Kunden, auf der noch der alte Auftritt
    steht.

    Schritt 8 des Design-Konzepts: Was wir Kunden vorwerfen, dürfen wir selbst
    nicht liefern.
    """
    from database import AuditResult
    from services.qualitaetsschleife import (
        KeineVorschauSite, NichtsZuPruefen, deploye_vorschau,
    )

    seite = db.query(SitemapPage).filter(SitemapPage.id == page_id).first()
    if not seite:
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")

    lead = db.query(Lead).filter(Lead.id == seite.lead_id).first()
    firmenname = (lead.display_name or lead.company_name) if lead else ""

    try:
        vorschau_url = await deploye_vorschau(seite, firmenname=firmenname or "")
    except NichtsZuPruefen as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeineVorschauSite as e:
        # Fehlende Einrichtung, kein Fehler im Ablauf — 503 sagt das.
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:  # noqa: BLE001
        logger.error(f"Qualitätsschleife: Deploy fehlgeschlagen: "
                     f"{type(e).__name__}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Die Vorschau konnte nicht bereitgestellt werden: {e}")

    audit = AuditResult(
        lead_id=seite.lead_id,
        sitemap_page_id=seite.id,
        website_url=vorschau_url,
        company_name=firmenname or (seite.page_name or "Eigenprüfung"),
        city=(lead.city or "") if lead else "",
        status="pending",
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    audit_id = audit.id

    from routers.audit import _run_audit_background
    background_tasks.add_task(_run_audit_background, audit_id)

    return {
        "audit_id": audit_id,
        "vorschau_url": vorschau_url,
        "status": "pending",
        "message": "Die Seite liegt als Vorschau bereit und wird geprüft.",
    }


@pages_router.get("/{page_id}/qualitaetspruefungen")
def qualitaetspruefungen(
    page_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Die bisherigen Eigenprüfungen dieser Seite, neueste zuerst."""
    from database import AuditResult

    laeufe = (
        db.query(AuditResult)
        .filter(AuditResult.sitemap_page_id == page_id)
        .order_by(AuditResult.created_at.desc())
        .limit(min(limit, 50))
        .all()
    )
    return [
        {
            "audit_id": a.id,
            "status": a.status,
            "total_score": a.total_score,
            "level": a.level,
            "coverage": a.coverage,
            "vorschau_url": a.website_url,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in laeufe
    ]
