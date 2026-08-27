"""Bestehende Sitemap einlesen, eigene als PDF ausgeben (L-25).

**Warum eigene Datei, 22.08.2026.** `routers/sitemap.py` hatte 1.800 Zeilen.
Der Weg hinein und der Weg hinaus. Die PDF-Erzeugung allein ist 163
Zeilen Layout, die mit der Sitemap-Logik nichts zu tun haben.

Die Verflechtung ist **transitiv** gemessen — nicht nur, was die Routen
brauchen, sondern auch, was deren Helfer brauchen. Beim Schnitt davor war
genau das die Luecke, und vier Namen fielen erst dem Lint auf.

Geteilt bleiben 2 Helfer, die auch der Rest braucht; sie werden von
dort geholt statt kopiert.
"""
import unicodedata
from datetime import datetime
from io import BytesIO
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from fastapi.responses import Response
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus.flowables import HRFlowable
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, text
from sqlalchemy.orm import Session
from database import Base, Briefing, Lead, get_db
from routers.auth_router import require_any_auth, optional_auth, require_innendienst

from routers.sitemap import PageBreak, Paragraph, SimpleDocTemplate, SitemapPage, Spacer, Table, TableStyle, _ASSET_EXTENSIONS, _FONT, _FONT_B, _PAGE_W, _PFLICHT_KEYWORDS, _TYPE_HEURISTICS, logger, _serialize, _ensure_pflichtseiten

_DARK_TEAL  = colors.HexColor("#004F59")

_FOOTER_TXT = "KOMPAGNON Communications BP GmbH · kompagnon.eu"

_LIGHT_GREY = colors.HexColor("#F4F7F8")

_MARGIN = 18 * mm

_MID_GREY   = colors.HexColor("#8A9BA8")

_PFLICHT_DESC = {
    "Impressum":                  "Gesetzliche Anbieterkennzeichnung nach § 5 DDG",
    "Datenschutzerklärung":       "Informationspflicht gemäß Art. 13/14 DSGVO",
    "Barrierefreiheitserklärung": "Konformitätserklärung gemäß BFSG / BITV 2.0",
    "AGB":                        "Allgemeine Geschäftsbedingungen / Vertragsgrundlage",
}

# ── PDF brand tokens (shared with briefing_pdf.py) ────────────────────────────
_TEAL       = colors.HexColor("#008EAA")

_TEXT_DARK  = colors.HexColor("#1A2C32")

_WHITE      = colors.white

router = APIRouter(prefix="/api/sitemap", tags=["sitemap-austausch"],
                   dependencies=[Depends(require_innendienst)])


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

    # Normalize + dedupe by path. Filter Assets (Bilder, CSS, JS, Fonts, PDF, …)
    # — die haben im Sitemap-Tree nichts verloren.
    seen: set[str] = set()
    items: list[tuple[str, str, list[str], int]] = []
    for raw in urls:
        parsed = urlparse(raw)
        netloc = parsed.netloc.lower().replace("www.", "")
        if netloc != base_netloc:
            continue
        path = parsed.path.rstrip("/").lower()
        # Asset-Filter: letzter Pfad-Bestandteil hat eine Datei-Endung aus der Liste
        last_seg = path.rsplit("/", 1)[-1]
        ext_idx = last_seg.rfind(".")
        if ext_idx > 0:
            ext = last_seg[ext_idx:].lower()
            if ext in _ASSET_EXTENSIONS:
                continue
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


def _humanize_slug(slug: str) -> str:
    """`wallbox-installation` → `Wallbox Installation`."""
    return slug.replace("-", " ").replace("_", " ").strip().title()


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


def _t(roher_text: str) -> str:
    # Der Parameter hiess `text` und verdeckte `sqlalchemy.text`
    # (L-25, 22.08.2026). In der grossen Datei fiel das nicht auf.
    if not roher_text:
        return ""
    return unicodedata.normalize("NFC", str(roher_text))
